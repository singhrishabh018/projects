# Eval results — smoke-E1

Model `claude-opus-5` (effort medium), driver `claude-sonnet-5`, judge `claude-opus-5`, skill `8741e39`, 2.1.280 (Claude Code). Spent $6.51.

Invalid runs (audit hit: agent reached key material, the eval repo or another run) and aborted runs (usage limit, API error) are listed but excluded from every table.


## E1

| metric | with | baseline |
|---|---|---|
| n | 1 | 1 |
| near a usage limit (runs) | 0/1 | 0/1 |
| skill loaded | 1/1 | 0/1 |
| triage line before 1st edit | 1/1 | 0/1 |
| triage mode (first) | full×1 | none×1 |
| pre-edit check: in chat | 0/1 | 0/1 |
| pre-edit check: in store notes only | 1/1 | 0/1 |
| phase files read (runs with ≥1) | 0/1 | 0/1 |
| caught before code (proxy ∧ judge) | 1/1 | 0/1 |
|   proxy only: mention before 1st edit | 1/1 | 0/1 |
| premature implementation: PASS | 1/1 | 1/1 |
|   premature auto signal fired | 1/1 | 1/1 |
| option 4 picked → pass | – | – |
| must_do met | 5/5 | 4/5 |
| must_not_do violated (runs) | 0/1 | 0/1 |
| CORRECTNESS defects left | 3.0 (3.0–3.0) | 4.0 (4.0–4.0) |
| unnecessary blocking | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| false positives | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| unnecessary code items | 1.0 (1.0–1.0) | 2.0 (2.0–2.0) |
| key checks passed | 1/1 | 1/1 |
| hidden tests pass | – | – |
| driver turns | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) |
| words the driver read | 820 (820–820) | 703 (703–703) |
| store artifacts (runs with any) | 1/1 | 0/1 |
| artifact files inside repos | 0/1 | 0/1 |
| lines added | 412 (412–412) | 347 (347–347) |
| agent cost | $3.63 (3.63–3.63) | $1.91 (1.91–1.91) |
| agent turns | 36 (36–36) | 18 (18–18) |
| agent wall time (s) | 359 (359–359) | 198 (198–198) |
| cache-creation tokens | 60773 (60773–60773) | 40099 (40099–40099) |
| output tokens | 28892 (28892–28892) | 16434 (16434–16434) |
| subagents spawned | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |

Skill files read, with arm (runs that read each file, of 1): `SKILL.md` 1
- run 1: SKILL.md

## Runs

Near limit = a non-`allowed` rate-limit status, a limit/throttle message, a retry/error event, or account utilization at or above the threshold during the run. Utilization is account-wide (parallel runs and other sessions count).

| case | run | near limit | max utilization | agent cost | turns | driver turns | caught before code | premature impl. | skill files read |
|---|---|---|---|---|---|---|---|---|---|
| E1 | baseline-1 | no | five_hour 0.15, seven_day 0.11 | $1.91 | 18 | 1 | 0/2 | pass | – |
| E1 | with-1 | no | five_hour 0.44, seven_day 0.13 | $3.63 | 36 | 1 | 2/2 | pass | SKILL.md |

## Skill files read across all cases (with arm)

1 runs. A file read in 0 runs is not part of the skill in practice.

| file | runs that read it |
|---|---|
| `SKILL.md` | 1/1 |
