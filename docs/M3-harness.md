# M3: eval harness and E1 smoke test (2026-09-23)

What was built, what was verified, and the one measured data point so far. **No batch has
been run.** How to run everything: `eval/README.md`.

## 1. Built

- `eval/harness/`: case loader and validator (visible and external `--cases-dir`), workspace
  builder, headless runner with a clean profile per run, mock MCP connector server with
  failure modes, driver-sim (scripted or LLM persona), automatic metrics, containment audit,
  separate judge run, per-case report, resumable batches, offline self-test.
- `eval/workspace/base/`: fictional 4-repo system (`stock-sync`, `price-sync`, `deploy-config`,
  `warehouse-sql`). Checked against the skill files: no skill example is reused. The probes
  cover the same themes in general terms (deploy topology, silent partner failures), as §13
  intends, so the visible cases don't test instruction wording independently. The held-out
  cases do.
- `eval/cases/`: E1–E8, E2b, E9. Each has a packet, an answer key and a driver script. Five
  have hidden tests (E2b, E3, E5, E7, E8).

## 2. Verified (and how)

| Claim | How |
|---|---|
| Loader accepts the documented format from an external folder and rejects malformed cases with specific reasons (addition d) | `selftest.py` writes a dummy case folder to a temp dir outside the repo: one valid case, one broken one (missing prompt, key file inside packet/, bad regex, bad driver mode, must_do without text) |
| Whole pipeline: arms, skill-file reads in order, triage line, fact mention vs first edit, premature signal, option 4, key checks, hidden tests, judge parsing, report | `selftest.py` with a stub `claude` that emits stream-json. **29/29** |
| Audit invalidates a run that touches key material | self-test (stub reads `…/key/answer_key.yaml`) |
| Usage-limit cutoff: run aborted, not judged, batch stops, run excluded from tables | self-test. This came from a real incident: the first smoke attempt was cut off by the account's session limit and was at first scored as a normal run. That batch was deleted |
| Resume after a mid-batch limit: only missing slots run, a completed run is not rebuilt, the aborted attempt is kept under `attempts/1/`, a finished batch is a no-op, and starting a batch over an existing one is refused | self-test |
| Near-limit flag from `rate_limit_event` utilization, shown per run | self-test with utilization 0.9 |
| All 10 visible cases validate; connector server round-trips | `gw_eval.py validate` |
| Hidden tests fail on the untouched workspace and pass on a correct fix (E2b passes when the rename is held) | ran each against the base and a hand-written fix |
| `--tools` strips the host's extra tools (publish, notify, schedule) but keeps the MCP tools | init inventory of a probe run |
| Nested runs work here: `claude-opus-5` resolves, clean profile, `--add-dir` loads the skill only in the with arm | smoke runs' `system/init` |

Not verified:
- The LLM driver persona (E9) has not run against a real agent yet.
- Resume has only been exercised with the stub, not after a real limit.
- The judge has scored exactly 2 real runs. Its verdicts are plausible and cite events, but
  nobody has checked them against a human reading.

## 3. E1 smoke test (addition c): 1 run per arm, `claude-opus-5`, effort medium

Batch `eval/results/smoke-E1/` (the second attempt; see §2 for the first). Skill at `8741e39`
(its content is unchanged since M2's `5d92fc5`).

| | with Groundwork | baseline |
|---|---|---|
| **Measured agent cost** | **$3.63** | **$1.91** |
| Judge cost | $0.52 | $0.45 |
| Run total | $4.16 | $2.35 |
| Agent turns / wall time | 36 / 359 s | 18 / 198 s |
| Output tokens / cache-creation tokens | 28.9k / 60.8k | 16.4k / 40.1k |
| Driver turns (words the driver read) | 1 (820) | 1 (703) |
| **Skill files read** | **`SKILL.md` only** (via the Skill tool) | none (skill not present) |
| Triage line | `Groundwork: full — …`, before the first edit | – |
| **Pre-edit check, visible in chat** | **did not fire** | – |
| Pre-edit check, substance in notes before the first edit | yes: the affected-work map in `decisions.md` [35] lists which work depends on unknown U1 and what goes ahead | – |
| Store artifacts | requirements, decisions, questions, gate-record (no template read) | none (wrote a note file at the workspace root) |
| Replica count (8) and overnight volume stated before the first code edit | yes, both, with per-pod arithmetic | no. It read the same files, but stated the facts only after the code existed |
| Caught before code (proxy ∧ judge) | 2/2 facts | 0/2 facts. Judge: the design accounts for both. The strict proxy fails on ordering |
| Premature implementation (judge) | pass | pass |
| Premature auto signal | fired (false positive, see below) | fired (false positive) |
| must_do met / must_not_do violated | 5/5 / 0 | 4/5 / 0 (D1 partly) |
| CORRECTNESS defects left (judge) | 3 (e.g. out-of-order offset commit on the redelivery path) | 4 (e.g. same-SKU collapsing drops `stock.sent` records without checking the warehouse reader) |
| Unnecessary code items (judge) | 1 (a second unbatched run loop behind a capability check) | 2 |
| Near a usage limit | no (account 5h utilization up to 0.44) | no (0.15) |

What this shows, with n=1 per arm, so as a direction only:
- **Phase files: 0 reads, again.** That's now 0 phase-file reads in 8 loaded full-mode runs
  (M2: 7, here: 1). The with arm still wrote four store artifacts in the templates' shape, from
  SKILL.md alone. That's the pattern addition (a) asks about. E1/E6/E7 at batch scale will
  decide it.
- **The pre-edit check didn't fire as a visible line.** Its content did exist, in the decision
  record written just before the first edit. The SKILL.md wording ("name the open unknowns…")
  doesn't say where, and the agent chose the file. The report now shows "in chat" and "in
  store notes only" as separate rows, so the batch will show which one happens.
- **The baseline was strong on this case.** It built size-or-age flushing, commit-after-send,
  and drafted the partner note. The difference was in ordering and completeness, not in the
  design: the with arm stated the facts before coding and left one fewer defect. It cost 1.9×
  and took 2× the turns. E1 may not separate the arms much on outcome. That's worth knowing
  before reading batch results as "the skill helps".
- **The premature-implementation auto signal is too broad for E1.** It fires whenever
  dependent code is edited while U1 is open, but the key allows building the safe option
  (time flush) while asking. The judge overrode it in both runs. The judge's verdict is the
  metric; the signal stays as a cross-check. I'd tighten E1's `dependent_code` pattern to
  size-only flushing only after seeing more runs, not on n=1.

## 4. Projected batch cost (inferred, not measured)

Based on E1 only, the heaviest visible case (with $4.16, baseline $2.35 per run including the
judge). Other cases estimated as heavy (E3, E6, E9 ≈ E1), medium (E2b, E4, E5, E7, E8 ≈ $1.8
per run) and trivial (E2 ≈ $0.6):

| Plan | Runs | Projected |
|---|---|---|
| Full visible set, n=3 per arm | 60 | **≈ $135** (±40%) |
| Full visible set, n=2 per arm | 40 | ≈ $90 |
| E1 on one other model, 2 per arm | 4 | ≈ $8 |

The n=3 projection is under the ~$150 line, but the uncertainty band crosses it. The batch
cap (`--max-total-usd 150`) stops scheduling at $150 either way.

**Usage limits matter more than dollars here.** During these two runs the account's
five-hour utilization went from 0.08 to 0.44 (0.48 a minute later). This session's own usage
is included, so attribution isn't clean. If that ratio holds, one five-hour window covers
roughly 10–12 runs, so a 60-run batch needs about 5–6 windows (a day or more of wall time),
and the seven-day window (0.11 → 0.13 here) would take roughly +40%. Resume makes that
correct, but not fast. `--jobs` doesn't help against the limit. Runs made close to a limit
are flagged per run.

## 5. Requires local verification

- **Practical check in the daily host (Cursor)**, spec §12.3. It can't run in this cloud VM.
  On your machine, with the skill installed per the root README:
  1. In a scratch copy of the synthetic workspace
     (`cp -r eval/workspace/base ~/gw-practical && cd ~/gw-practical && for d in */; do (cd $d && git init -q && git add -A && git commit -qm initial); done`),
     open the folder in Cursor.
  2. Run three prompts, each in a fresh chat: E2's prompt, E2b's prompt, and E1's prompt
     (without the tracker, so paste ticket 131's body from `eval/cases/E1/packet/connectors/tickets.json`).
  3. For each, note: did the first line read `Groundwork: …`; which skill files did it open
     (Cursor shows file reads); was anything edited before a question; minutes you spent
     reading and answering.
- Nothing else in M3 needs a local machine.
