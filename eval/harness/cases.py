"""Load and validate eval cases (visible or external held-out) in the documented format.

<cases-dir>/<case>/
  packet/                  the only part an agent run ever sees (via the built workspace)
    case.yaml              id, driver_prompt, workspace, connectors, limits
    overlay/               optional: files layered onto the base workspace
    connectors/*.json      optional: simulated sources, served by mockmcp.py
  key/                     driver-sim and scorer only; never copied into a run
    answer_key.yaml        hidden_conditions, facts, unknowns, must_do, must_not_do, checks
    driver_script.yaml     persona + replies for the simulated driver
    hidden_tests/          optional: tests copied into the workspace only after the run

See eval/README.md for every field.
"""
import os
import re

import yaml

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.dirname(HARNESS_DIR)
DEFAULT_BASE = os.path.join(EVAL_DIR, "workspace", "base")
DEFAULT_CASES = os.path.join(EVAL_DIR, "cases")

CHECK_TYPES = {"diff_present", "diff_absent", "no_new_files", "store_empty", "store_nonempty",
               "no_driver_turns", "text_absent", "text_present", "hidden_tests_pass",
               "skill_loaded"}


class CaseError(Exception):
    pass


class Case:
    def __init__(self, case_dir):
        self.dir = os.path.abspath(case_dir)
        self.packet_dir = os.path.join(self.dir, "packet")
        self.key_dir = os.path.join(self.dir, "key")
        self.packet = _yaml(os.path.join(self.packet_dir, "case.yaml"))
        self.key = _yaml(os.path.join(self.key_dir, "answer_key.yaml"))
        self.driver = _yaml(os.path.join(self.key_dir, "driver_script.yaml"))
        self.id = str(self.packet.get("id") or os.path.basename(self.dir))

    # packet accessors -------------------------------------------------------------
    @property
    def prompt(self):
        return self.packet["driver_prompt"].strip()

    @property
    def limits(self):
        lim = {"max_turns": 80, "max_budget_usd": 6.0, "max_driver_turns": 4,
               "timeout_minutes": 40, "disallowed_tools": []}
        lim.update(self.packet.get("limits") or {})
        return lim

    def base_dir(self):
        ws = self.packet.get("workspace") or {}
        base = ws.get("base", "default")
        if base == "default":
            return DEFAULT_BASE
        if base in (None, "none"):
            return None
        return os.path.join(self.packet_dir, base)

    def overlay_dir(self):
        ws = self.packet.get("workspace") or {}
        rel = ws.get("overlay", "overlay")
        path = os.path.join(self.packet_dir, rel)
        return path if os.path.isdir(path) else None

    def removals(self):
        return list((self.packet.get("workspace") or {}).get("remove") or [])

    def connectors_dir(self):
        rel = (self.packet.get("connectors") or {}).get("dir", "connectors")
        path = os.path.join(self.packet_dir, rel)
        if os.path.isdir(path) and any(f.endswith(".json") for f in os.listdir(path)):
            return path
        return None

    def hidden_tests_dir(self):
        path = os.path.join(self.key_dir, "hidden_tests")
        return path if os.path.isdir(path) else None


def _yaml(path):
    if not os.path.isfile(path):
        raise CaseError(f"missing {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise CaseError(f"{path}: expected a mapping at top level")
    return data


def validate(case_dir):
    """Return a list of problems (empty = valid). Never raises for content problems."""
    errs = []
    for sub in ("packet", "key"):
        if not os.path.isdir(os.path.join(case_dir, sub)):
            errs.append(f"missing {sub}/")
    if errs:
        return errs
    try:
        c = Case(case_dir)
    except (CaseError, yaml.YAMLError) as e:
        return [str(e)]
    p, k, d = c.packet, c.key, c.driver
    if not isinstance(p.get("driver_prompt"), str) or not p["driver_prompt"].strip():
        errs.append("case.yaml: driver_prompt must be a non-empty string")
    base = c.base_dir()
    if base is not None and not os.path.isdir(base):
        errs.append(f"case.yaml: workspace base not found: {base}")
    if base is None and c.overlay_dir() is None:
        errs.append("case.yaml: workspace has neither a base nor an overlay/")
    for name in os.listdir(c.packet_dir):
        if name in ("key", "answer_key.yaml", "driver_script.yaml"):
            errs.append(f"packet/ contains {name}: key material must stay in key/")
    cdir = c.connectors_dir()
    if cdir:
        import json
        for f in os.listdir(cdir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(cdir, f)) as fh:
                        data = json.load(fh)
                    if not isinstance(data.get("items", []), list):
                        errs.append(f"connectors/{f}: items must be a list")
                    if data.get("failure") not in (None, "timeout", "error"):
                        errs.append(f"connectors/{f}: failure must be null, timeout or error")
                except ValueError as e:
                    errs.append(f"connectors/{f}: invalid JSON ({e})")
    lim = p.get("limits") or {}
    if not isinstance(lim, dict):
        errs.append("case.yaml: limits must be a mapping")

    for field in ("hidden_conditions", "must_do", "must_not_do"):
        if not isinstance(k.get(field), list) or not k.get(field):
            errs.append(f"answer_key.yaml: {field} must be a non-empty list")
    ids = set()
    for field in ("must_do", "must_not_do"):
        for i, item in enumerate(k.get(field) or []):
            if not isinstance(item, dict) or not item.get("id") or not item.get("text"):
                errs.append(f"answer_key.yaml: {field}[{i}] needs id and text")
            elif item["id"] in ids:
                errs.append(f"answer_key.yaml: duplicate id {item['id']}")
            else:
                ids.add(item["id"])
    for i, fact in enumerate(k.get("facts") or []):
        if not fact.get("id") or not fact.get("mention_regex"):
            errs.append(f"answer_key.yaml: facts[{i}] needs id and mention_regex")
        else:
            errs += _regex_ok(fact["mention_regex"], f"facts[{i}].mention_regex")
    fact_ids = {f.get("id") for f in k.get("facts") or []}
    for i, u in enumerate(k.get("unknowns") or []):
        if not u.get("id"):
            errs.append(f"answer_key.yaml: unknowns[{i}] needs id")
        for fid in u.get("facts") or []:
            if fid not in fact_ids:
                errs.append(f"answer_key.yaml: unknowns[{i}] refers to unknown fact {fid}")
        for j, dc in enumerate(u.get("dependent_code") or []):
            if not dc.get("path") or not dc.get("pattern"):
                errs.append(f"answer_key.yaml: unknowns[{i}].dependent_code[{j}] needs path and pattern")
            else:
                errs += _regex_ok(dc["pattern"], f"unknowns[{i}].dependent_code[{j}]")
        if u.get("question_regex"):
            errs += _regex_ok(u["question_regex"], f"unknowns[{i}].question_regex")
    for i, chk in enumerate(k.get("checks") or []):
        if chk.get("type") not in CHECK_TYPES:
            errs.append(f"answer_key.yaml: checks[{i}].type must be one of {sorted(CHECK_TYPES)}")
        if chk.get("pattern"):
            errs += _regex_ok(chk["pattern"], f"checks[{i}].pattern")
        if not chk.get("id"):
            errs.append(f"answer_key.yaml: checks[{i}] needs id")
    o4 = k.get("option4")
    if o4 is not None:
        if not isinstance(o4, dict) or not (o4.get("affected_absent") or o4.get("unrelated_present")):
            errs.append("answer_key.yaml: option4 needs affected_absent and/or unrelated_present")
    if c.hidden_tests_dir() and not k.get("hidden_tests_cmd"):
        errs.append("answer_key.yaml: hidden_tests/ present but hidden_tests_cmd missing")

    mode = d.get("mode", "scripted")
    if mode not in ("scripted", "llm"):
        errs.append("driver_script.yaml: mode must be scripted or llm")
    if mode == "llm" and not d.get("persona"):
        errs.append("driver_script.yaml: llm mode needs a persona")
    for i, r in enumerate(d.get("rules") or []):
        if not r.get("match") or "reply" not in r:
            errs.append(f"driver_script.yaml: rules[{i}] needs match and reply")
        else:
            errs += _regex_ok(r["match"], f"driver rules[{i}].match")
        if r.get("option") not in (None, 1, 2, 3, 4):
            errs.append(f"driver_script.yaml: rules[{i}].option must be 1-4 or null")
    if mode == "scripted" and "default_reply" not in d:
        errs.append("driver_script.yaml: scripted mode needs default_reply")
    return errs


def _regex_ok(pattern, where):
    try:
        re.compile(pattern)
        return []
    except re.error as e:
        return [f"answer_key/driver: bad regex in {where}: {e}"]


def discover(cases_dir, only=None):
    """Return case directories under cases_dir (a folder of cases, or one case folder)."""
    cases_dir = os.path.abspath(cases_dir)
    if os.path.isdir(os.path.join(cases_dir, "packet")):
        dirs = [cases_dir]
    else:
        dirs = [os.path.join(cases_dir, n) for n in sorted(os.listdir(cases_dir))
                if os.path.isdir(os.path.join(cases_dir, n, "packet"))
                or os.path.isdir(os.path.join(cases_dir, n, "key"))]
    if only:
        want = set(only)
        dirs = [d for d in dirs if os.path.basename(d) in want]
    return dirs


def load_all(cases_dir, only=None):
    """Load valid cases; raise CaseError listing every invalid one."""
    out, problems = [], []
    for d in discover(cases_dir, only):
        errs = validate(d)
        if errs:
            problems.append(f"{os.path.basename(d)}:\n  - " + "\n  - ".join(errs))
        else:
            out.append(Case(d))
    if problems:
        raise CaseError("invalid cases:\n" + "\n".join(problems))
    if not out:
        raise CaseError(f"no cases found in {cases_dir}")
    return out
