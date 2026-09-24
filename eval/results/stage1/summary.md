# Eval results — stage1

Model `claude-opus-5` (effort medium), driver `claude-sonnet-5`, judge `claude-opus-5`, skill `77c36aa`, 2.1.280 (Claude Code). Spent $17.52.

Invalid runs (audit hit: agent reached key material, the eval repo or another run) and aborted runs (usage limit, API error) are listed but excluded from every table.


## E2b

| metric | with | baseline |
|---|---|---|
| **cost multiple (with ÷ baseline)** | **2.4×** |  |
| n | 2 | 2 |
| near a usage limit (runs) | 0/2 | 1/2 |
| skill loaded | 2/2 | 0/2 |
| triage line before 1st edit | 2/2 | 0/2 |
| triage mode (first) | full×2 | none×2 |
| pre-edit check: in chat | 1/1 | – |
| pre-edit check: in store notes only | 0/1 | – |
| phase files read (runs with ≥1) | 0/2 | 0/2 |
| caught before code (proxy ∧ judge) | 2/2 | 2/2 |
|   proxy only: mention before 1st edit | 2/2 | 2/2 |
| premature implementation: PASS | 2/2 | 2/2 |
|   premature auto signal fired | 0/2 | 0/2 |
| option 4 picked → pass | 2/2 | 1/1 |
| must_do met | 8/8 | 8/8 |
| must_not_do violated (runs) | 0/2 | 0/2 |
| CORRECTNESS defects left | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| unnecessary blocking | 0.5 (0.0–1.0) | 0.0 (0.0–0.0) |
| false positives | 0.0 (0.0–0.0) | 0.5 (0.0–1.0) |
| unnecessary code items | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| key checks passed | 6/6 | 4/4 |
| hidden tests pass | 2/2 | 2/2 |
| driver turns | 1.0 (1.0–1.0) | 0.5 (0.0–1.0) |
| words the driver read | 615 (587–643) | 294 (268–320) |
| store artifacts (runs with any) | 0/2 | 0/2 |
| artifact files inside repos | 0/2 | 0/2 |
| lines added | 3 (0–6) | 0 (0–0) |
| agent cost | $0.69 (0.66–0.72) | $0.29 (0.20–0.38) |
| agent turns | 20 (19–21) | 10 (9–11) |
| agent wall time (s) | 62 (61–64) | 32 (31–32) |
| cache-creation tokens | 17868 (16512–19223) | 10496 (10279–10713) |
| output tokens | 4552 (4390–4715) | 2158 (2063–2252) |
| subagents spawned | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |

Skill files read, with arm (runs that read each file, of 2): `SKILL.md` 2
- run 1: SKILL.md
- run 2: SKILL.md

## E6

| metric | with | baseline |
|---|---|---|
| **cost multiple (with ÷ baseline)** | **1.8×** |  |
| n | 2 | 2 |
| near a usage limit (runs) | 1/2 | 1/2 |
| skill loaded | 2/2 | 0/2 |
| triage line before 1st edit | 2/2 | 0/2 |
| triage mode (first) | full×2 | none×2 |
| pre-edit check: in chat | 1/2 | 0/2 |
| pre-edit check: in store notes only | 0/2 | 0/2 |
| phase files read (runs with ≥1) | 0/2 | 0/2 |
| caught before code (proxy ∧ judge) | 1/2 | 2/2 |
|   proxy only: mention before 1st edit | 1/2 | 2/2 |
| premature implementation: PASS | 2/2 | 2/2 |
|   premature auto signal fired | 1/2 | 0/2 |
| option 4 picked → pass | – | – |
| must_do met | 8/8 | 8/8 |
| must_not_do violated (runs) | 0/2 | 0/2 |
| CORRECTNESS defects left | 2.0 (2.0–2.0) | 2.0 (2.0–2.0) |
| unnecessary blocking | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| false positives | 0.0 (0.0–0.0) | 0.5 (0.0–1.0) |
| unnecessary code items | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| key checks passed | 4/4 | 4/4 |
| hidden tests pass | – | – |
| driver turns | 0.5 (0.0–1.0) | 0.0 (0.0–0.0) |
| words the driver read | 614 (395–834) | 311 (277–345) |
| store artifacts (runs with any) | 0/2 | 0/2 |
| artifact files inside repos | 0/2 | 0/2 |
| lines added | 46 (45–47) | 48 (45–51) |
| agent cost | $0.96 (0.62–1.30) | $0.54 (0.53–0.54) |
| agent turns | 20 (19–20) | 26 (19–34) |
| agent wall time (s) | 105 (96–113) | 80 (75–85) |
| cache-creation tokens | 26424 (26239–26608) | 19168 (18945–19390) |
| output tokens | 8064 (7921–8207) | 6286 (5761–6810) |
| subagents spawned | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |

Skill files read, with arm (runs that read each file, of 2): `SKILL.md` 2
- run 1: SKILL.md
- run 2: SKILL.md

## E7

| metric | with | baseline |
|---|---|---|
| **cost multiple (with ÷ baseline)** | **5.2×** |  |
| n | 2 | 2 |
| near a usage limit (runs) | 1/2 | 1/2 |
| skill loaded | 2/2 | 0/2 |
| triage line before 1st edit | 2/2 | 0/2 |
| triage mode (first) | full×2 | none×2 |
| pre-edit check: in chat | 1/2 | 0/2 |
| pre-edit check: in store notes only | 0/2 | 0/2 |
| phase files read (runs with ≥1) | 0/2 | 0/2 |
| caught before code (proxy ∧ judge) | 2/2 | 1/2 |
|   proxy only: mention before 1st edit | 2/2 | 1/2 |
| premature implementation: PASS | 2/2 | 2/2 |
|   premature auto signal fired | 0/2 | 0/2 |
| option 4 picked → pass | – | – |
| must_do met | 10/10 | 9/10 |
| must_not_do violated (runs) | 0/2 | 0/2 |
| CORRECTNESS defects left | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| unnecessary blocking | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| false positives | 0.5 (0.0–1.0) | 0.0 (0.0–0.0) |
| unnecessary code items | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| key checks passed | 4/4 | 4/4 |
| hidden tests pass | 2/2 | 2/2 |
| driver turns | 1.5 (1.0–2.0) | 0.0 (0.0–0.0) |
| words the driver read | 687 (656–718) | 162 (131–193) |
| store artifacts (runs with any) | 1/2 | 0/2 |
| artifact files inside repos | 0/2 | 0/2 |
| lines added | 19 (17–21) | 18 (17–18) |
| agent cost | $1.21 (0.86–1.56) | $0.23 (0.22–0.24) |
| agent turns | 24 (23–25) | 10 (8–13) |
| agent wall time (s) | 93 (81–105) | 32 (29–34) |
| cache-creation tokens | 20592 (19276–21907) | 11136 (11108–11165) |
| output tokens | 6866 (5818–7915) | 2308 (2013–2604) |
| subagents spawned | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |

Skill files read, with arm (runs that read each file, of 2): `SKILL.md` 2
- run 1: SKILL.md
- run 2: SKILL.md

## E9

| metric | with | baseline |
|---|---|---|
| **cost multiple (with ÷ baseline)** | **3.1×** |  |
| n | 2 | 2 |
| near a usage limit (runs) | 1/2 | 1/2 |
| skill loaded | 2/2 | 0/2 |
| triage line before 1st edit | 2/2 | 0/2 |
| triage mode (first) | full×2 | none×2 |
| pre-edit check: in chat | 1/2 | 0/2 |
| pre-edit check: in store notes only | 0/2 | 0/2 |
| phase files read (runs with ≥1) | 0/2 | 0/2 |
| caught before code (proxy ∧ judge) | 2/2 | 0/2 |
|   proxy only: mention before 1st edit | 2/2 | 0/2 |
| premature implementation: PASS | 2/2 | 2/2 |
|   premature auto signal fired | 2/2 | 2/2 |
| option 4 picked → pass | – | – |
| must_do met | 9/9 | 6/6 |
| must_not_do violated (runs) | 0/2 | 0/2 |
| CORRECTNESS defects left | 4.0 (4.0–4.0) | 3.5 (3.0–4.0) |
| unnecessary blocking | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| false positives | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |
| unnecessary code items | 1.0 (1.0–1.0) | 1.0 (0.0–2.0) |
| key checks passed | – | – |
| hidden tests pass | – | – |
| driver turns | 1.0 (1.0–1.0) | 0.0 (0.0–0.0) |
| words the driver read | 798 (715–882) | 328 (324–333) |
| store artifacts (runs with any) | 0/2 | 0/2 |
| artifact files inside repos | 0/2 | 0/2 |
| lines added | 144 (128–160) | 130 (108–152) |
| agent cost | $1.46 (1.40–1.53) | $0.47 (0.46–0.47) |
| agent turns | 24 (18–30) | 17 (16–18) |
| agent wall time (s) | 160 (157–164) | 89 (88–90) |
| cache-creation tokens | 30929 (26994–34864) | 17366 (16746–17986) |
| output tokens | 12360 (12267–12452) | 6858 (6814–6901) |
| subagents spawned | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) |

Skill files read, with arm (runs that read each file, of 2): `SKILL.md` 2
- run 1: SKILL.md
- run 2: SKILL.md

## Runs

Near limit = a non-`allowed` rate-limit status, a limit/throttle message, a retry/error event, or account utilization at or above the threshold during the run. Utilization is account-wide (parallel runs and other sessions count).

| case | run | near limit | max utilization | agent cost | turns | driver turns | caught before code | premature impl. | skill files read |
|---|---|---|---|---|---|---|---|---|---|
| E2b | baseline-1 | no | five_hour 0.60, seven_day 0.14 | $0.38 | 9 | 1 | 2/2 | pass | – |
| E2b | baseline-2 | **yes** | five_hour 0.80, seven_day 0.16 | $0.20 | 11 | 0 | 2/2 | pass | – |
| E2b | with-1 | no | five_hour 0.61, seven_day 0.14 | $0.72 | 21 | 1 | 2/2 | pass | SKILL.md |
| E2b | with-2 | no | five_hour 0.77, seven_day 0.16 | $0.66 | 19 | 1 | 2/2 | pass | SKILL.md |
| E6 | baseline-1 | no | five_hour 0.67, seven_day 0.15 | $0.54 | 19 | 0 | 2/2 | pass | – |
| E6 | baseline-2 | **yes** | five_hour 0.88, seven_day 0.17 | $0.53 | 34 | 0 | 2/2 | pass | – |
| E6 | with-1 | no | five_hour 0.63, seven_day 0.15 | $0.62 | 20 | 0 | 1/2 | pass | SKILL.md |
| E6 | with-2 | **yes** | five_hour 0.89, seven_day 0.17 | $1.30 | 19 | 1 | 2/2 | pass | SKILL.md |
| E7 | baseline-1 | no | five_hour 0.70, seven_day 0.15 | $0.24 | 13 | 0 | 1/2 | pass | – |
| E7 | baseline-2 | **yes** (allowed_warning) | five_hour 0.93, seven_day 0.17 | $0.22 | 8 | 0 | 2/2 | pass | – |
| E7 | with-1 | no | five_hour 0.70, seven_day 0.15 | $0.86 | 23 | 1 | 2/2 | pass | SKILL.md |
| E7 | with-2 | **yes** (allowed_warning) | five_hour 0.90, seven_day 0.17 | $1.56 | 25 | 2 | 2/2 | pass | SKILL.md |
| E9 | baseline-1 | no | five_hour 0.78, seven_day 0.16 | $0.46 | 16 | 0 | 1/2 | pass | – |
| E9 | baseline-2 | **yes** (allowed_warning) | five_hour 0.99, seven_day 0.18 | $0.47 | 18 | 0 | 1/2 | pass | – |
| E9 | with-1 | **yes** | five_hour 0.80, seven_day 0.16 | $1.40 | 18 | 1 | 2/2 | pass | SKILL.md |
| E9 | with-2 | no | five_hour 0.36, seven_day 0.21 | $1.53 | 30 | 1 | 2/2 | pass | SKILL.md |

## Proxy fix (2026-09-24): caught-before-code, old vs new

The automatic "mentioned before the first edit" check originally scanned only chat text and store notes, and treated the first edit's own index as "not before". It missed facts the agent stated only inside the first edit's own code/docstring. Fixed to scan that content too and treat the first edit's own index as "at or before". These runs were rescored from the saved transcript — no new agent or judge calls.

| case | run | fact | old: mentioned before edit | new: mentioned before edit | judge: design accounts for it | old: caught before code | new: caught before code |
|---|---|---|---|---|---|---|---|
| E6 | with-1 | F1 | False | False | True | False | False |
| E6 | with-1 | F2 | False | True | True | False | True |
| E7 | baseline-1 | F1 | False | True | True | False | True |
| E7 | baseline-1 | F2 | False | False | True | False | False |
| E7 | baseline-2 | F1 | False | True | True | False | True |
| E7 | baseline-2 | F2 | False | True | True | False | True |
| E7 | with-1 | F1 | False | True | True | False | True |
| E7 | with-1 | F2 | True | True | True | True | True |
| E9 | with-1 | F1 | False | True | True | False | True |
| E9 | with-1 | F2 | True | True | True | True | True |

Across 5 rescored runs: **2/10 → 8/10** facts now counted as caught before code.

## Skill files read across all cases (with arm)

8 runs. A file read in 0 runs is not part of the skill in practice.

| file | runs that read it |
|---|---|
| `SKILL.md` | 8/8 |
