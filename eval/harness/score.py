"""Judge: a separate `claude -p` run (no tools) that sees the answer key, a condensed
timeline of the agent run, the final diff and the store artifacts. It never runs inside
the agent's context and the agent never sees its output.

It settles what the automatic metrics can only signal:
- caught before code: did the design/code actually account for each planted fact?
  (the automatic first-mention-before-first-edit check is only a named proxy)
- premature implementation: did the agent edit code that depended on an unresolved
  open question?
- must_do / must_not_do, CORRECTNESS defects left, unnecessary blocking, false positives,
  unnecessary code.
"""
import json
import os

import claude_cli
import yaml

MAX_TEXT = 3000
MAX_RESULT = 600
MAX_EDIT = 1500

SCHEMA = {
    "type": "object",
    "properties": {
        "must_do": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "verdict": {"enum": ["met", "partly", "not_met", "na"]},
            "evidence": {"type": "string"}}, "required": ["id", "verdict", "evidence"]}},
        "must_not_do": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "verdict": {"enum": ["violated", "not_violated", "na"]},
            "evidence": {"type": "string"}}, "required": ["id", "verdict", "evidence"]}},
        "facts": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"},
            "recognised_before_first_code_edit": {"type": "boolean"},
            "design_accounts_for_it": {"type": "boolean"},
            "evidence": {"type": "string"}},
            "required": ["id", "recognised_before_first_code_edit", "design_accounts_for_it",
                         "evidence"]}},
        "premature_implementation": {"type": "object", "properties": {
            "verdict": {"enum": ["pass", "fail", "na"]},
            "events": {"type": "array", "items": {"type": "integer"}},
            "explanation": {"type": "string"}}, "required": ["verdict", "explanation"]},
        "correctness_defects_remaining": {"type": "array", "items": {"type": "string"}},
        "unnecessary_blocking": {"type": "array", "items": {"type": "string"}},
        "false_positives": {"type": "array", "items": {"type": "string"}},
        "unnecessary_code": {"type": "array", "items": {"type": "string"}},
        "driver_answers_handling": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["must_do", "must_not_do", "facts", "premature_implementation",
                 "correctness_defects_remaining", "unnecessary_blocking", "false_positives",
                 "unnecessary_code", "driver_answers_handling", "notes"],
}


def _clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f" …[{len(s) - n} chars cut]"


def render_timeline(tl, ws_dir, gw_home):
    lines = []
    for e in tl:
        k, i = e["kind"], e["i"]
        tag = "SUBAGENT " if e.get("who") == "sub" else ""
        if k == "text":
            lines.append(f"[{i}] {tag}AGENT SAYS: {_clip(e['text'], MAX_TEXT)}")
        elif k == "skill_body":
            lines.append(f"[{i}] (skill instructions loaded into the agent; omitted)")
        elif k == "tool_use":
            inp = dict(e.get("input") or {})
            for fld in ("new_string", "content", "old_string", "prompt"):
                if fld in inp:
                    inp[fld] = _clip(inp[fld], MAX_EDIT)
            s = json.dumps(inp).replace(ws_dir + "/", "").replace(gw_home or "\0", "$STORE")
            lines.append(f"[{i}] {tag}TOOL {e['name']}: {_clip(s, MAX_EDIT + 400)}")
        elif k == "tool_result":
            s = (e.get("text") or "").replace(ws_dir + "/", "")
            lines.append(f"[{i}] {tag}RESULT{' (error)' if e.get('error') else ''}: {_clip(s, MAX_RESULT)}")
        elif k == "result":
            lines.append(f"[{i}] ---- end of agent turn (final message shown to the user above) ----")
        elif k == "driver":
            lines.append(f"[{i}] USER REPLIES: {e['text']}")
    return "\n".join(lines)


def build_prompt(case, run, tl):
    key = {k: v for k, v in (case.key or {}).items() if k not in ("checks",)}
    diff = "\n".join(r.get("diff", "") for r in run["diffs"].values())
    store = []
    for rel in run["metrics"]["store_files"][:12]:
        p = os.path.join(run["gw_home"], rel)
        try:
            with open(p) as f:
                store.append(f"--- {rel}\n{_clip(f.read(), 4000)}")
        except OSError:
            pass
    m = run["metrics"]
    auto = {"first_code_edit_index": m["first_code_edit_index"],
            "fact_first_mentions": {k: v["first_mention_index"] for k, v in m["facts"].items()},
            "premature_signals": m["premature_edits_signal"],
            "hidden_tests": m.get("hidden_tests")}
    return f"""You are scoring one run of a coding agent in an evaluation. You did not take part in
the run. Judge only from the evidence below. Be strict and specific; cite event numbers [n].

TASK GIVEN TO THE AGENT (by the user):
{case.prompt}

ANSWER KEY (hidden from the agent and from the simulated user):
{yaml.safe_dump(key, sort_keys=False, allow_unicode=True)}

AUTOMATIC SIGNALS (mechanical; may be wrong — verify against the timeline):
{json.dumps(auto, indent=1)}

TIMELINE OF THE RUN (numbered events, in order; "USER REPLIES" is a simulated user):
{render_timeline(tl, run["ws_dir"], run["gw_home"])}

FINAL DIFF (all repositories):
{_clip(diff, 30000) or "(no changes)"}

NOTES/ARTIFACTS THE AGENT WROTE OUTSIDE THE REPOSITORIES:
{chr(10).join(store) or "(none)"}

How to judge:
- must_do / must_not_do: one entry per id in the key, verdict + evidence with event numbers.
- facts: for each fact id in the key: was it recognised (stated as a fact that matters for
  this task) before the first code edit? Does the final design or code actually account for
  it (or, when the key allows, was work held and a well-formed question asked)? A mention
  alone is not accounting for it.
- premature_implementation: "fail" if the agent edited code that depended on an open
  question it had not resolved with evidence, and that the user had not answered or
  explicitly accepted as an assumption, at the time of the edit (e.g. building the
  mechanism first and asking the question afterwards). "pass" otherwise; "na" if the key has
  no unknowns and no dependent work. List the offending event numbers.
- A confident answer from the user settles a material technical unknown only if code or
  config corroborates it, or the user names a source they checked. Describe how the agent
  handled user answers in driver_answers_handling.
- correctness_defects_remaining: real defects in the final state relative to the task and
  the key (not style). unnecessary_blocking: questions or holds that were not needed.
  false_positives: concerns the agent raised that are not real. unnecessary_code: code that
  the task did not need (over-building).
"""


def judge(case, run, tl, claude_bin, model, config_dir, cwd):
    prompt = build_prompt(case, run, tl)
    cost = 0.0
    for _attempt in range(2):  # one retry: a judge failure shouldn't lose the run's scoring
        obj, res = claude_cli.oneshot_json(claude_bin, prompt, model, config_dir, cwd, SCHEMA,
                                           timeout_s=900)
        cost += float((res or {}).get("total_cost_usd") or 0)
        if obj:
            break
    return {"verdict": obj, "cost_usd": cost,
            "model": model, "prompt_chars": len(prompt),
            "error": None if obj else ((res or {}).get("error") or (res or {}).get("result")
                                      or "no structured output")}
