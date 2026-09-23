"""Per-case with/without tables from a results batch. No aggregate score across cases."""
import json
import os
import statistics
from collections import Counter, defaultdict


def _load(batch_dir):
    runs = []
    for case_id in sorted(os.listdir(batch_dir)):
        cdir = os.path.join(batch_dir, case_id)
        if not os.path.isdir(cdir):
            continue
        for rd in sorted(os.listdir(cdir)):
            p = os.path.join(cdir, rd, "run.json")
            if os.path.exists(p):
                with open(p) as f:
                    runs.append(json.load(f))
    return runs


def _frac(xs):
    xs = [x for x in xs if x is not None]
    return f"{sum(1 for x in xs if x)}/{len(xs)}" if xs else "–"


def _money(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "–"
    return f"${statistics.mean(xs):.2f} ({min(xs):.2f}–{max(xs):.2f})"


def _num(xs, fmt="{:.1f}"):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "–"
    return fmt.format(statistics.mean(xs)) + f" ({fmt.format(min(xs))}–{fmt.format(max(xs))})"


def summarize(runs):
    by = defaultdict(lambda: defaultdict(list))
    for r in runs:
        by[r["case"]][r["arm"]].append(r)
    return by


def write(batch_dir):
    runs = _load(batch_dir)
    meta = {}
    if os.path.exists(os.path.join(batch_dir, "batch.json")):
        meta = json.load(open(os.path.join(batch_dir, "batch.json")))
    by = summarize(runs)
    out = [f"# Eval results — {meta.get('batch', os.path.basename(batch_dir))}", ""]
    out.append(f"Model `{meta.get('model')}` (effort {meta.get('effort')}), driver "
               f"`{meta.get('driver_model')}`, judge `{meta.get('judge_model')}`, skill "
               f"`{meta.get('skill_commit')}`, {meta.get('claude_version')}. "
               f"Spent ${meta.get('spent_usd', '?')}.")
    out.append("")
    out.append("Invalid runs (audit hit: agent reached key material, the eval repo or another run) "
               "are listed but excluded from every table.")
    out.append("")
    invalid = [r for r in runs if not r["audit"]["valid"]]
    for r in invalid:
        out.append(f"- INVALID {r['case']} {r['arm']}-{r['index']}: {r['audit']['hits'][:3]}")
    runs_ok = [r for r in runs if r["audit"]["valid"]]
    by = summarize(runs_ok)

    rows = [("n", lambda rs: str(len(rs))),
            ("skill loaded", lambda rs: _frac([r["metrics"]["skill_loaded"] for r in rs])),
            ("triage line before 1st edit", lambda rs: _frac([r["metrics"]["triage_before_first_edit"] for r in rs])),
            ("triage mode (first)", lambda rs: ", ".join(f"{k}×{v}" for k, v in Counter(
                r["metrics"]["triage_mode_first"] or "none" for r in rs).items())),
            ("pre-edit check signal", lambda rs: _frac([r["metrics"]["pre_edit_check_signal"] for r in rs
                                                        if r["metrics"]["first_code_edit_index"] is not None])),
            ("phase files read (runs with ≥1)", lambda rs: _frac([bool(r["metrics"]["phase_files_read"]) for r in rs])),
            ("caught before code (proxy ∧ judge)", lambda rs: _caught(rs)),
            ("  proxy only: mention before 1st edit", lambda rs: _caught(rs, proxy=True)),
            ("premature implementation: PASS", lambda rs: _frac([(r.get("final") or {}).get("premature_implementation") == "pass"
                                                                for r in rs if (r.get("final") or {}).get("premature_implementation") in ("pass", "fail")])),
            ("  premature auto signal fired", lambda rs: _frac([r["metrics"]["premature_signal"] for r in rs])),
            ("option 4 picked → pass", lambda rs: _frac([r["metrics"]["option4"].get("pass") for r in rs
                                                         if r["metrics"]["option4"].get("picked")])),
            ("must_do met", lambda rs: _ratio(rs, "must_do_met", "must_do_total")),
            ("must_not_do violated (runs)", lambda rs: _frac([(r.get("final") or {}).get("must_not_violated", 0) > 0
                                                              for r in rs if r.get("final")])),
            ("CORRECTNESS defects left", lambda rs: _num([(r.get("final") or {}).get("correctness_defects") for r in rs])),
            ("unnecessary blocking", lambda rs: _num([(r.get("final") or {}).get("unnecessary_blocking") for r in rs])),
            ("false positives", lambda rs: _num([(r.get("final") or {}).get("false_positives") for r in rs])),
            ("unnecessary code items", lambda rs: _num([(r.get("final") or {}).get("unnecessary_code") for r in rs])),
            ("key checks passed", lambda rs: _checks(rs)),
            ("hidden tests pass", lambda rs: _frac([all(h["returncode"] == 0 for h in r["metrics"]["hidden_tests"])
                                                    for r in rs if r["metrics"].get("hidden_tests")])),
            ("driver turns", lambda rs: _num([r["metrics"]["driver_turns"] for r in rs])),
            ("words the driver read", lambda rs: _num([r["metrics"]["words_read_by_driver"] for r in rs], "{:.0f}")),
            ("store artifacts (runs with any)", lambda rs: _frac([bool(r["metrics"]["store_files"]) for r in rs])),
            ("artifact files inside repos", lambda rs: _frac([bool(r["metrics"]["artifact_like_files_in_repos"]) for r in rs])),
            ("lines added", lambda rs: _num([r["metrics"]["lines_added"] for r in rs], "{:.0f}")),
            ("agent cost", lambda rs: _money([r["metrics"]["agent_cost_usd"] for r in rs])),
            ("agent turns", lambda rs: _num([r["metrics"]["agent_turns"] for r in rs], "{:.0f}")),
            ("agent wall time (s)", lambda rs: _num([r["metrics"]["agent_wall_seconds"] for r in rs], "{:.0f}")),
            ("cache-creation tokens", lambda rs: _num([r["metrics"]["tokens"]["cache_creation"] for r in rs], "{:.0f}")),
            ("output tokens", lambda rs: _num([r["metrics"]["tokens"]["output"] for r in rs], "{:.0f}")),
            ("subagents spawned", lambda rs: _num([len(r["metrics"]["subagents"]) for r in rs], "{:.1f}"))]

    summary = {}
    for case_id in sorted(by):
        arms = by[case_id]
        cols = [a for a in ("with", "baseline") if a in arms] + [a for a in arms if a not in ("with", "baseline")]
        out += ["", f"## {case_id}", "", "| metric | " + " | ".join(cols) + " |",
                "|---|" + "---|" * len(cols)]
        summary[case_id] = {}
        for label, fn in rows:
            vals = [fn(arms[a]) for a in cols]
            out.append(f"| {label} | " + " | ".join(vals) + " |")
            summary[case_id][label] = dict(zip(cols, vals))
        # which skill files actually load (addition a)
        if "with" in arms:
            cnt = Counter(f for r in arms["with"] for f in dict.fromkeys(r["metrics"]["skill_files_order"]))
            out += ["", f"Skill files read, with arm (runs that read each file, of {len(arms['with'])}): "
                    + (", ".join(f"`{f}` {c}" for f, c in cnt.most_common()) or "none")]
            for r in arms["with"]:
                out.append(f"- run {r['index']}: " + (" → ".join(r["metrics"]["skill_files_order"]) or "(skill not loaded)"))

    # cross-case file-read table
    withs = [r for r in runs_ok if r["arm"] == "with"]
    if withs:
        files = Counter(f for r in withs for f in dict.fromkeys(r["metrics"]["skill_files_order"]))
        out += ["", "## Skill files read across all cases (with arm)", "",
                f"{len(withs)} runs. A file read in 0 runs is not part of the skill in practice.", "",
                "| file | runs that read it |", "|---|---|"]
        for f, c in files.most_common():
            out.append(f"| `{f}` | {c}/{len(withs)} |")
    text = "\n".join(out) + "\n"
    with open(os.path.join(batch_dir, "summary.md"), "w") as f:
        f.write(text)
    with open(os.path.join(batch_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return text


def _caught(rs, proxy=False):
    vals = []
    for r in rs:
        facts = (r.get("final") or {}).get("facts")
        if proxy or not facts:
            auto = r["metrics"]["facts"]
            if not auto:
                continue
            vals.append(all(v["mention_before_first_edit"] for v in auto.values()) if proxy else None)
        else:
            vals.append(all(v["caught_before_code"] for v in facts.values()))
    return _frac(vals)


def _ratio(rs, a, b):
    num = sum((r.get("final") or {}).get(a, 0) for r in rs)
    den = sum((r.get("final") or {}).get(b, 0) for r in rs)
    return f"{num}/{den}" if den else "–"


def _checks(rs):
    p = sum(1 for r in rs for c in r["metrics"]["checks"] if c["result"] == "pass")
    t = sum(1 for r in rs for c in r["metrics"]["checks"] if c["result"] != "na")
    return f"{p}/{t}" if t else "–"
