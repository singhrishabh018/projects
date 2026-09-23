# Groundwork eval harness

Runs each case **with** and **without** the Groundwork skill on the same model, records the
spec §12.4 metrics plus which skill files were actually read, and scores each run
automatically where possible and with a separate judge run where judgment is needed.

Python 3.10+ and PyYAML. No other dependencies. Needs the `claude` CLI (Claude Code) logged in.

```
eval/
  harness/
    gw_eval.py      CLI: validate | run | rescore | report
    cases.py        case loader + format validator (visible and external cases)
    workspace.py    builds a fresh git-initialised workspace per run; collects diffs
    claude_cli.py   headless `claude -p` with a clean profile; captures stream-json
    mockmcp.py      stdlib stdio MCP server serving a case's connectors/*.json (with failure modes)
    driver.py       simulated driver (scripted rules, or an LLM persona); never sees must_do
    metrics.py      automatic metrics from transcript + diff + store + answer key
    score.py        judge: separate no-tools `claude -p` that sees the key, never the agent context
    report.py       per-case with/without tables, file-read table; no aggregate score
    selftest.py     offline end-to-end test with a stub `claude` and a dummy external case folder
  workspace/base/   synthetic 4-repo workspace (stock-sync, price-sync, deploy-config, warehouse-sql)
  cases/E1..E9, E2b visible cases (packet/ + key/)
  results/<batch>/  run.json per run, gzipped transcripts and timeline, diff.patch, summary.md
```

## Quick start

```bash
cd eval/harness
python3 selftest.py                       # offline, free: checks the whole pipeline (19 checks)
python3 gw_eval.py validate               # visible cases
python3 gw_eval.py validate --cases-dir /path/to/heldout   # external cases: format check only

# smoke test: heavy case, 1 run per arm; read the cost before running anything bigger
python3 gw_eval.py run --case E1 --n 1 --jobs 2 --warmup --batch smoke-E1

# full visible set, n=3 per arm (see "Cost" first)
python3 gw_eval.py run --n 3 --jobs 4 --warmup --batch visible-n3 --max-total-usd 150

# held-out cases, same protocol
python3 gw_eval.py run --cases-dir /path/to/heldout --n 3 --jobs 4 --batch heldout-n3

# generalization check: E1 on one other model, 2 runs per arm
python3 gw_eval.py run --case E1 --n 2 --model claude-sonnet-5 --batch E1-sonnet5

python3 gw_eval.py report results/<batch>      # rebuild summary.md
python3 gw_eval.py rescore results/<batch>     # re-run only the judge (e.g. after a key fix)
```

Useful `run` options: `--arm with|baseline|both`, `--case ID` (repeatable), `--model`
(default `claude-opus-5`, both arms), `--effort` (default `medium`), `--driver-model`
(default `claude-sonnet-5`, used only by LLM-mode drivers), `--judge-model` (default
`claude-opus-5`), `--max-run-usd` (default 6), `--max-total-usd` (default 150; the batch stops
scheduling new runs once reached), `--jobs`, `--keep-runs` (keep workspaces for debugging),
`--no-judge`, `--runs-root` (default `/tmp/gw-eval-runs`, or `$GW_EVAL_RUNS`).

## What a run is

1. A fresh copy of the workspace (base + the case's overlay), each top-level folder its own git
   repo with one `initial` commit, in an opaquely named folder under the runs root (no case
   id or arm in any path the agent can see).
2. A fresh empty `CLAUDE_CONFIG_DIR` (clean profile) and a fresh `GROUNDWORK_HOME`, for both
   arms. Parent-session variables that leak into children are removed (`claude_cli.STRIP_ENV`).
3. Arms: **with** = the skill copied to `<run>/skill/.claude/skills/groundwork/` and passed with
   `--add-dir`; **baseline** = nothing added. Everything else is identical, including the
   connector server when the case has one. Each run records the `system/init` inventory
   (tools, skills, MCP servers, plugins) so the baseline's built-in skills are on record.
4. Tools: `--tools Bash,Read,Edit,Write,Glob,Grep,Skill,Agent` (host extras such as
   publishing, notifications and scheduling are removed), `--permission-mode acceptEdits`,
   stdin closed. A case can disallow tools (E4 disallows `Agent`).
5. Driver loop: after each agent turn, if the final message waits for the user, the driver
   replies and the harness `--resume`s, up to the case's `max_driver_turns`.
6. After the run: per-repo diff against `initial` (untracked files included), store listing,
   then the key's hidden tests are copied in and run (never visible during the run).
7. Audit: every tool call and tool result is scanned for the cases folder, the eval repo,
   `answer_key`, `driver_script`, `/key/` and other runs' folders. **Any hit invalidates the
   run**; invalid runs are listed in the report and excluded from every table. Broad
   `find /`-style searches are recorded.
8. Judge (unless `--no-judge`).

## Metrics

Automatic (`metrics.py`), per run:

| Metric | How |
|---|---|
| Skill loaded | `Skill` tool call for `groundwork` |
| **Skill files read, in order** | `Skill` (SKILL.md), `Read` of any file under the skill folder, file paths in `Bash` commands, `Glob`/`Grep` in the skill folder (as "listing"); main agent and subagents |
| Triage line | first `Groundwork: <mode>` line; whether it came before the first code edit |
| Pre-edit check (signal) | text between skill load and first edit mentioning unknowns and what they block/affect |
| First code edit | first `Edit`/`Write`/`NotebookEdit` in the workspace, or a `Bash` command that writes |
| Fact mentioned before first edit | per planted fact, regex over the agent's text and its store notes — **named proxy**, see below |
| **Premature implementation (signal)** | an edit to code the key lists as depending on an open unknown, made before the related fact was mentioned, or in a turn that then ends by asking about it (the `on_batch()` pattern) |
| Option 4 | when the driver picks "none of these": affected work absent from the diff, unrelated work present — pass/fail |
| Key checks | per-case mechanical checks (diff patterns, store empty, no driver turns, hidden tests…) |
| Human effort | driver turns, questions put to the driver, words the driver had to read |
| Cost, tokens, time | per invocation, summed: cost, turns, input/output/cache-creation/cache-read tokens, wall time |
| Other | store artifacts; planning files written inside repos; files/lines changed; tests run; subagents |

Judge (`score.py`, a separate no-tools run with the answer key, a numbered condensed
timeline, the diff and the store notes; the SKILL.md body is replaced by a placeholder):
must_do / must_not_do per item, per fact whether it was recognised before the first code
edit and whether the design **actually accounts for it**, premature implementation
pass/fail, CORRECTNESS defects left, unnecessary blocking, false positives, unnecessary code,
how the agent treated the user's answers.

Final per-run results (`combine()` in `gw_eval.py`):
- **Caught before code** = mention before the first edit (automatic proxy) **and** the judge
  confirms the design accounts for the fact. The proxy alone is also reported, so the gap
  between "mentioned" and "acted on" is visible.
- **Premature implementation** = the judge's pass/fail; the automatic signal is reported next to it.

Report (`summary.md`): one table per case, columns with/baseline, n and spread; a list of
skill files read per run; a cross-case table of how many with-arm runs read each skill file.
There is deliberately no aggregate score across cases.

Known limits of the scoring:
- The judge can usually tell which arm it is scoring (triage lines, store notes). It is not blind.
- Regexes for fact mentions and bash writes are heuristics. They are signals; the judge
  confirms. Tune a case's regex in its key, then `rescore`.
- Question detection for the driver loop is a heuristic (`driver.asks_question`).
- Human minutes can't be measured in simulation; driver turns and words read are the proxies.
- The visible cases were written by the skill's author and share themes with the probe
  files (§13: "probes needed by the evaluation cases"). Held-out cases are the real test.

## Case format (visible and external held-out cases)

```
<cases-dir>/<case>/
  packet/                     the only part the agent ever sees (through the built workspace)
    case.yaml
    overlay/                  optional: files layered onto the base workspace
    connectors/*.json         optional: simulated sources
  key/                        driver-sim and judge only; never copied into a run
    answer_key.yaml
    driver_script.yaml
    hidden_tests/             optional: copied into the workspace after the run, then executed
```

`--cases-dir` accepts a folder of cases or a single case folder. `validate` checks the shape,
the regexes and the connector JSON, builds each workspace in a temp dir, confirms no key
material lands in it, and round-trips the connector server. Nothing is run against a model.

### `packet/case.yaml`

```yaml
id: X1                          # defaults to the folder name
driver_prompt: |                # what the user types
  ...
workspace:
  base: default                 # default = eval/workspace/base; none = overlay only;
                                # or a path relative to packet/ (your own full workspace)
  overlay: overlay              # optional, relative to packet/
  remove: [path, ...]           # optional, workspace-relative paths to delete after overlay
connectors:
  dir: connectors               # optional
limits:                         # all optional
  max_driver_turns: 4
  max_turns: 80                 # agent turns per invocation
  max_budget_usd: 6.0           # per run (all invocations)
  timeout_minutes: 40           # per invocation
  disallowed_tools: [Agent]
```

Each top-level folder of the built workspace becomes a git repo.

### `packet/connectors/<role>.json`

```json
{"role": "tickets", "description": "team ticket tracker",
 "failure": null,                // null | "timeout" | "error"
 "delay_seconds": 2,             // for "timeout"
 "items": [{"id": "142", "title": "...", "body": "...", "author": "...",
            "updated": "2026-09-19", "url": "tracker://142", "comments": []}]}
```

Served as MCP tools `<role>_search(query)` and `<role>_get(id)` (visible to the agent as
`mcp__sources__<role>_get`). `timeout` answers every call with a timeout error.

### `key/answer_key.yaml`

```yaml
hidden_conditions: [text, ...]          # required; what's planted
facts:                                   # planted facts to catch before code
  - id: F1
    description: text
    mention_regex: 'regex'               # automatic "mentioned" signal (case-insensitive)
unknowns:                                # open questions; work that depends on them
  - id: U1
    description: text
    facts: [F1]                          # facts whose discovery the dependent work needs
    dependent_code:
      - {path: 'repo/pkg/*.py', pattern: 'regex on the edit content'}
    question_regex: 'regex'              # a question about this unknown
must_do:     [{id: D1, text: ...}, ...]  # required
must_not_do: [{id: N1, text: ...}, ...]  # required
option4:                                 # checked when the driver picks "none of these"
  affected_absent:   [{path: glob, pattern: regex}]            # added lines must not match
  unrelated_present: [{path: glob, pattern: regex, removed: false}]  # added (or removed) lines must match
checks:                                  # mechanical, per run
  - {id: C1, type: diff_present, path: glob, pattern: regex, arm: both, desc: text}
  # types: diff_present, diff_absent (added lines), no_new_files (path glob), store_empty,
  #        store_nonempty, no_driver_turns, text_present / text_absent (where: final|all),
  #        hidden_tests_pass, skill_loaded.  arm: with | baseline | both
hidden_tests_cmd: [{repo: name, cmd: 'python3 -m unittest tests.test_x'}]
judge_notes: text                        # optional guidance for the judge
```

Diff paths are workspace-relative (`<repo>/<file>`); globs use `fnmatch` (`*` matches `/`).

### `key/driver_script.yaml`

```yaml
mode: scripted                  # or llm
persona: text                   # required for llm
rules:                          # scripted: first match wins; llm: guidance
  - {match: 'regex on the agent message', reply: text, option: 4, max_uses: 1}
default_reply: text             # scripted: when the agent asks and no rule matches
default_option: 1
```

The driver replies only when the agent's final message waits for input; otherwise the run
ends. `option` records which answer path the reply takes (1 know, 2 checked, 3 will ask,
4 none of these) so option-4 runs are checked mechanically. The driver sees this file and the
agent's messages, never `answer_key.yaml`.

## Visible cases

| # | Task (driver prompt, short) | Planted | Driver |
|---|---|---|---|
| E1 | batch stock updates per partner ticket | 8 prod replicas (base says 1), per-pod buffers, low overnight volume vs 15-min freshness; offsets | scripted; knows the 15 min, not the topology |
| E2 | fix a log typo | nothing | scripted |
| E2b | rename payload `qty` → `quantity` | partner contract field, silent drop; warehouse reader in another repo | scripted, picks option 4 |
| E3 | implement ticket 142 | title + PM comment say price, cloned description says stock; independent token-in-log fix | scripted, picks option 4 |
| E4 | implement ticket 157 (timeout config) | tracker times out; subagents disabled | scripted; tracker down for them too |
| E5 | add `location`; reviewer worries about dedup | dedup keyed on event id: concern contradicted | scripted |
| E6 | only send brands sold on the website | `is_searchable` look-alike; real rule `web_eligible AND active` in warehouse-sql | scripted |
| E7 | send the restock date | partner field `restock_eta` (YYYY-MM-DD), silent drop, always 202 | scripted |
| E8 | partner location-reset call | existing `PartnerClient._request` with retries | scripted |
| E9 | admin endpoint to reload eligible brands | 4 replicas behind a Service; export only nightly | **LLM "yes to everything"** persona with confident wrong answers |

## Cost

Measured costs are in `docs/M3-harness.md`. Every run is capped (`--max-run-usd`), and a batch
stops scheduling new runs at `--max-total-usd`. Cold caches cost 3–4× more on the same task
(M1); `--warmup` makes one cheap call per arm first, and cache-creation vs cache-read tokens are
recorded per run so cost comparisons can account for it.

## Optional scoring layers

None are built. A third-party scoring layer may only ever be added behind an env flag, as an
extra column, never as a dependency and never deciding pass/fail (see `NOTES-deferred.md`).
