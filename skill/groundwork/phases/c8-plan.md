# C8 — Plan and verification plan

Purpose: build the minimum that correctly does the job, in slices that can move
independently, with a way to show each requirement works.

Write `plan.md`:

## Slices

Vertical slices, each with: goal · repos/files · **depends on** (decision/unknown ids) ·
blast radius (what else could break: callers, consumers, shared config, schedules) ·
rollout and rollback, when the change is externally visible or hard to reverse.
Slices with no open dependencies start now.

## Reuse declaration

Existing modules, clients, helpers and patterns this plan uses, with paths; the golden
example each slice follows. Any **new** abstraction cites the requirement that needs it and
why the reuse candidates don't fit (F6). No speculative extras (rate limiters, caches,
persistence, config knobs) without a requirement or a failure-model reason.

## Verification plan (per requirement)

| Req | Method | Proves |
|---|---|---|
| R1 | failing-then-passing test / end-to-end run / contract check / config diff / doc check | <what exactly> |

- Derive tests from requirements and decisions, not from the implementation.
- Use a failing test first where it genuinely demonstrates the defect or behaviour.
- Mocks and stubs encode assumptions; for external contracts, assert on what the other
  side *accepts* (field names, formats), not on a success status.
- Add system scenarios where topology, volume or schedules matter (e.g. N instances,
  low volume, the job runs later).

## Decision-closing wording

When handing a slice to an implementer (you, a subagent, or a later session), close each
decision like this: *"Decided X because Y. If evidence shows Y is false, stop this slice and
report."* Never "don't ask" or "ignore conflicts".

## Checkpoints

Commit per slice only if the user's workflow allows it; otherwise recommend the commit
points. Don't touch unrelated code (scope drift).
