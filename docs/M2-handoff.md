# M2 → M3 handoff

For the session that builds M3 (eval harness + visible cases). Sources of truth: the spec
(`groundwork-spec.md` v0.3), `docs/M0-build-plan.md` (§0, §0b, §2, §5), this file. Repo:
`/home/user/projects/groundwork` (symlinked from `~/projects/groundwork`); push only to
branch `build/groundwork` of `singhrishabh018/projects`; never `main`, no PRs.

## 1. On disk (skill = `skill/groundwork/`, lines)

`SKILL.md` 118 — triage line, always-material triggers, G1–G8, question shape (4 answer
paths), answer rule, full-mode router, pre-edit check, final report, store location.
Phases: `c1-triage` 36 · `c2-requirements` 34 · `c3-discovery` 41 · `c4-research` 26 ·
`c5-decisions` 41 · `c6-design-review` 32 · `c7-questions` 49 · `c8-plan` 44 · `c9-verify` 40 ·
`c11-handoff` 20 · `c14-connectors` 35.
Probes: `common` 30 · `deploy-topology` 22 · `external-api` 23.
Templates: `requirements` 32 · `decisions` 34 · `questions` 19 · `gate-record` 25 ·
`verification` 32 · `handoff` 20.
Also: `README.md` (install, Cursor hands-on check), `NOTES-deferred.md`, `docs/M0-build-plan.md`,
`docs/M1-self-check.md`, `docs/M2-check.md`. No `eval/` yet.

| Phase | Does |
|---|---|
| C1 | picks phases/conditional sections, creates the task folder in the store |
| C2 | requirements with provenance, contradictions (never silently resolved), material unknowns |
| C3 | task-scoped discovery (touched flow + one hop, all repos) as claims; proxies; reuse/golden examples |
| C4 | neutral questions + disconfirming search per working assumption |
| C5 | living decision record: statuses, proxy register, affected-work map, scan list |
| C6 | fresh-context completeness + implementability review, max 2 rounds |
| C7 | routes unknowns; drafts questions (4 answer paths, no-answer default); draft-only |
| C8 | slices with dependencies, reuse declaration, verification per requirement |
| C9 | fresh-context verification with proof of work; 1 round + 1 re-check; never "passed" |
| C11 | spec / background / prompt split with retrieval marker |
| C14 | connectors by role, read-only, provenance, failure → unknown + gate record |

## 2. Decisions made during M1–M2 that aren't in the spec or M0 plan

- **`rules/full.md` deleted.** It loaded in 1/5 full-mode runs and mostly duplicated phase
  files. Its unique parts moved: the answer rule and the final-report line → SKILL.md; the
  gate-default table → `templates/gate-record.md`; the claim status/source lists → C3.
- **Pre-edit check (one line, full mode, SKILL.md):** "Before your first file edit: name the
  open unknowns that affect this edit, and which part of the work they block. Edit only the
  parts they don't block." Reason: a heavy run built dead code (`on_batch()`) before asking
  the question it depended on. Don't expand this line.
- **Answer rule:** a user's answer to a material technical question is a statement; without
  matching evidence or a named source it becomes `accepted-assumption` with its consequence.
- **Question shape:** a recommendation (the option that's safe if wrong) is required;
  option 4 = hold the affected work and continue unrelated work, never "do it anyway".
- **Triage line** `Groundwork: <guard|full> — …` is the first text after the skill loads.
- **Description is directive** ("Load this BEFORE the first search, read or edit…"). It's a
  named proxy, see §3.
- **Size:** SKILL.md ≈ 2.27k tokens loaded, measured on `claude-opus-5` against an
  empty-body skill (≈ 2.03k before the merge). Accepted; don't trim working content to hit a budget.

## 3. Known issues / unresolved

1. **Phase files after C1 were never read in any M2 run** (0 reads in 7 runs: 3 mixed,
   2 heavy, 2 trivial). On the 2 heavy runs, full mode was triaged but the flow wasn't followed.
   The pre-edit check is the only change made for this; the eval must measure it.
2. **The description is a named proxy, assumed overfit.** It went 0/2 → 4/4 loads after a
   one-sentence change on two scratch tasks, one model. E2b tests both directions.
3. **The skill doesn't load on trivial tasks** (0/2 on `claude-opus-5`, 0/4 on
   `claude-sonnet-5`), so guard rules don't apply there.
4. Option 2 isn't always an exact step (2/3 in M2).
5. The pre-edit check and the merged SKILL.md are **untested**: no run has used them yet.

## 4. Harness facts (all tested here)

- **Arms.** With: put the skill at `<root>/.claude/skills/groundwork/` (copy
  `skill/groundwork/`) and pass `--add-dir <root>`. Baseline: no `--add-dir`. Confirm per run
  from the `system/init` event: `skills` contains `groundwork` only in the with arm.
- **Clean profile:** `CLAUDE_CONFIG_DIR=<fresh empty dir>` per run. Auth still works; user and
  synced skills disappear; built-in skills remain (record the `system/init` skills/tools/
  MCP/plugins in every result). Use the same dir for `--resume` turns of that run. Also
  record a listing of the ambient `~/.claude`.
- **Env to clear:** `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_REMOTE_SESSION_ID`,
  `CLAUDE_CODE_DEBUG` (otherwise children reuse this session's id / print debug to stderr).
  **Set:** `GROUNDWORK_HOME=<fresh dir per run>`.
- **`--bare` doesn't work** (needs `ANTHROPIC_API_KEY`; direct API host blocked).
- **Permissions:** `--dangerously-skip-permissions` is refused as root. Use
  `--permission-mode acceptEdits --allowedTools "Bash,Read,Edit,Write,Glob,Grep,Skill,Agent"`.
  Pass `stdin=/dev/null`.
- **Command:** `claude -p "<msg>" --model claude-opus-5 --output-format stream-json --verbose
  --max-turns 60 --max-budget-usd 6 [--add-dir <root>] [--resume <session_id>]`. Parse
  `result` events for `total_cost_usd`, `num_turns`, `usage`, `session_id`.
- **Driver loop:** after each agent turn, if the result asks a question, the driver-sim replies
  and the harness `--resume`s (max 4 driver turns). `--max-budget-usd` applies per invocation,
  so also cap the run total.
- **Warm cache:** cold-cache runs cost 3–4× more on the same task. Do a warm-up run before
  measuring, or report cache-creation and cache-read tokens separately.
- **Containment:** agents sometimes run `find /`. Keep `key/` and any held-out folder outside
  the run's reach where possible, and audit every tool call; any access to `key/` or the
  held-out path discards the run.
- **Models:** `claude-opus-5` for both arms (resolves here; distinct from `claude-opus-5-5`).
  Generalization check: E1 on one other model, 2 runs per arm.
- **Measured costs, `claude-opus-5`, warm cache:**

| Task | Cost per run |
|---|---|
| Trivial | $0.13–0.36 |
| Mixed (2 invocations) | $0.90–1.17 |
| Heavy (2–3 invocations) | $1.70 and $4.48 |

  Estimate for the full set: $90–250. Smoke test first (1 case × 1 run per arm) and report
  measured cost before any batch; if expensive, go to n=2, never drop cases.

## 5. Eval design already locked

- **Cases:** E1–E8 (spec §12.2), **E2b** (looks trivial, touches a cross-repo field or contract;
  measures whether the skill loads at all, and loading on genuinely trivial work via E2),
  **E9** (yes-to-everything driver: approves every suggestion, gives confident unverified
  technical answers; pass only if consequential issues are still caught, held, or flagged).
  Details: `docs/M0-build-plan.md` §5.2.
- **Workspace:** fictional, 4 tiny Python repos (`stock-sync`, `price-sync`, `deploy-config`,
  `warehouse-sql`) + per-case overlay. No real names (O8). Must not reuse skill examples.
- **Case format** (visible and held-out): `<case>/packet/` (`case.yaml`: id, driver_prompt,
  workspace base+overlay, connectors + failure modes, limits; `overlay/`; `connectors/*.json`) —
  the only thing the agent can see; `<case>/key/` (`answer_key.yaml`: hidden_conditions,
  must_do, must_not_do, scoring; `driver_script.yaml`) — driver-sim and scorer only; the
  driver never sees must_do. `--cases-dir <path>` loads any folder in this shape; the
  loader never copies `key/`. Don't look for or imitate the held-out cases.
- **Connectors:** a stdlib-only stdio MCP server serving `connectors/` fixtures, with a
  timeout mode (E4). Same server in both arms.
- **n = 3 per arm per case** (10 cases → 60 agent runs).
- **Scoring:** automatic where possible. Judge = separate `claude -p --json-schema` run that
  sees the answer key + transcript + diff, never the agent context.
  - "Caught before code" is a **named proxy** (first edit after first mention of the fact);
    it counts only if the judge also confirms the design/code accounts for the fact.
  - **Option-4 pass/fail** is computed for every run where option 4 is offered and picked.
  - Also record: triage line before first edit, phase files read, pre-edit check present.
  - §12.4 metrics: human effort = driver turns, questions and words read.
- **Report:** raw per-run JSON + per-case with/without tables. No single aggregate score.
