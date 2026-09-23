# M1 self-check (2026-09-23)

A quick smoke check, not an evaluation. The only thing it establishes: the skill loads, it
triages, and guard mode stays cheap, on two tasks in one tiny scratch workspace. Visible
eval cases (M3) are separate and were not used for this.

## Setup

- Scratch workspace: two git repos. `order-svc` publishes a JSON payload with field `qty`;
  `label-svc/consumer.py` reads `msg["qty"]`. One log message has a typo.
- Tasks: **trivial** = "Fix the typo in the log message in order-svc/app.py."
  **cross-repo** = "In order-svc, rename the payload field qty to quantity."
- Host: Claude Code 2.1.280 headless, `--model claude-sonnet-5` for every run (chosen for
  cost in this check; the eval model is still to be pinned at M3). Clean profile per run
  (`CLAUDE_CONFIG_DIR=<empty>`), fresh `GROUNDWORK_HOME`, `--permission-mode acceptEdits`
  with tool allowlist. `--dangerously-skip-permissions` is refused when running as root.
- With arm: `--add-dir <root containing .claude/skills/groundwork>`. Baseline: no `--add-dir`.
  `system/init` confirmed `groundwork` is listed in the with arm and absent in the baseline.

## Results

Costs are from the run's own `total_cost_usd` (client-side estimate). The first round had
cold caches (~$0.18–0.24 per run) and isn't comparable, so the table uses warm-cache runs.

| Run | Description | Skill loaded | Edited before surfacing consumer | Cost | Turns |
|---|---|---|---|---|---|
| trivial, baseline ×2 | — | — | n/a | $0.056, $0.059 | 4, 4 |
| trivial, with ×3 (+1 cold) | v2 ×3 (one after the option-4 fix); cold run was v1 | **no** (0/4) | n/a | $0.056, $0.056, $0.063 | 4 |
| cross, baseline ×2 (+1 cold) | — | — | **yes** (3/3): renamed in order-svc, then warned | $0.110, $0.145 | 7, 9 |
| cross, with, v1 description ×1 | v1 | **no**: said "let me load the groundwork skill", never did | **yes** | $0.244 (cold) | 7 |
| cross, with, v2 description ×4 | v2 (directive "load BEFORE…") | **yes** (4/4), before any read or edit | **no** (0/4): asked first, nothing edited | $0.100–0.107 | 7–8 |

Loaded skill body in context: 5,079 characters ≈ 1.3k tokens, measured before the option-4 wording fix added ~250 characters (budget: ~1.3k).

## What this shows

- **Description wording decides whether the skill loads at all.** v1 (descriptive) loaded
  0/2 times (one trivial, one cross-repo); v2 (directive, "load BEFORE the first search, read or edit…") loaded 4/4 on the
  cross-repo task. SKILL.md now uses v2. E2b will measure this properly.
- **Guard mode is cheap here.** On the cross-repo task the with-arm cost was about the same
  as baseline ($0.10–0.11 vs $0.11–0.14, n=4 vs 2 — too few runs to call it a difference).
  On the trivial task the skill **did not load at all**, so its cost there was only the
  description in the skill listing. Guard rules therefore did **not** apply on the trivial
  task. That's the cheap end of "bias toward loading"; E2 and E2b will show whether it's
  the right trade.
- **Surfacing changed; understanding didn't.** The baseline also found the consumer every
  time, but only *after* making the breaking edit. With the skill, the edit was held and a
  question was asked first. That's the "before code" behaviour on this one tiny case, nothing
  more.

## Defects found (to fix in M2, not tuned further here)

1. **Option 4 misapplied (1 of 2 runs before the wording fix, 1 of 2 after).** "None of
   these" was written as "I'll do the breaking rename anyway". The fix belongs in the M2
   question template (`templates/questions.md`, `phases/c7-questions.md`), with the no-answer
   default filled in explicitly.
2. **Technical judgment asked of the user.** Option 1 asked about "staged rollout" and
   "compatibility window". The plain-language rule isn't strong enough on its own; the M2
   template will require a recommended default with its consequence in plain words, so the
   user only confirms or declines.
3. **Option 2 not an exact step** ("grep other service repos"). Same template fix.
4. **Full mode didn't read `rules/full.md`.** In every loaded run the agent triaged full,
   found the conflict and asked immediately. Reasonable for a task that's entirely blocked,
   but it means full-mode rules were never exercised. Phase files don't exist yet (M2), so
   phase loading couldn't be tested.
5. **Triage line printed inconsistently** (2 of 4 loaded runs). Needed for the Cursor
   hands-on check and for E2b scoring. M2: make it the literal first output line.

## Harness notes carried to M3

- Agents sometimes ran `find /` style searches outside the workspace. Keys and held-out
  cases must live somewhere an agent run can't reach, and runs are audited for access.
- Cost comparisons must use warm-cache runs or report cache-creation and cache-read tokens
  separately; cold runs cost 3–4× more on the same task.
- The runner must not run as root with `--dangerously-skip-permissions`; use `acceptEdits`
  plus an explicit tool allowlist.
