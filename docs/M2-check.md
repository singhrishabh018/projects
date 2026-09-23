# M2 check (2026-09-23)

Smoke check of the build flow with phase files in place. Not an evaluation: scratch tasks
only (same two-repo scratch workspace as M1: `order-svc` publishes `qty`, `label-svc` reads
it), no visible eval cases used. Model `claude-opus-5` (the pinned eval model), clean
profile per run, with-skill arm only. The simulated user was a fixed reply string.

| Task | Prompt | Driver replies | Runs |
|---|---|---|---|
| mixed | "In order-svc: rename the payload field qty to quantity, and fix the typo in the log message." | "None of these." | 3 |
| heavy | "Label printing should put priority orders first. Add a priority flag to orders in order-svc and make label-svc use it." | "Go with your recommendation." ×3 (yes-to-everything) | 2 |
| trivial | "Fix the typo in the log message in order-svc/app.py." | — | 2 |

## 1. Option 4 test (pass/fail, mechanical)

Pass = after the "None of these." reply, the affected work is **not** done (payload key is
still `qty` in `order-svc`, `label-svc` untouched) **and** the unrelated work **is** done
(typo fixed). Checked with `git diff` of both repos at the end of the run.

| Run | Option 4 offered | Affected work held | Unrelated work done | Result |
|---|---|---|---|---|
| mix-1 | yes | yes | yes | **PASS** |
| mix-2 | yes | yes | yes | **PASS** |
| mix-3 | yes | yes | yes | **PASS** |

**3/3 pass.** In all three runs the typo was fixed *before* asking (independent work
proceeded), and option 4 was worded as a hold, not as "do it anyway" (M1 defect 1 not seen
again in these 3 runs). Small n; this becomes an automatic metric in M3.

Related question-quality checks on the same 3 questions:
- Option 2 exact, copy-pasteable step: **2/3** (mix-1 said "broker admin UI, or your
  service catalog", not an exact step).
- Recommendation given, user not asked to choose between technical designs: **3/3**
  (M1 defect 2 not seen again).

## 2. Triage line

After the skill loaded, the first text line was `Groundwork: <mode> — …` in **5/5** loaded
runs (M1: 2/4). In 2 of the 5, the agent wrote one line of narration ("I'll start by
loading the groundwork skill…") *before* calling the Skill tool. That can't be avoided
from inside the skill, so the E2b check will look for the triage line anywhere before the
first edit.

## 3. Loading

| Run | Skill loaded | `rules/full.md` read | Phase files read | Store artifacts |
|---|---|---|---|---|
| mix-1..3 | yes (3/3) | no | none | none |
| heavy-1 | yes | **no** | **none** | **none** |
| heavy-2 | yes | yes | `c1-triage.md` only | `decisions.md` |
| trivial-1..2 | **no** (0/2) | — | — | — |

- Trivial: the skill didn't load (0/2), as in M1. Guard rules didn't apply on it.
- Mixed: full mode was triaged, the conflict was found and a question asked before any
  risky edit, with no phase file read. For this task, SKILL.md alone produced the right
  behaviour.
- Heavy: triaged full in both runs, but the build flow **wasn't followed**:
  - heavy-1 read nothing beyond SKILL.md and wrote no artifacts. It implemented both
    services in its first turn, including a `on_batch()` function nothing calls, and only
    then asked the central question ("where can label-svc actually reorder?"). That's the
    over-building / deciding-in-code pattern the skill exists to stop. The flag itself was
    safe, additive and independent work; the batching code depended on the open unknown
    and should have waited (F7).
  - heavy-2 read `rules/full.md` and C1, wrote `decisions.md`, then did the same thing:
    implemented first, asked second. On "go with your recommendation" it ran a
    fresh-context subagent review (C9-style), which caught two real defects (a batch-wide
    failure on one bad message; `bool("false")` is `True`). After the third "go with your
    recommendation" it still flagged the open product question ("batch-local ordering may
    not be what priority-first means") rather than treating the approvals as answers.
    Good for E9, but too few runs to count.
- Cost: mixed $0.90–1.17 per run (2 turns of the driver loop), heavy $1.70 and **$4.48**,
  trivial $0.13–0.36.

## 4. Answer to "what does `rules/full.md` add, and does it load?"

**It loaded in 1 of 5 full-mode runs.** The behaviour that went right (mixed task:
held the risky edit, did independent work, asked a well-formed question, option 4 held)
came from SKILL.md alone. The behaviour that went wrong (heavy task: code before the
design question) happened with and without it.

What it contains, and where else that already lives:

| full.md section | Also in | Unique? |
|---|---|---|
| F1 claim format `[status · source · scope]` | c3-discovery, templates | no |
| §5.2 unknown statuses, silence ≠ approval | c2-requirements, c7-questions, templates | no |
| **Answers from the user (non-expert/E9 rule)** | nowhere else | **yes** |
| F2 materiality table, scan list | c5-decisions, templates/decisions | mostly no |
| F3 independence + review budgets | c6, c9 | no |
| F4 severity ≠ confidence | c9, templates/verification | no |
| F5 needs not implementations | c2, c8 | no |
| F6 reuse first | c8 | no |
| F7 proportional stopping | c5, affected-work map | no |
| §5.6 gate record + defaults table | templates/gate-record (defaults table is unique) | partly |
| **Final report** (what changed, verified how, open unknowns, gates, independence) | nowhere else | **yes** |

So it's mostly duplication, it rarely loads, and the two parts that are unique are exactly
the parts that must apply even when nothing else loads (answers from a non-expert user;
the honest final report).

**Proposal (approved and done after this check; see `docs/M2-handoff.md`):** delete `rules/full.md`.
- Move the answers-from-the-user rule into SKILL.md "Asking the user" (about 3 lines):
  a user's answer to a material technical question is a statement, not verification;
  without evidence or a named source it becomes an accepted assumption with its
  consequence stated; code that contradicts it is shown once more.
- Move the final-report line into SKILL.md "Full mode" (1 line).
- Move the gate-record defaults table into `templates/gate-record.md`.
- Everything else already lives in the phase file that uses it.
Net effect: roughly +250 characters in SKILL.md, one fewer file, no rule lost.

## 5. Bigger finding: phase files aren't followed on the heavy task

Progressive loading assumes the agent reads each phase file when it reaches that phase.
In practice (2 heavy runs) it read at most C1 and went straight to implementation. The
phase files themselves were never exercised (C2–C9, C11, C14: 0 reads in 7 runs).

This is the thing to watch at M3/M4, not something to fix by more wording now. The
smallest change I'd propose if E1/E6/E7 confirm it: one **pre-edit checkpoint** in
SKILL.md's full-mode section, visible in the output, e.g.

```
Before the first edit in full mode, print:
Groundwork check — unknowns affecting this edit: <none | U…>; decision record: <path | not needed because …>
```

Decision after this check: a one-line pre-edit check was added to SKILL.md now, in the
user's wording (see `docs/M2-handoff.md` §2). Not yet tested.

## 6. Size

Correction, measured after this check: the character-based estimates undercounted.
Measured against an empty-body skill on `claude-opus-5`, the version tested here loads at
≈ 2.03k tokens; after the full.md merge and pre-edit check, ≈ 2.27k (118 lines). The size
is accepted; no trimming to a budget. Phase files 20–49 lines, templates 15–34, probes 22–30: all
within budget.
