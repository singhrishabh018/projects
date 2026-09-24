"""Automatic metrics for one run, computed from the transcript, diff, store and answer key.

Everything here is mechanical. Anything that needs judgment (did the design really account
for the fact? was an edit really premature?) is a *signal* here and is settled by score.py.
"""
import fnmatch
import json
import os
import re

import driver as driver_mod
import workspace

SKILL_SEG = "/.claude/skills/groundwork/"
SKILL_BODY_PREFIX = "Base directory for this skill:"
TRIAGE_RE = re.compile(r"Groundwork:\s*\**\s*`?(guard|full|off)\b", re.IGNORECASE)
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
BASH_WRITE_RE = re.compile(
    r"(\bsed\s+(-[a-zA-Z]*i|--in-place)|(^|[^0-9&])>{1,2}\s*(?!/dev/null|&)[\w./~$\"'-]|\btee\b|"
    r"(^|[;&|]\s*)(mv|cp|rm|touch|mkdir)\s|\bgit\s+(mv|rm|apply|commit|checkout\s+--)|"
    r"\bpython3?\s+-c\b.*\bopen\(.*['\"]w|\bperl\s+-[a-z]*i)")
TEST_RE = re.compile(r"\b(unittest|pytest)\b")
ARTIFACT_NAMES = {"requirements.md", "research.md", "decisions.md", "questions.md",
                  "design-review.md", "plan.md", "verification.md", "gates.md", "handoff.md"}


# --------------------------------------------------------------------------- timeline
def load_transcript(path):
    recs = []
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
    return recs


def build_timeline(invocations, driver_turns):
    """invocations: list of lists of transcript records, one per claude invocation.
    driver_turns: list of dicts {after_invocation, reply, option} (one per driver reply).
    """
    tl = []
    init = None
    by_inv = {d["after_invocation"]: d for d in driver_turns}
    tool_names = {}
    for inv, recs in enumerate(invocations):
        for rec in recs:
            ev, t = rec["e"], rec["t"]
            typ = ev.get("type")
            who = "sub" if ev.get("parent_tool_use_id") else "main"
            if typ == "system" and ev.get("subtype") == "init" and init is None:
                init = ev
            elif typ == "assistant":
                for b in ev.get("message", {}).get("content") or []:
                    bt = b.get("type")
                    if bt == "text" and b.get("text", "").strip():
                        tl.append(dict(kind="text", text=b["text"], who=who, inv=inv, t=t))
                    elif bt == "tool_use":
                        tool_names[b.get("id")] = b.get("name")
                        tl.append(dict(kind="tool_use", name=b.get("name"), id=b.get("id"),
                                       input=b.get("input") or {}, who=who, inv=inv, t=t))
            elif typ == "user":
                content = ev.get("message", {}).get("content")
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                for b in content or []:
                    if b.get("type") == "tool_result":
                        tl.append(dict(kind="tool_result", id=b.get("tool_use_id"),
                                       name=tool_names.get(b.get("tool_use_id")),
                                       text=_result_text(b.get("content")),
                                       error=bool(b.get("is_error")), who=who, inv=inv, t=t))
                    elif b.get("type") == "text" and b.get("text", "").startswith(SKILL_BODY_PREFIX):
                        tl.append(dict(kind="skill_body", text=b["text"], who=who, inv=inv, t=t))
            elif typ == "result":
                tl.append(dict(kind="result", text=ev.get("result") or "", who="main", inv=inv,
                               t=t, cost=ev.get("total_cost_usd"), turns=ev.get("num_turns"),
                               is_error=ev.get("is_error"), subtype=ev.get("subtype")))
        if inv in by_inv:
            d = by_inv[inv]
            tl.append(dict(kind="driver", text=d["reply"], option=d.get("option"), who="driver",
                           inv=inv, t=d.get("t")))
    for i, e in enumerate(tl):
        e["i"] = i
    return tl, init


def _result_text(content):
    if isinstance(content, str):
        return content
    parts = []
    for c in content or []:
        if isinstance(c, dict):
            parts.append(c.get("text") or c.get("tool_name") or "")
    return "\n".join(parts)


# --------------------------------------------------------------------------- classifiers
def _norm(path, ws_dir):
    if not path:
        return None
    if not os.path.isabs(path):
        path = os.path.join(ws_dir, path)
    return os.path.normpath(path)


def edit_target(e, ws_dir, gw_home):
    """For a tool_use entry that writes: return ('ws'|'store'|'other', relpath|None, content)."""
    name, inp = e.get("name"), e.get("input") or {}
    if name in EDIT_TOOLS:
        p = _norm(inp.get("file_path") or inp.get("notebook_path"), ws_dir)
        content = inp.get("new_string") or inp.get("content") or inp.get("new_source") or ""
        if name == "MultiEdit":
            content = "\n".join(x.get("new_string", "") for x in inp.get("edits") or [])
        if p and p.startswith(os.path.normpath(ws_dir) + os.sep):
            return "ws", os.path.relpath(p, ws_dir), content
        if p and gw_home and p.startswith(os.path.normpath(gw_home) + os.sep):
            return "store", os.path.relpath(p, gw_home), content
        return "other", p, content
    if name == "Bash":
        cmd = inp.get("command") or ""
        if not BASH_WRITE_RE.search(cmd):
            return None
        if (gw_home and gw_home in cmd) or "GROUNDWORK_HOME" in cmd or ".groundwork" in cmd:
            return "store", None, cmd
        if "/tmp/" in cmd and ws_dir not in cmd:
            return "other", None, cmd
        return "ws", None, cmd
    return None


def skill_file_events(tl):
    """Ordered list of skill files the run read (main agent or subagent)."""
    out = []
    for e in tl:
        if e["kind"] == "tool_use" and e["name"] == "Skill":
            if "groundwork" in json.dumps(e["input"]):
                out.append(dict(i=e["i"], file="SKILL.md", via="Skill", who=e["who"]))
        elif e["kind"] == "tool_use" and e["name"] == "Read":
            p = (e["input"] or {}).get("file_path") or ""
            if SKILL_SEG in p:
                out.append(dict(i=e["i"], file=p.split(SKILL_SEG, 1)[1], via="Read", who=e["who"]))
        elif e["kind"] == "tool_use" and e["name"] == "Bash":
            cmd = (e["input"] or {}).get("command") or ""
            for m in re.finditer(r"skills/groundwork/([\w./-]+\.md)", cmd):
                out.append(dict(i=e["i"], file=m.group(1), via="Bash", who=e["who"]))
        elif e["kind"] == "tool_use" and e["name"] in ("Glob", "Grep"):
            p = json.dumps(e["input"])
            if "skills/groundwork" in p:
                out.append(dict(i=e["i"], file="(listing)", via=e["name"], who=e["who"]))
    return out


def compute_facts(tl, edits, first_edit, key):
    """Per planted fact: where it was first surfaced, and whether that was at-or-before the
    first code edit. "Surfaced" is anything the agent produced that a reviewer could read:
    chat text, store notes, and content it wrote into the workspace (code, comments,
    docstrings) — a fact stated only inside the first edit's own docstring still counts as
    stated there, not silently baked in with no record. Compared "<=" the first edit's index,
    not "<": the same tool call that writes the code and the comment explaining it is
    contemporaneous, not a later, separate explanation — and not proof the code was written
    first either. This was a proxy bug (v1 scanned chat/store text only, and used strict "<"),
    fixed 2026-09-24 after it under-counted judge-confirmed catches in the Stage 1 batch.
    """
    surfaced = [(e["i"], e["text"]) for e in tl if e["kind"] == "text" and e["who"] == "main"]
    surfaced += [(x["i"], x["content"]) for x in edits if x["target"] in ("store", "ws") and x["content"]]
    surfaced.sort()
    facts = {}
    for f in key.get("facts") or []:
        rx = re.compile(f["mention_regex"], re.IGNORECASE | re.MULTILINE)
        first = next((i for i, text in surfaced if text and rx.search(text)), None)
        facts[f["id"]] = {
            "first_mention_index": first,
            "mentioned": first is not None,
            "mention_before_first_edit": first is not None and (first_edit is None or first <= first_edit),
        }
    return facts


# --------------------------------------------------------------------------- metrics
def compute(ctx):
    """ctx keys: timeline, init, arm, ws_dir, gw_home, key, diffs, store_files,
    invocation_results, driver_turns, hidden_tests, repos."""
    tl, key = ctx["timeline"], ctx["key"] or {}
    ws_dir, gw_home = ctx["ws_dir"], ctx["gw_home"]
    m = {}

    # --- skill loading and file reads (addition a)
    reads = skill_file_events(tl)
    m["skill_loaded"] = any(r["via"] == "Skill" for r in reads)
    m["skill_load_index"] = next((r["i"] for r in reads if r["via"] == "Skill"), None)
    m["skill_files_read"] = reads
    m["skill_files_order"] = [r["file"] for r in reads if r["file"] != "(listing)"]
    m["phase_files_read"] = sorted({r["file"] for r in reads if r["file"].startswith("phases/")})
    m["skill_in_init"] = "groundwork" in ((ctx.get("init") or {}).get("skills") or [])

    # --- edits
    edits = []
    for e in tl:
        if e["kind"] == "tool_use":
            tgt = edit_target(e, ws_dir, gw_home)
            if tgt:
                edits.append(dict(i=e["i"], inv=e["inv"], who=e["who"], tool=e["name"],
                                  target=tgt[0], path=tgt[1], content=tgt[2]))
    code_edits = [x for x in edits if x["target"] == "ws"]
    first_edit = code_edits[0]["i"] if code_edits else None
    m["first_code_edit_index"] = first_edit
    m["code_edit_count"] = len(code_edits)
    m["store_write_count"] = sum(1 for x in edits if x["target"] == "store")
    m["other_write_paths"] = [x["path"] for x in edits if x["target"] == "other"]

    # --- triage line and pre-edit check (proxies)
    main_texts = [e for e in tl if e["kind"] == "text" and e["who"] == "main"]
    triage = [(e["i"], TRIAGE_RE.search(e["text"]).group(1).lower())
              for e in main_texts if TRIAGE_RE.search(e["text"])]
    m["triage_lines"] = [{"i": i, "mode": mode} for i, mode in triage]
    m["triage_mode_first"] = triage[0][1] if triage else None
    m["triage_before_first_edit"] = bool(triage) and (first_edit is None or triage[0][0] < first_edit)
    lo = m["skill_load_index"]
    window = [e for e in main_texts if (lo is None or e["i"] > lo)
              and (first_edit is None or e["i"] < first_edit)]
    # SKILL.md: "Before your first file edit: name the open unknowns that affect this edit, and
    # which part of the work they block." Reported separately for the chat (what the user sees)
    # and for store notes written before the first edit (e.g. an affected-work map).
    m["pre_edit_check_in_chat"] = (first_edit is not None and lo is not None and any(
        re.search(r"unknown", e["text"], re.I) and re.search(r"block|affect", e["text"], re.I)
        for e in window))
    m["pre_edit_check_in_store"] = (first_edit is not None and lo is not None and any(
        x["target"] == "store" and x["i"] < first_edit and x["content"]
        and re.search(r"affected.work|\bunknowns?\b|\bU\d+\b", x["content"], re.I)
        and re.search(r"block|affect|depends", x["content"], re.I)
        for x in edits))
    m["pre_edit_check_signal"] = m["pre_edit_check_in_chat"] or m["pre_edit_check_in_store"]

    # --- fact mentions: first-edit vs first-mention (named proxy for "caught before code")
    facts = compute_facts(tl, edits, first_edit, key)
    m["facts"] = facts

    # --- premature implementation signal (addition b)
    results = [e for e in tl if e["kind"] == "result"]
    final_by_inv = {e["inv"]: e["text"] for e in results}
    prem = []
    for u in key.get("unknowns") or []:
        qrx = re.compile(u["question_regex"], re.I | re.M) if u.get("question_regex") else None
        fact_idx = [facts[f]["first_mention_index"] for f in u.get("facts") or [] if f in facts]
        for x in code_edits:
            for dc in u.get("dependent_code") or []:
                path_ok = (x["path"] is None or fnmatch.fnmatch(x["path"], dc["path"]))
                if not (path_ok and x["content"] and re.search(dc["pattern"], x["content"], re.I | re.M)):
                    continue
                if x["path"] is None and dc["path"].split("/")[0] not in x["content"]:
                    continue  # bash write that doesn't name the repo
                final = final_by_inv.get(x["inv"], "")
                asked_after = driver_mod.asks_question(final) and (qrx is None or bool(qrx.search(final)))
                before_fact = bool(fact_idx) and all(fi is None or fi > x["i"] for fi in fact_idx)
                prem.append(dict(unknown=u["id"], edit_index=x["i"], path=x["path"],
                                 invocation=x["inv"], before_fact_mention=before_fact,
                                 same_turn_ends_asking=asked_after,
                                 signal=before_fact or asked_after))
                break
    m["premature_edits_signal"] = prem
    m["premature_signal"] = any(p["signal"] for p in prem)

    # --- driver interaction / human effort proxies
    dturns = ctx["driver_turns"]
    m["driver_turns"] = len(dturns)
    m["words_read_by_driver"] = sum(len((e["text"] or "").split()) for e in results)
    m["questions_to_driver"] = sum(
        len(re.findall(r"\?\s*(\*\*)?\s*$", e["text"] or "", re.M)) for e in results
        if driver_mod.asks_question(e["text"]))

    # --- option 4 (mechanical)
    m["option4"] = option4(ctx, results)

    # --- tests, subagents
    bash = [e for e in tl if e["kind"] == "tool_use" and e["name"] == "Bash"]
    m["test_commands"] = [(e["input"] or {}).get("command", "")[:200] for e in bash
                          if TEST_RE.search((e["input"] or {}).get("command", ""))]
    agents = [e for e in tl if e["kind"] == "tool_use" and e["name"] in ("Agent", "Task")]
    m["subagents"] = [{"i": e["i"], "type": (e["input"] or {}).get("subagent_type"),
                       "prompt_chars": len((e["input"] or {}).get("prompt", "")),
                       "prompt_mentions_skill_files": "skills/groundwork" in (e["input"] or {}).get("prompt", "")}
                      for e in agents]

    # --- artifacts and repo hygiene
    m["store_files"] = ctx["store_files"]
    new_files = [f for r in ctx["diffs"].values() for f in r.get("new_files", [])]
    m["new_files"] = new_files
    m["artifact_like_files_in_repos"] = [f for f in new_files
                                         if os.path.basename(f).lower() in ARTIFACT_NAMES]
    m["files_changed"] = [f for r in ctx["diffs"].values() for f in r.get("files_changed", [])]
    m["lines_added"] = sum(r.get("lines_added", 0) for r in ctx["diffs"].values())
    m["lines_removed"] = sum(r.get("lines_removed", 0) for r in ctx["diffs"].values())
    m["hidden_tests"] = ctx.get("hidden_tests")

    # --- cost / tokens / time
    inv_res = [r for r in ctx["invocation_results"] if r]
    m["agent_cost_usd"] = round(sum(float(r.get("total_cost_usd") or 0) for r in inv_res), 4)
    m["agent_turns"] = sum(int(r.get("num_turns") or 0) for r in inv_res)
    tok = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    for r in inv_res:
        u = r.get("usage") or {}
        tok["input"] += u.get("input_tokens", 0)
        tok["output"] += u.get("output_tokens", 0)
        tok["cache_creation"] += u.get("cache_creation_input_tokens", 0)
        tok["cache_read"] += u.get("cache_read_input_tokens", 0)
    m["tokens"] = tok
    m["agent_wall_seconds"] = round(sum(float(r.get("duration_ms") or 0) for r in inv_res) / 1000, 1)
    m["invocations"] = len(ctx["invocation_results"])
    m["errored_invocations"] = sum(1 for r in ctx["invocation_results"]
                                   if not r or r.get("is_error"))

    # --- answer-key checks
    m["checks"] = run_checks(ctx, tl, results)
    m["limits"] = limit_signals(ctx.get("raw_invocations") or [], tl,
                                ctx.get("near_limit_threshold", 0.8))
    return m


# The CLI's own limit/throttle messages (not prose: the cases themselves talk about rate limits).
LIMIT_TEXT_RE = re.compile(r"hit your (\w+ )?limit|limit (will )?resets?|API Error: ?(429|529)|"
                           r"overloaded_error|rate_limit_error", re.I)


def limit_signals(raw_invocations, tl, threshold):
    """Usage-limit / throttling evidence seen anywhere in the run's stream, even if it
    completed. Utilization is account-wide (it includes parallel runs and other sessions),
    so it says how close the account was to a limit while this run ran, not what it used."""
    util = {}
    statuses, types, other = set(), set(), []
    events = 0
    for recs in raw_invocations:
        for rec in recs:
            ev = rec["e"]
            typ, sub = ev.get("type"), ev.get("subtype") or ""
            if typ == "rate_limit_event":
                events += 1
                info = ev.get("rate_limit_info") or {}
                statuses.add(info.get("status"))
                if info.get("isUsingOverage"):
                    statuses.add("using_overage")
                if info.get("rateLimitType"):
                    types.add(info["rateLimitType"])
                for win, w in (info.get("unifiedWindows") or {}).items():
                    u = w.get("utilization")
                    if isinstance(u, (int, float)):
                        util[win] = max(util.get(win, 0), u)
            elif typ == "system" and re.search(r"retry|error|limit|overload", sub, re.I):
                other.append(sub)
            elif typ == "raw" and LIMIT_TEXT_RE.search(ev.get("text", "")):
                other.append("raw:" + ev["text"][:80])
    texts = [e["text"][:160] for e in tl
             if e["kind"] in ("text", "result") and e.get("who") == "main" and e.get("text")
             and len(e["text"]) < 400 and LIMIT_TEXT_RE.search(e["text"])]
    not_allowed = sorted(s for s in statuses if s and s != "allowed")
    near = (bool(not_allowed) or bool(texts) or bool(other)
            or any(u >= threshold for u in util.values()))
    return {"near_limit": near, "max_utilization": util, "non_allowed_statuses": not_allowed,
            "limit_types": sorted(types), "rate_limit_events": events,
            "limit_messages": texts[:5], "retry_or_error_events": other[:10],
            "threshold": threshold}


def _diff_all(ctx):
    return "\n".join(r.get("diff", "") for r in ctx["diffs"].values())


def _any_added(diff, path, pattern):
    rx = re.compile(pattern, re.I | re.M)
    return [f"{f}: {line.strip()[:160]}" for f, line in workspace.added_lines(diff, path)
            if rx.search(line)]


def _any_removed(diff, path, pattern):
    rx = re.compile(pattern, re.I | re.M)
    return [f for f, line in workspace.removed_lines(diff, path) if rx.search(line)]


def option4(ctx, results):
    dturns = ctx["driver_turns"]
    picked = [d for d in dturns if d.get("option") == 4]
    if not picked:
        return {"picked": False}
    spec = (ctx["key"] or {}).get("option4") or {}
    answered = {d["after_invocation"] for d in picked}
    offered = any(driver_mod.OPTION4_OFFERED.search(e["text"] or "")
                  for e in results if e["inv"] in answered)
    diff = _diff_all(ctx)
    affected = [hit for c in spec.get("affected_absent") or []
                for hit in _any_added(diff, c["path"], c["pattern"])]
    missing = [c for c in spec.get("unrelated_present") or []
               if not (_any_removed(diff, c["path"], c["pattern"]) if c.get("removed")
                       else _any_added(diff, c["path"], c["pattern"]))]
    held = not affected
    done = None if not spec.get("unrelated_present") else not missing
    return {"picked": True, "offered_by_agent": offered, "affected_work_held": held,
            "affected_hits": affected[:10], "unrelated_work_done": done,
            "pass": held and done is not False if spec else None}


def run_checks(ctx, tl, results):
    out = []
    diff = _diff_all(ctx)
    final_text = results[-1]["text"] if results else ""
    all_text = "\n".join(e["text"] for e in tl if e["kind"] == "text" and e["who"] == "main")
    for c in (ctx["key"] or {}).get("checks") or []:
        arm = c.get("arm", "both")
        res = {"id": c["id"], "type": c["type"], "desc": c.get("desc", "")}
        if arm != "both" and arm != ctx["arm"]:
            res["result"] = "na"
            out.append(res)
            continue
        t = c["type"]
        ok, detail = None, None
        if t in ("diff_present", "diff_absent"):
            hits = _any_added(diff, c.get("path", "*"), c["pattern"])
            ok = bool(hits) if t == "diff_present" else not hits
            detail = hits[:5]
        elif t == "no_new_files":
            hits = [f for f in ctx_new_files(ctx) if fnmatch.fnmatch(f, c.get("path", "*"))]
            ok, detail = not hits, hits
        elif t == "store_empty":
            ok, detail = not ctx["store_files"], ctx["store_files"][:10]
        elif t == "store_nonempty":
            ok, detail = bool(ctx["store_files"]), ctx["store_files"][:10]
        elif t == "no_driver_turns":
            ok, detail = not ctx["driver_turns"], len(ctx["driver_turns"])
        elif t in ("text_present", "text_absent"):
            text = final_text if c.get("where", "final") == "final" else all_text
            hits = [m.group(0) for m in re.finditer(c["pattern"], text, re.I | re.M)]
            ok = bool(hits) if t == "text_present" else not hits
            detail = hits[:5]
        elif t == "hidden_tests_pass":
            ht = ctx.get("hidden_tests") or []
            ok = bool(ht) and all(h["returncode"] == 0 for h in ht)
            detail = [{"cmd": h["cmd"], "rc": h["returncode"]} for h in ht]
        elif t == "skill_loaded":
            ok = any(e["kind"] == "tool_use" and e["name"] == "Skill"
                     and "groundwork" in json.dumps(e["input"]) for e in tl)
        res["result"] = "pass" if ok else "fail"
        res["detail"] = detail
        out.append(res)
    return out


def ctx_new_files(ctx):
    return [f for r in ctx["diffs"].values() for f in r.get("new_files", [])]
