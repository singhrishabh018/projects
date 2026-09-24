#!/usr/bin/env python3
"""Groundwork eval harness.

  gw_eval.py validate --cases-dir DIR           check case format; build each workspace dry
  gw_eval.py run --cases-dir DIR [options]      run cases with and without the skill
  gw_eval.py rescore RESULTS_DIR                re-run the judge on stored runs
  gw_eval.py report RESULTS_DIR                 per-case with/without tables

See eval/README.md.
"""
import argparse
import concurrent.futures as cf
import datetime
import fnmatch
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases as cases_mod  # noqa: E402
import claude_cli  # noqa: E402
import driver as driver_mod  # noqa: E402
import metrics  # noqa: E402
import score  # noqa: E402
import workspace  # noqa: E402

HARNESS = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.dirname(HARNESS)
REPO_DIR = os.path.dirname(EVAL_DIR)
DEFAULT_SKILL = os.path.join(REPO_DIR, "skill", "groundwork")
DEFAULT_RUNS_ROOT = os.environ.get("GW_EVAL_RUNS", "/tmp/gw-eval-runs")

_lock = threading.Lock()
_stop = threading.Event()  # set when the account hits a usage limit: schedule no more runs

# The CLI reports an exhausted plan/usage limit as a normal-looking final message.
LIMIT_RE = re.compile(r"hit your (\w+ )?limit|usage limit|rate limit|limit .{0,20}resets", re.I)


def aborted_reason(result):
    """Why an invocation result can't be scored (None if it can)."""
    if result is None:
        return "no result event"
    text = result.get("result") or ""
    if LIMIT_RE.search(text) and len(text) < 300:
        return "usage limit: " + text.strip()[:120]
    if result.get("api_error_status"):
        return f"API error {result.get('api_error_status')}"
    return None


def log(msg):
    with _lock:
        print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


# --------------------------------------------------------------------------- validate
def cmd_validate(args):
    dirs = cases_mod.discover(args.cases_dir, args.case)
    if not dirs:
        print(f"no case folders found in {args.cases_dir}")
        return 1
    bad = 0
    for d in dirs:
        errs = cases_mod.validate(d)
        name = os.path.basename(d)
        if errs:
            bad += 1
            print(f"INVALID {name}")
            for e in errs:
                print(f"   - {e}")
            continue
        case = cases_mod.Case(d)
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            repos = workspace.build(case, ws)
            leaked = [p for p in workspace.list_files(ws)
                      if "answer_key" in p or "driver_script" in p or p.startswith("key/")]
            mcp_ok = _probe_mcp(case.connectors_dir()) if case.connectors_dir() else "none"
        if leaked:
            bad += 1
            print(f"INVALID {name}: key material in workspace: {leaked}")
            continue
        print(f"ok      {name}: repos={repos} connectors={mcp_ok} "
              f"driver={case.driver.get('mode', 'scripted')} "
              f"facts={len(case.key.get('facts') or [])} unknowns={len(case.key.get('unknowns') or [])} "
              f"checks={len(case.key.get('checks') or [])} "
              f"hidden_tests={'yes' if case.hidden_tests_dir() else 'no'}")
    print(f"{len(dirs) - bad}/{len(dirs)} valid")
    return 1 if bad else 0


def _probe_mcp(conn_dir):
    """Round-trip initialize + tools/list against mockmcp.py; return tool names."""
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "validate", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    p = subprocess.run([sys.executable, os.path.join(HARNESS, "mockmcp.py"), conn_dir],
                       input="\n".join(json.dumps(r) for r in reqs) + "\n",
                       capture_output=True, text=True, timeout=30)
    for line in p.stdout.splitlines():
        msg = json.loads(line)
        if msg.get("id") == 2:
            return [t["name"] for t in msg["result"]["tools"]]
    return f"ERROR {p.stderr[-300:]}"


# --------------------------------------------------------------------------- audit
def audit(tl, run_root, runs_root, forbidden):
    """Any sign the agent reached key material, the eval repo, or another run → invalid."""
    hits = []
    other_run = re.compile(re.escape(runs_root.rstrip("/")) + r"/(?!" +
                           re.escape(os.path.basename(run_root)) + r"\b)[\w-]+")
    for e in tl:
        if e["kind"] == "tool_use":
            blob = json.dumps(e.get("input") or {})
        elif e["kind"] == "tool_result":
            blob = e.get("text") or ""
        else:
            continue
        for pat in forbidden:
            if pat in blob:
                hits.append({"i": e["i"], "kind": e["kind"], "match": pat})
        if other_run.search(blob):
            hits.append({"i": e["i"], "kind": e["kind"], "match": "another run's folder"})
    broad = [e["i"] for e in tl if e["kind"] == "tool_use" and e.get("name") == "Bash"
             and re.search(r"\b(find|grep -r|rg|ls -R)\s+/(\s|$)", (e.get("input") or {}).get("command", ""))]
    return {"valid": not hits, "hits": hits[:20], "broad_searches": broad}


# --------------------------------------------------------------------------- run one
def run_one(case, arm, idx, args, batch_dir):
    lim = case.limits
    run_id = uuid.uuid4().hex[:10]
    root = os.path.join(args.runs_root, run_id)  # opaque name: no case id or arm in paths
    ws = os.path.join(root, "workspace")
    cfg = os.path.join(root, "profile")
    gw = os.path.join(root, "store")
    for d in (ws, cfg, gw):
        os.makedirs(d, exist_ok=True)
    out_dir = os.path.join(batch_dir, case.id, f"{arm}-{idx}")
    os.makedirs(out_dir, exist_ok=True)
    repos = workspace.build(case, ws)

    add_dir = None
    if arm == "with":
        add_dir = os.path.join(root, "skill")
        shutil.copytree(args.skill_dir, os.path.join(add_dir, ".claude", "skills", "groundwork"),
                        ignore=shutil.ignore_patterns("__pycache__"))
    mcp_config = None
    if case.connectors_dir():
        conn = os.path.join(root, "connectors")
        shutil.copytree(case.connectors_dir(), conn)
        server = os.path.join(root, "sources_server.py")
        shutil.copy(os.path.join(HARNESS, "mockmcp.py"), server)
        mcp_config = os.path.join(root, "mcp.json")
        with open(mcp_config, "w") as f:
            json.dump({"mcpServers": {"sources": {
                "command": sys.executable, "args": [server, conn],
                "env": {"MOCKMCP_LOG": os.path.join(root, "mcp-calls.jsonl")}}}}, f)

    env = claude_cli.child_env(cfg, {"GROUNDWORK_HOME": gw})
    drv = driver_mod.Driver(case.driver, claude_bin=args.claude_bin, model=args.driver_model,
                            config_dir=os.path.join(root, "driver-profile"), cwd=root)
    os.makedirs(os.path.join(root, "driver-profile"), exist_ok=True)

    msg, sid = case.prompt, None
    invocations, results, dturns, notes = [], [], [], []
    spent, t0 = 0.0, time.time()
    aborted = None
    for k in range(lim["max_driver_turns"] + 1):
        left = min(lim["max_budget_usd"], args.max_run_usd) - spent
        if left < 0.25:
            notes.append("run budget exhausted")
            break
        cmd = claude_cli.agent_cmd(args.claude_bin, msg, args.model, effort=args.effort,
                                   max_turns=lim["max_turns"], max_budget=left, resume=sid,
                                   add_dir=add_dir, mcp_config=mcp_config,
                                   disallowed=tuple(lim.get("disallowed_tools") or ()))
        tpath = os.path.join(root, f"transcript-{k}.jsonl")
        events, result, rc, stderr, timed_out = claude_cli.run_stream(
            cmd, ws, env, tpath, lim["timeout_minutes"] * 60)
        invocations.append(events)
        results.append(result)
        if stderr.strip():
            notes.append(f"invocation {k} stderr: {stderr.strip()[-400:]}")
        if timed_out:
            notes.append(f"invocation {k} timed out")
        if result is None:
            notes.append(f"invocation {k}: no result event (rc={rc})")
            break
        spent += float(result.get("total_cost_usd") or 0)
        sid = result.get("session_id") or sid
        why = aborted_reason(result)
        if why:
            aborted = why
            notes.append(f"invocation {k} aborted: {why}")
            if why.startswith("usage limit"):
                _stop.set()
            break
        if result.get("is_error"):
            notes.append(f"invocation {k} ended with {result.get('subtype')}")
            break
        reply, option, source = drv.respond(result.get("result") or "")
        if reply == driver_mod.STOP:
            break
        if k == lim["max_driver_turns"]:
            notes.append("max driver turns reached while the agent was still asking")
            break
        dturns.append({"after_invocation": k, "reply": reply, "option": option,
                       "source": source, "t": time.time()})
        msg = reply
    wall = time.time() - t0

    diffs = workspace.collect(ws, repos)
    store_files = workspace.list_files(gw)
    hidden = run_hidden_tests(case, ws)

    tl, init = metrics.build_timeline(invocations, dturns)
    forbidden = [case.dir, EVAL_DIR, REPO_DIR, "answer_key", "driver_script", "/key/"]
    if args.cases_dir:
        forbidden.append(os.path.abspath(args.cases_dir))
    aud = audit(tl, root, args.runs_root, sorted(set(forbidden), key=len, reverse=True))

    ctx = dict(timeline=tl, init=init, arm=arm, ws_dir=ws, gw_home=gw, key=case.key,
               diffs=diffs, store_files=store_files, invocation_results=results,
               driver_turns=dturns, hidden_tests=hidden, repos=repos,
               raw_invocations=invocations, near_limit_threshold=args.near_limit)
    m = metrics.compute(ctx)
    m["harness_wall_seconds"] = round(wall, 1)
    m["driver_cost_usd"] = round(drv.cost, 4)

    run = {"case": case.id, "arm": arm, "index": idx, "run_id": run_id, "model": args.model,
           "aborted": aborted, "valid": aud["valid"] and not aborted,
           "effort": args.effort, "driver_model": args.driver_model,
           "started": datetime.datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
           "notes": notes, "audit": aud, "metrics": m, "driver_turns": dturns,
           "final_messages": [(r or {}).get("result") for r in results],
           "inventory": _inventory(init), "ws_dir": ws, "gw_home": gw, "diffs": diffs}

    # persist raw evidence
    with gzip.open(os.path.join(out_dir, "timeline.json.gz"), "wt") as f:
        json.dump(tl, f)
    for k in range(len(invocations)):
        src = os.path.join(root, f"transcript-{k}.jsonl")
        if os.path.exists(src):
            with open(src, "rb") as fi, gzip.open(os.path.join(out_dir, f"transcript-{k}.jsonl.gz"), "wb") as fo:
                shutil.copyfileobj(fi, fo)
    with open(os.path.join(out_dir, "diff.patch"), "w") as f:
        f.write("\n".join(d.get("diff", "") for d in diffs.values()))
    if store_files:
        shutil.copytree(gw, os.path.join(out_dir, "store"), dirs_exist_ok=True)
    if os.path.exists(os.path.join(root, "mcp-calls.jsonl")):
        shutil.copy(os.path.join(root, "mcp-calls.jsonl"), out_dir)

    if not args.no_judge and not aborted:
        j = score.judge(case, run, tl, args.claude_bin, args.judge_model,
                        _judge_profile(root), root)
        run["judge"] = j
        run["final"] = combine(run)
    _write_json(os.path.join(out_dir, "run.json"), _strip(run))
    if not args.keep_runs:
        shutil.rmtree(root, ignore_errors=True)
    total = m["agent_cost_usd"] + m["driver_cost_usd"] + (run.get("judge") or {}).get("cost_usd", 0)
    log(f"{case.id} {arm}-{idx}: agent ${m['agent_cost_usd']:.2f} total ${total:.2f} "
        f"turns={m['agent_turns']} driver_turns={m['driver_turns']} skill={m['skill_loaded']} "
        f"phases={m['phase_files_read']} valid={run['valid']}"
        + (f" ABORTED ({aborted})" if aborted else ""))
    return run, total


def _judge_profile(root):
    p = os.path.join(root, "judge-profile")
    os.makedirs(p, exist_ok=True)
    return p


def run_hidden_tests(case, ws):
    src = case.hidden_tests_dir()
    if not src:
        return None
    shutil.copytree(src, ws, dirs_exist_ok=True)
    out = []
    for item in case.key.get("hidden_tests_cmd") or []:
        cwd = os.path.join(ws, item.get("repo", ""))
        try:
            p = subprocess.run(item["cmd"], shell=True, cwd=cwd, capture_output=True, text=True,
                               timeout=300, env={k: v for k, v in os.environ.items()
                                                 if not k.startswith("CLAUDE")})
            out.append({"cmd": item["cmd"], "repo": item.get("repo"), "returncode": p.returncode,
                        "output": (p.stdout + p.stderr)[-2000:]})
        except subprocess.TimeoutExpired:
            out.append({"cmd": item["cmd"], "repo": item.get("repo"), "returncode": -1,
                        "output": "timeout"})
    return out


def combine(run):
    """Final per-run verdicts: automatic proxy AND judge where both are needed."""
    m, v = run["metrics"], (run.get("judge") or {}).get("verdict") or {}
    jf = {f["id"]: f for f in v.get("facts") or []}
    facts = {}
    for fid, auto in m["facts"].items():
        j = jf.get(fid) or {}
        facts[fid] = {
            "proxy_mention_before_edit": auto["mention_before_first_edit"],
            "judge_design_accounts": j.get("design_accounts_for_it"),
            # named proxy (G3): counts only if the judge confirms the design accounts for it
            "caught_before_code": bool(auto["mention_before_first_edit"] and j.get("design_accounts_for_it")),
        }
    pi = v.get("premature_implementation") or {}
    return {
        "facts": facts,
        "premature_implementation": pi.get("verdict"),
        "premature_signal": m["premature_signal"],
        "must_do_met": sum(1 for x in v.get("must_do") or [] if x["verdict"] == "met"),
        "must_do_total": len([x for x in v.get("must_do") or [] if x["verdict"] != "na"]),
        "must_not_violated": sum(1 for x in v.get("must_not_do") or [] if x["verdict"] == "violated"),
        "correctness_defects": len(v.get("correctness_defects_remaining") or []),
        "unnecessary_blocking": len(v.get("unnecessary_blocking") or []),
        "false_positives": len(v.get("false_positives") or []),
        "unnecessary_code": len(v.get("unnecessary_code") or []),
    }


def _inventory(init):
    init = init or {}
    return {k: init.get(k) for k in ("model", "tools", "skills", "mcp_servers", "plugins",
                                     "agents", "claude_code_version", "permissionMode")}


def _strip(run):
    r = dict(run)
    r["diffs"] = {k: {kk: vv for kk, vv in v.items() if kk != "diff"} for k, v in run["diffs"].items()}
    return r


def _write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


# --------------------------------------------------------------------------- run many
# Batch state: <batch>/state.json records every slot ("<case>/<arm>-<i>"):
#   pending | running | done | aborted | failed, with attempts, cost and reason.
# A slot counts as done only if its run.json exists and the run wasn't aborted; the files
# are the source of truth, state.json is the readable record. On --resume-batch, done slots
# are skipped and never rebuilt; every other slot's old files move to <slot>/attempts/<n>/.
RESUME_KEYS = ("cases_dir", "cases", "arms", "n", "model", "effort", "driver_model",
               "judge_model", "skill_dir")


def slot_status(batch_dir, case_id, arm, i):
    d = os.path.join(batch_dir, case_id, f"{arm}-{i}")
    rp = os.path.join(d, "run.json")
    if os.path.exists(rp):
        try:
            with open(rp) as f:
                return "aborted" if json.load(f).get("aborted") else "done"
        except ValueError:
            return "failed"
    if os.path.exists(os.path.join(d, "error.json")):
        return "failed"
    return "pending" if not os.path.isdir(d) or not os.listdir(d) else "failed"


def _archive_slot(batch_dir, case_id, arm, i):
    d = os.path.join(batch_dir, case_id, f"{arm}-{i}")
    if not os.path.isdir(d):
        return
    items = [x for x in os.listdir(d) if x != "attempts"]
    if not items:
        return
    adir = os.path.join(d, "attempts")
    n = len(os.listdir(adir)) + 1 if os.path.isdir(adir) else 1
    dest = os.path.join(adir, str(n))
    os.makedirs(dest)
    for x in items:
        shutil.move(os.path.join(d, x), os.path.join(dest, x))


class BatchState:
    def __init__(self, batch_dir):
        self.path = os.path.join(batch_dir, "state.json")
        self.data = {"slots": {}}
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.data = json.load(f)

    def set(self, slot, status, **extra):
        with _lock:
            rec = self.data["slots"].setdefault(slot, {"attempts": 0})
            if status == "running":
                rec["attempts"] = rec.get("attempts", 0) + 1
            rec["status"] = status
            rec["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
            rec.update(extra)
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self.data, f, indent=1, sort_keys=True)
            os.replace(tmp, self.path)


def cmd_run(args):
    if args.resume_batch:
        batch_dir = os.path.abspath(args.resume_batch)
        with open(os.path.join(batch_dir, "batch.json")) as f:
            meta = json.load(f)
        for k in RESUME_KEYS:  # the batch's own settings win; the run is the same experiment
            setattr(args, k, meta[k] if k != "cases" else meta[k])
        args.case = meta["cases"]
        args.arm = "both" if meta["arms"] == ["with", "baseline"] else meta["arms"][0]
        now = _git_head(args.skill_dir)
        if now != meta["skill_commit"] and not args.allow_skill_change:
            sys.exit(f"refusing to resume: skill is {now}, batch was run with {meta['skill_commit']}. "
                     "Mixing skill versions in one batch breaks the comparison. "
                     "Use --allow-skill-change only if the change can't affect behaviour.")
        cs = cases_mod.load_all(args.cases_dir, args.case)
        arms = meta["arms"]
        meta.setdefault("resumes", []).append(datetime.datetime.now().isoformat(timespec="seconds"))
    else:
        cs = cases_mod.load_all(args.cases_dir, args.case)
        arms = ["with", "baseline"] if args.arm == "both" else [args.arm]
        batch = args.batch or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        batch_dir = os.path.abspath(os.path.join(args.out, batch))
        if os.path.exists(os.path.join(batch_dir, "batch.json")):
            sys.exit(f"{batch_dir} already exists; use --resume-batch {batch_dir} or a new --batch")
        meta = {"batch": batch, "model": args.model, "effort": args.effort,
                "driver_model": args.driver_model, "judge_model": args.judge_model,
                "n": args.n, "arms": arms, "cases": [c.id for c in cs],
                "cases_dir": os.path.abspath(args.cases_dir),
                "skill_dir": args.skill_dir, "skill_commit": _git_head(args.skill_dir),
                "claude_version": _claude_version(args.claude_bin),
                "near_limit_threshold": args.near_limit,
                "ambient_claude_dir": sorted(os.listdir(os.path.expanduser("~/.claude")))
                if os.path.isdir(os.path.expanduser("~/.claude")) else None,
                "started": datetime.datetime.now().isoformat(timespec="seconds"),
                "spent_usd": 0.0}
    os.makedirs(batch_dir, exist_ok=True)
    os.makedirs(args.runs_root, exist_ok=True)
    # the eval repo and the cases must not live inside the runs root
    for p in (EVAL_DIR, os.path.abspath(args.cases_dir)):
        if os.path.abspath(p).startswith(os.path.abspath(args.runs_root) + os.sep):
            sys.exit(f"refusing: {p} is inside the runs root {args.runs_root}")
    _write_json(os.path.join(batch_dir, "batch.json"), meta)
    state = BatchState(batch_dir)

    # interleave arms so cache warmth and time-of-day effects spread over both
    slots = [(c, arm, i) for i in range(1, args.n + 1) for c in cs for arm in arms]
    jobs = []
    for c, arm, i in slots:
        st = slot_status(batch_dir, c.id, arm, i)
        slot = f"{c.id}/{arm}-{i}"
        if st == "done":
            if state.data["slots"].get(slot, {}).get("status") != "done":
                state.set(slot, "done")
            continue
        state.set(slot, st if st != "pending" else "pending")
        jobs.append((c, arm, i))
    log(f"{batch_dir}: {len(slots) - len(jobs)}/{len(slots)} runs already done, {len(jobs)} to run")
    if not jobs:
        import report
        report.write(batch_dir)
        return 0

    spent = float(meta.get("spent_usd") or 0)  # cumulative across resumes
    if args.warmup:
        for arm in arms:
            spent += _warmup(arm, args)
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {}
        it = iter(jobs)
        while True:
            while len(pending) < args.jobs:
                if spent >= args.max_total_usd or _stop.is_set():
                    break
                job = next(it, None)
                if job is None:
                    break
                c, arm, i = job
                _archive_slot(batch_dir, c.id, arm, i)
                state.set(f"{c.id}/{arm}-{i}", "running")
                pending[pool.submit(run_one, *job, args, batch_dir)] = job
            if not pending:
                break
            done, _ = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for fut in done:
                job = pending.pop(fut)
                slot = f"{job[0].id}/{job[1]}-{job[2]}"
                try:
                    run, cost = fut.result()
                    spent += cost
                    state.set(slot, "aborted" if run.get("aborted") else "done",
                              cost_usd=round(cost, 4), reason=run.get("aborted"),
                              near_limit=run["metrics"]["limits"]["near_limit"])
                except Exception as e:  # keep the batch going; record the failure
                    log(f"{slot} FAILED: {e!r}")
                    _write_json(os.path.join(batch_dir, job[0].id, f"{job[1]}-{job[2]}", "error.json"),
                                {"error": repr(e)})
                    state.set(slot, "failed", reason=repr(e)[:300])
            meta["spent_usd"] = round(spent, 2)
            _write_json(os.path.join(batch_dir, "batch.json"), meta)
    missing = [s for s, r in state.data["slots"].items() if r.get("status") != "done"]
    if _stop.is_set():
        log("stopped: the account hit a usage limit; remaining runs were not started.")
    if spent >= args.max_total_usd:
        log(f"stopped: batch spend ${spent:.2f} reached --max-total-usd {args.max_total_usd}")
    if missing:
        log(f"{len(missing)} runs not done: {', '.join(sorted(missing)[:12])}"
            f"{' …' if len(missing) > 12 else ''}. Resume with: gw_eval.py run --resume-batch {batch_dir}")
    meta["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    meta["spent_usd"] = round(spent, 2)
    _write_json(os.path.join(batch_dir, "batch.json"), meta)
    import report
    report.write(batch_dir)
    log(f"done: {batch_dir} (spent ${spent:.2f} cumulative)")
    return 0


def _warmup(arm, args):
    root = tempfile.mkdtemp(prefix="warm-", dir=args.runs_root)
    try:
        cfg = os.path.join(root, "profile")
        os.makedirs(cfg)
        add_dir = None
        if arm == "with":
            add_dir = os.path.join(root, "skill")
            shutil.copytree(args.skill_dir, os.path.join(add_dir, ".claude", "skills", "groundwork"))
        cmd = claude_cli.agent_cmd(args.claude_bin, "Reply with OK only.", args.model,
                                   effort=args.effort, max_turns=2, max_budget=1, add_dir=add_dir)
        _, res, _, _, _ = claude_cli.run_stream(cmd, root, claude_cli.child_env(cfg),
                                                os.path.join(root, "t.jsonl"), 300)
        cost = float((res or {}).get('total_cost_usd') or 0)
        log(f"warm-up {arm}: ${cost:.3f}")
        return cost
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _git_head(path):
    """The commit that last touched `path`'s content — not the whole repo's HEAD, which moves
    on every unrelated commit (results, harness code) and would make --resume-batch's
    skill-change guard fire on runs where the skill itself never changed."""
    p = subprocess.run(["git", "-C", path, "log", "-1", "--format=%h", "--", "."],
                       capture_output=True, text=True)
    dirty = subprocess.run(["git", "-C", path, "status", "--porcelain", "--", "."],
                           capture_output=True, text=True).stdout.strip()
    return (p.stdout.strip() or "unknown") + ("+dirty" if dirty else "")


def _claude_version(claude_bin):
    try:
        return subprocess.run([claude_bin, "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except OSError:
        return None


# --------------------------------------------------------------------------- rescore
def cmd_recompute_facts(args):
    """Retroactively re-score already-run transcripts with a fixed automatic metric. No agent
    or judge calls — pure local recomputation from the saved timeline. Old values are kept
    under metrics["facts_pre_2026-09-24_proxy_fix"] / final["facts_pre_2026-09-24_proxy_fix"]
    so the report can show both."""
    batch_dir = os.path.abspath(args.results_dir)
    meta = json.load(open(os.path.join(batch_dir, "batch.json")))
    cs = {c.id: c for c in cases_mod.load_all(args.cases_dir or meta["cases_dir"])}
    changed = []
    for case_id in sorted(os.listdir(batch_dir)):
        cdir = os.path.join(batch_dir, case_id)
        if not os.path.isdir(cdir) or case_id not in cs:
            continue
        key = cs[case_id].key
        for rd in sorted(os.listdir(cdir)):
            rpath = os.path.join(cdir, rd, "run.json")
            tpath = os.path.join(cdir, rd, "timeline.json.gz")
            if not os.path.exists(rpath) or not os.path.exists(tpath):
                continue
            run = json.load(open(rpath))
            if run.get("aborted"):
                continue
            with gzip.open(tpath, "rt") as f:
                tl = json.load(f)
            m = run["metrics"]
            if "facts_pre_2026-09-24_proxy_fix" in m:
                continue  # already recomputed; recompute is idempotent by design, skip re-doing it
            edits = []
            for e in tl:
                if e["kind"] == "tool_use":
                    t = metrics.edit_target(e, run["ws_dir"], run["gw_home"])
                    if t:
                        edits.append(dict(i=e["i"], inv=e["inv"], who=e["who"], tool=e["name"],
                                          target=t[0], path=t[1], content=t[2]))
            old_facts = m.get("facts") or {}
            new_facts = metrics.compute_facts(tl, edits, m.get("first_code_edit_index"), key)
            if new_facts == old_facts:
                continue
            m["facts_pre_2026-09-24_proxy_fix"] = old_facts
            m["facts"] = new_facts
            # premature_edits_signal shares the same first_mention_index; recompute it too so
            # the two stay consistent (the fix broadens what counts as "surfaced"). Mirrors the
            # block in metrics.compute() exactly, with new_facts in place of facts.
            code_edits = [x for x in edits if x["target"] == "ws"]
            results = [e for e in tl if e["kind"] == "result"]
            final_by_inv = {e["inv"]: e["text"] for e in results}
            prem = []
            for u in key.get("unknowns") or []:
                qrx = re.compile(u["question_regex"], re.I | re.M) if u.get("question_regex") else None
                fact_idx = [new_facts[f]["first_mention_index"] for f in u.get("facts") or [] if f in new_facts]
                for x in code_edits:
                    for dc in u.get("dependent_code") or []:
                        path_ok = (x["path"] is None or fnmatch.fnmatch(x["path"], dc["path"]))
                        if not (path_ok and x["content"] and re.search(dc["pattern"], x["content"], re.I | re.M)):
                            continue
                        if x["path"] is None and dc["path"].split("/")[0] not in x["content"]:
                            continue
                        final = final_by_inv.get(x["inv"], "")
                        asked_after = driver_mod.asks_question(final) and (qrx is None or bool(qrx.search(final)))
                        before_fact = bool(fact_idx) and all(fi is None or fi > x["i"] for fi in fact_idx)
                        prem.append(dict(unknown=u["id"], edit_index=x["i"], path=x["path"],
                                         invocation=x["inv"], before_fact_mention=before_fact,
                                         same_turn_ends_asking=asked_after,
                                         signal=before_fact or asked_after))
                        break
            if m.get("premature_edits_signal") is not None:
                m["premature_edits_signal_pre_2026-09-24_proxy_fix"] = m["premature_edits_signal"]
            if m.get("premature_signal") is not None:
                m["premature_signal_pre_2026-09-24_proxy_fix"] = m["premature_signal"]
            m["premature_edits_signal"] = prem
            m["premature_signal"] = any(p["signal"] for p in prem)
            if run.get("final"):
                old_final_facts = run["final"].get("facts")
                jf = {f["id"]: f for f in ((run.get("judge") or {}).get("verdict") or {}).get("facts") or []}
                new_final_facts = {}
                for fid, auto in new_facts.items():
                    j = jf.get(fid) or {}
                    new_final_facts[fid] = {
                        "proxy_mention_before_edit": auto["mention_before_first_edit"],
                        "judge_design_accounts": j.get("design_accounts_for_it"),
                        "caught_before_code": bool(auto["mention_before_first_edit"] and j.get("design_accounts_for_it")),
                    }
                run["final"]["facts_pre_2026-09-24_proxy_fix"] = old_final_facts
                run["final"]["facts"] = new_final_facts
            _write_json(rpath, run)
            changed.append(f"{case_id}/{rd}")
            log(f"recomputed facts: {case_id}/{rd}")
    log(f"{len(changed)} runs changed: {changed}")
    import report
    report.write(batch_dir)
    return 0


def cmd_rescore(args):
    batch_dir = os.path.abspath(args.results_dir)
    meta = json.load(open(os.path.join(batch_dir, "batch.json")))
    cs = {c.id: c for c in cases_mod.load_all(args.cases_dir or meta["cases_dir"])}
    for case_id in sorted(os.listdir(batch_dir)):
        cdir = os.path.join(batch_dir, case_id)
        if not os.path.isdir(cdir) or case_id not in cs:
            continue
        for rd in sorted(os.listdir(cdir)):
            rpath = os.path.join(cdir, rd, "run.json")
            if not os.path.exists(rpath):
                continue
            run = json.load(open(rpath))
            with gzip.open(os.path.join(cdir, rd, "timeline.json.gz"), "rt") as f:
                tl = json.load(f)
            diff = open(os.path.join(cdir, rd, "diff.patch")).read()
            run["diffs"] = {"all": {"diff": diff}}
            store = os.path.join(cdir, rd, "store")
            run["gw_home"] = store if os.path.isdir(store) else run["gw_home"]
            with tempfile.TemporaryDirectory() as tmp:
                run["judge"] = score.judge(cs[case_id], run, tl, args.claude_bin,
                                           args.judge_model, tmp, tmp)
            run["final"] = combine(run)
            run["diffs"] = {}
            _write_json(rpath, run)
            log(f"rescored {case_id}/{rd}: ${run['judge']['cost_usd']:.2f}")
    import report
    report.write(batch_dir)
    return 0


def cmd_report(args):
    import report
    print(report.write(os.path.abspath(args.results_dir)))
    return 0


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("--cases-dir", default=cases_mod.DEFAULT_CASES)
    v.add_argument("--case", action="append")

    r = sub.add_parser("run")
    r.add_argument("--cases-dir", default=cases_mod.DEFAULT_CASES)
    r.add_argument("--case", action="append", help="case id (repeatable); default: all")
    r.add_argument("--arm", choices=["with", "baseline", "both"], default="both")
    r.add_argument("--n", type=int, default=3)
    r.add_argument("--model", default="claude-opus-5")
    r.add_argument("--effort", default="medium",
                   help="passed as --effort to agent runs (M1/M2 runs inherited medium)")
    r.add_argument("--driver-model", default="claude-sonnet-5")
    r.add_argument("--judge-model", default="claude-opus-5")
    r.add_argument("--skill-dir", default=DEFAULT_SKILL)
    r.add_argument("--out", default=os.path.join(EVAL_DIR, "results"))
    r.add_argument("--batch", help="results sub-folder name (default: timestamp)")
    r.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT,
                   help="where run workspaces live; must not contain the eval repo or cases")
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--max-run-usd", type=float, default=6.0)
    r.add_argument("--max-total-usd", type=float, default=150.0)
    r.add_argument("--warmup", action="store_true", help="one cheap warm-up call per arm first")
    r.add_argument("--no-judge", action="store_true")
    r.add_argument("--keep-runs", action="store_true", help="keep run workspaces for debugging")
    r.add_argument("--claude-bin", default=os.environ.get("GW_EVAL_CLAUDE", "claude"))
    r.add_argument("--resume-batch", metavar="DIR",
                   help="continue an existing batch: run only slots that aren't done, with the "
                        "batch's recorded settings; completed runs are never rebuilt")
    r.add_argument("--allow-skill-change", action="store_true",
                   help="resume even though the skill changed since the batch started")
    r.add_argument("--near-limit", type=float, default=0.8,
                   help="flag a run as near a usage limit when account utilization reaches this")

    s = sub.add_parser("rescore")
    s.add_argument("results_dir")
    s.add_argument("--cases-dir")
    s.add_argument("--judge-model", default="claude-opus-5")
    s.add_argument("--claude-bin", default=os.environ.get("GW_EVAL_CLAUDE", "claude"))

    rf = sub.add_parser("recompute-facts",
                        help="retroactively re-score saved transcripts with a fixed automatic "
                             "metric; no agent or judge calls, pure local recomputation")
    rf.add_argument("results_dir")
    rf.add_argument("--cases-dir")

    p = sub.add_parser("report")
    p.add_argument("results_dir")

    args = ap.parse_args(argv)
    if getattr(args, "runs_root", None):
        args.runs_root = os.path.abspath(args.runs_root)
    if getattr(args, "skill_dir", None):
        args.skill_dir = os.path.abspath(args.skill_dir)
    return {"validate": cmd_validate, "run": cmd_run, "rescore": cmd_rescore,
            "recompute-facts": cmd_recompute_facts,
            "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
