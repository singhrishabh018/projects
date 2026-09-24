#!/usr/bin/env python3
"""Offline self-test of the harness. No API calls, no cost.

1. Writes a throwaway folder of dummy cases (documented format) to a temp dir OUTSIDE the
   repo, one valid and one deliberately broken, and checks `validate` accepts/rejects them.
2. Runs `run --cases-dir <dummy>` end to end with a stub `claude` binary that emits
   stream-json like the real CLI (skill load, phase-file read, edits, a question offering
   option 4, a resume), then checks the metrics, option-4 result, audit and report.
3. Runs once more with the stub reading a key file, and checks the audit invalidates the run.

The dummy cases are format fixtures only (a one-file repo and a marker string); they are
not evaluation cases.

Usage: python3 eval/harness/selftest.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GW = os.path.join(HERE, "gw_eval.py")
sys.path.insert(0, HERE)
import metrics  # noqa: E402 -- unit tests for the fact-mention proxy fix

STUB = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
def val(flag):
    return args[args.index(flag) + 1] if flag in args else None
if "--version" in args:
    print("0.0.0 (stub)"); sys.exit(0)
if "--json-schema" in args:                      # driver-sim / judge one-shot
    sys.stdin.read()
    schema = json.loads(val("--json-schema"))
    def make(s):
        t = s.get("type")
        if "enum" in s: return s["enum"][0]
        if t == "object": return {k: make(v) for k, v in s.get("properties", {}).items()}
        if t == "array": return []
        if t == "boolean": return True
        if t == "integer" or t == ["integer", "null"]: return None
        return "stub"
    print(json.dumps({"type": "result", "result": "", "total_cost_usd": 0.001,
                      "structured_output": make(schema)})); sys.exit(0)
cwd = os.getcwd()
add_dir = val("--add-dir")
resume = val("--resume")
out = lambda ev: print(json.dumps(ev), flush=True)
out({"type": "system", "subtype": "init", "session_id": "stub-sid", "model": val("--model"),
     "tools": val("--tools").split(","), "skills": ["groundwork"] if add_dir else [],
     "mcp_servers": [], "plugins": [], "agents": []})
def use(i, name, inp, who=None):
    out({"type": "assistant", "parent_tool_use_id": who, "message": {"content": [
        {"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}})
    out({"type": "user", "parent_tool_use_id": who, "message": {"content": [
        {"type": "tool_result", "tool_use_id": f"t{i}", "content": "ok"}]}})
def say(text):
    out({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
out({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "unifiedWindows": {
     "five_hour": {"utilization": float(os.environ.get("STUB_UTIL", "0.1"))}}}})
_n = 0
if os.environ.get("STUB_COUNTER"):
    c = os.environ["STUB_COUNTER"]
    _n = int(open(c).read()) + 1 if os.path.exists(c) else 1
    open(c, "w").write(str(_n))
if os.environ.get("STUB_LIMIT") or (os.environ.get("STUB_LIMIT_AT") and _n >= int(os.environ["STUB_LIMIT_AT"])):
    say("You've hit your session limit · resets 9am (UTC)")
    out({"type": "result", "subtype": "success", "is_error": True,
         "result": "You've hit your session limit · resets 9am (UTC)", "session_id": "stub-sid",
         "total_cost_usd": 0.0, "num_turns": 1, "duration_ms": 10, "usage": {}})
    sys.exit(0)
if not resume:
    if add_dir:
        use(1, "Skill", {"skill": "groundwork"})
        out({"type": "user", "message": {"content": [{"type": "text",
             "text": "Base directory for this skill: " + add_dir + "/.claude/skills/groundwork\n# Groundwork"}]}})
        say("Groundwork: full - touches something material")
        use(2, "Read", {"file_path": add_dir + "/.claude/skills/groundwork/phases/c1-triage.md"})
        say("Open unknowns that affect this edit: U1 blocks the flush part.")
    if os.environ.get("STUB_LEAK"):
        use(3, "Bash", {"command": "cat /somewhere/key/answer_key.yaml"})
    say("The MARKER_FACT matters here.")
    p = os.path.join(cwd, "demo", "other.py")
    with open(p, "a") as f: f.write("UNRELATED_FIX = True\n")
    use(4, "Edit", {"file_path": p, "old_string": "", "new_string": "UNRELATED_FIX = True"})
    p2 = os.path.join(cwd, "demo", "app.py")
    with open(p2, "a") as f: f.write("def flush():\n    pass\n")
    use(5, "Write", {"file_path": p2, "content": "def flush():\n    pass\n"})
    text = ("**Should the flush wait for the owner?**\nMy recommendation: wait.\n"
            "1. You know the answer\n2. You have access\n3. You know who would know\n"
            "4. None of these -> I leave the flush unchanged and continue with the rest.")
else:
    say("Holding the affected work.")
    text = "Done. What changed: other.py. Open unknowns: U1 (flush policy)."
say(text)
out({"type": "result", "subtype": "success", "is_error": False, "result": text,
     "session_id": "stub-sid", "total_cost_usd": 0.01, "num_turns": 3, "duration_ms": 1000,
     "usage": {"input_tokens": 10, "output_tokens": 20, "cache_creation_input_tokens": 30,
               "cache_read_input_tokens": 40}})
'''


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def make_dummy_cases(root):
    ok = os.path.join(root, "DUMMY-OK")
    write(os.path.join(ok, "packet", "case.yaml"),
          "id: DUMMY-OK\ndriver_prompt: Change demo/app.py.\nworkspace:\n  base: none\n"
          "  overlay: overlay\nconnectors:\n  dir: connectors\nlimits:\n  max_driver_turns: 2\n")
    write(os.path.join(ok, "packet", "overlay", "demo", "app.py"), "X = 1\n")
    write(os.path.join(ok, "packet", "overlay", "demo", "other.py"), "Y = 1\n")
    write(os.path.join(ok, "packet", "connectors", "tickets.json"), json.dumps(
        {"role": "tickets", "failure": None, "items": [{"id": "1", "title": "t", "body": "b"}]}))
    write(os.path.join(ok, "key", "answer_key.yaml"), """\
hidden_conditions: [a marker]
facts:
  - {id: F1, mention_regex: 'MARKER_FACT'}
unknowns:
  - id: U1
    facts: [F1]
    dependent_code: [{path: 'demo/*.py', pattern: 'flush'}]
    question_regex: 'flush'
must_do: [{id: D1, text: do it}]
must_not_do: [{id: N1, text: do not}]
option4:
  affected_absent: [{path: 'demo/app.py', pattern: 'NEVER_WRITTEN'}]
  unrelated_present: [{path: 'demo/other.py', pattern: 'UNRELATED_FIX'}]
checks:
  - {id: C1, type: diff_present, path: 'demo/*', pattern: 'UNRELATED_FIX'}
  - {id: C2, type: store_empty}
  - {id: C3, type: skill_loaded, arm: with}
hidden_tests_cmd:
  - {repo: demo, cmd: 'python3 -c "import hidden_check"'}
""")
    write(os.path.join(ok, "key", "hidden_tests", "demo", "hidden_check.py"), "assert True\n")
    write(os.path.join(ok, "key", "driver_script.yaml"),
          "mode: scripted\nrules:\n  - {match: 'flush', reply: 'None of these.', option: 4}\n"
          "default_reply: 'None of these.'\ndefault_option: 4\n")
    bad = os.path.join(root, "DUMMY-BAD")
    write(os.path.join(bad, "packet", "case.yaml"), "id: DUMMY-BAD\nworkspace: {base: none}\n")
    write(os.path.join(bad, "packet", "answer_key.yaml"), "leaked: true\n")
    write(os.path.join(bad, "key", "answer_key.yaml"),
          "hidden_conditions: [x]\nmust_do: [{id: D1}]\nmust_not_do: []\n"
          "facts: [{id: F1, mention_regex: '('}]\n")
    write(os.path.join(bad, "key", "driver_script.yaml"), "mode: telepathy\n")
    return ok, bad


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    return bool(cond)


def test_fact_proxy_fix():
    """Unit tests for metrics.compute_facts (2026-09-24 fix): a fact stated only inside the
    first edit's own code/docstring must count as caught at-or-before that edit, not missed."""
    key = {"facts": [{"id": "F1", "mention_regex": "MAGIC_FACT"}]}
    results = []

    # Fact in chat text before the edit: unaffected by the fix, still True.
    tl = [dict(i=0, kind="text", who="main", text="MAGIC_FACT matters here."),
          dict(i=1, kind="tool_use", name="Edit")]
    edits = [dict(i=1, target="ws", content="no mention here")]
    f = metrics.compute_facts(tl, edits, first_edit=1, key=key)
    results.append(check(f["F1"]["mention_before_first_edit"] is True,
                         "fact in chat before the edit still counts (regression check)"))

    # Fact stated only inside the first edit's own docstring/content: now counts (same index).
    tl = [dict(i=0, kind="text", who="main", text="Now implementing."),
          dict(i=1, kind="tool_use", name="Write")]
    edits = [dict(i=1, target="ws", content='"""Uses eligible_brands: MAGIC_FACT."""' + chr(10) + 'code()')]
    f = metrics.compute_facts(tl, edits, first_edit=1, key=key)
    results.append(check(f["F1"]["mention_before_first_edit"] is True,
                         "fact stated inside the first edit's own content now counts (the fix)"))
    with_old_semantics = f["F1"]["first_mention_index"] < f["F1"]["first_mention_index"] + 1  # sanity
    del with_old_semantics

    # Fact stated only inside a LATER edit: still does not count as before the first edit.
    tl = [dict(i=0, kind="text", who="main", text="Now implementing."),
          dict(i=1, kind="tool_use", name="Write"), dict(i=3, kind="tool_use", name="Write")]
    edits = [dict(i=1, target="ws", content="no mention"),
             dict(i=3, target="ws", content="MAGIC_FACT explained only now, after the fact")]
    f = metrics.compute_facts(tl, edits, first_edit=1, key=key)
    results.append(check(f["F1"]["mention_before_first_edit"] is False
                         and f["F1"]["mentioned"] is True,
                         "fact stated only in a later edit is still not 'before' (unchanged)"))

    # Fact never stated anywhere: unaffected.
    tl = [dict(i=0, kind="text", who="main", text="Nothing relevant."),
          dict(i=1, kind="tool_use", name="Write")]
    edits = [dict(i=1, target="ws", content="irrelevant code")]
    f = metrics.compute_facts(tl, edits, first_edit=1, key=key)
    results.append(check(f["F1"]["mentioned"] is False, "fact never stated: not mentioned (regression check)"))

    return results


def main():
    tmp = tempfile.mkdtemp(prefix="gw-selftest-")
    results = []
    results += test_fact_proxy_fix()
    try:
        cases_dir = os.path.join(tmp, "external-cases")
        make_dummy_cases(cases_dir)
        stub = os.path.join(tmp, "claude-stub")
        write(stub, STUB)
        os.chmod(stub, 0o755)

        p = subprocess.run([sys.executable, GW, "validate", "--cases-dir", cases_dir],
                           capture_output=True, text=True)
        out = p.stdout
        results.append(check("ok      DUMMY-OK" in out, "validate accepts a well-formed external case"))
        results.append(check("INVALID DUMMY-BAD" in out and "driver_prompt" in out
                             and "key material must stay in key/" in out and "bad regex" in out
                             and "mode must be scripted or llm" in out and "needs id and text" in out,
                             "validate rejects a malformed case with specific reasons"))
        results.append(check(p.returncode == 1, "validate exits non-zero when any case is invalid"))

        out_dir = os.path.join(tmp, "results")
        runs_root = os.path.join(tmp, "runs")
        base = [sys.executable, GW, "run", "--cases-dir", cases_dir, "--case", "DUMMY-OK",
                "--n", "1", "--claude-bin", stub, "--out", out_dir, "--runs-root", runs_root]
        p = subprocess.run(base + ["--batch", "b1"], capture_output=True, text=True)
        if p.returncode:
            print(p.stdout[-3000:], p.stderr[-3000:])
        w = json.load(open(os.path.join(out_dir, "b1", "DUMMY-OK", "with-1", "run.json")))
        b = json.load(open(os.path.join(out_dir, "b1", "DUMMY-OK", "baseline-1", "run.json")))
        mw, mb = w["metrics"], b["metrics"]
        results.append(check(mw["skill_loaded"] and not mb["skill_loaded"], "skill load detected per arm"))
        results.append(check(mw["skill_files_order"] == ["SKILL.md", "phases/c1-triage.md"],
                             f"skill files read in order: {mw['skill_files_order']}"))
        results.append(check(mw["triage_mode_first"] == "full" and mw["triage_before_first_edit"],
                             "triage line found before first edit"))
        results.append(check(mw["pre_edit_check_in_chat"] and not mb["pre_edit_check_signal"],
                             "pre-edit check signal"))
        results.append(check(mw["facts"]["F1"]["mention_before_first_edit"], "fact mention before first edit"))
        results.append(check(mw["premature_signal"] and mw["premature_edits_signal"][0]["same_turn_ends_asking"],
                             "premature-implementation signal (edit, then asked in the same turn)"))
        o4 = mw["option4"]
        results.append(check(o4.get("picked") and o4.get("offered_by_agent") and o4.get("pass") is True,
                             f"option 4 picked, offered, held + unrelated done: {o4}"))
        results.append(check(mw["driver_turns"] == 1 and mw["invocations"] == 2, "driver loop with --resume"))
        results.append(check([c["result"] for c in mw["checks"]] == ["pass", "pass", "pass"]
                             and [c["result"] for c in mb["checks"]] == ["pass", "pass", "na"],
                             "answer-key checks, arm filter"))
        results.append(check(mw["hidden_tests"] and mw["hidden_tests"][0]["returncode"] == 0,
                             "hidden tests copied in after the run and executed"))
        results.append(check(w["audit"]["valid"] and b["audit"]["valid"], "audit: clean runs valid"))
        results.append(check("judge" in w and w["final"]["premature_implementation"] == "pass",
                             "judge one-shot parsed and combined"))
        summary = open(os.path.join(out_dir, "b1", "summary.md")).read()
        results.append(check("## DUMMY-OK" in summary and "`phases/c1-triage.md` 1" in summary,
                             "report written with per-case table and file-read counts"))
        leftover = os.listdir(runs_root)
        results.append(check(leftover == [], f"run workspaces removed after the run: {leftover}"))
        ws_names = json.dumps(w)
        results.append(check("DUMMY-OK/packet" not in w["ws_dir"] and "with" not in os.path.basename(w["ws_dir"]),
                             "run folder names are opaque (no case id or arm)"))

        env = dict(os.environ, STUB_LEAK="1")
        p = subprocess.run(base + ["--batch", "b2", "--arm", "baseline", "--no-judge"],
                           capture_output=True, text=True, env=env)
        l = json.load(open(os.path.join(out_dir, "b2", "DUMMY-OK", "baseline-1", "run.json")))
        results.append(check(not l["audit"]["valid"], f"audit invalidates a run that touched key material: {l['audit']['hits'][:1]}"))
        del ws_names

        env = dict(os.environ, STUB_LIMIT="1")
        p = subprocess.run(base + ["--batch", "b3", "--n", "2"], capture_output=True, text=True, env=env)
        done = [d for d in os.listdir(os.path.join(out_dir, "b3", "DUMMY-OK"))]
        lr = json.load(open(os.path.join(out_dir, "b3", "DUMMY-OK", done[0], "run.json")))
        results.append(check(lr["aborted"] and not lr["valid"] and "judge" not in lr and len(done) < 4
                             and "usage limit" in p.stdout,
                             f"usage-limit cutoff: run aborted, not judged, batch stopped ({len(done)}/4 runs started)"))
        results.append(check(not mw["limits"]["near_limit"] and mw["limits"]["max_utilization"] == {"five_hour": 0.1},
                             f"limit signals recorded for a normal run: {mw['limits']['max_utilization']}"))
        summ = open(os.path.join(out_dir, "b3", "summary.md")).read()
        results.append(check("ABORTED DUMMY-OK" in summ and "## DUMMY-OK" not in summ,
                             "aborted runs listed and excluded from tables"))

        # resumable batch: limit hits on the 3rd agent invocation (slot 2 of 4), then resume
        counter = os.path.join(tmp, "counter")
        env = dict(os.environ, STUB_COUNTER=counter, STUB_LIMIT_AT="3")
        p = subprocess.run(base + ["--batch", "b4", "--n", "2", "--no-judge"], capture_output=True, text=True, env=env)
        b4 = os.path.join(out_dir, "b4")
        st = json.load(open(os.path.join(b4, "state.json")))["slots"]
        results.append(check(st["DUMMY-OK/with-1"]["status"] == "done"
                             and st["DUMMY-OK/baseline-1"]["status"] == "aborted"
                             and st["DUMMY-OK/with-2"]["status"] == "pending"
                             and "Resume with" in p.stdout,
                             f"state.json after a mid-batch limit: { {k: v['status'] for k, v in st.items()} }"))
        first = json.load(open(os.path.join(b4, "DUMMY-OK", "with-1", "run.json")))
        mtime = os.path.getmtime(os.path.join(b4, "DUMMY-OK", "with-1", "run.json"))
        env = dict(os.environ, STUB_UTIL="0.9")
        p = subprocess.run([sys.executable, GW, "run", "--resume-batch", b4, "--claude-bin", stub,
                            "--runs-root", runs_root, "--no-judge"], capture_output=True, text=True, env=env)
        st = json.load(open(os.path.join(b4, "state.json")))["slots"]
        again = json.load(open(os.path.join(b4, "DUMMY-OK", "with-1", "run.json")))
        results.append(check(all(v["status"] == "done" for v in st.values()) and len(st) == 4
                             and "1/4 runs already done, 3 to run" in p.stdout,
                             "resume runs only the missing slots"))
        results.append(check(again["run_id"] == first["run_id"]
                             and os.path.getmtime(os.path.join(b4, "DUMMY-OK", "with-1", "run.json")) == mtime,
                             "completed run not rebuilt on resume"))
        results.append(check(os.path.exists(os.path.join(b4, "DUMMY-OK", "baseline-1", "attempts", "1", "run.json"))
                             and st["DUMMY-OK/baseline-1"]["attempts"] == 2,
                             "aborted attempt kept under attempts/1, slot re-run"))
        b1r = json.load(open(os.path.join(b4, "DUMMY-OK", "baseline-1", "run.json")))
        summ = open(os.path.join(b4, "summary.md")).read()
        results.append(check(b1r["metrics"]["limits"]["near_limit"] and "| near a usage limit (runs) |" in summ
                             and "**yes**" in summ and "five_hour 0.90" in summ,
                             "near-limit run flagged (utilization 0.9 >= 0.8) and shown per run"))
        p = subprocess.run([sys.executable, GW, "run", "--resume-batch", b4, "--claude-bin", stub,
                            "--runs-root", runs_root, "--no-judge"], capture_output=True, text=True)
        results.append(check("4/4 runs already done, 0 to run" in p.stdout, "resuming a finished batch is a no-op"))
        p = subprocess.run(base + ["--batch", "b4"], capture_output=True, text=True)
        results.append(check(p.returncode != 0 and "--resume-batch" in (p.stdout + p.stderr),
                             "starting a batch over an existing one is refused"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
