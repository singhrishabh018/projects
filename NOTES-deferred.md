# Deferred ideas (not in v0.1)

Anything here needs a v0.1 result that justifies it (spec §13, v0.2).

## Eval
- **TypeSafe/Jev as an optional eval-scoring layer.** Try at M3 behind an env flag (e.g. `GW_EVAL_JEV=1`). Never a dependency of the skill or harness, never gates material decisions or pass/fail.
- **Task-blind research (C4 variant).** Goal hidden during fact-finding. Run as an eval variant only if v0.1 results show goal-anchored research misses things.

## Companions
- **save-token-jev** (MIT, github.com/IAmUnbounded/save-token-jev-clean) — suggested companion for context compaction. Mention in README; don't rebuild.

## Spec items outside v0.1 scope (§13)
- Investigate / Answer / Review / Handoff / Decide flows as separate flows.
- Persistent workspace map, revalidation of stored claims (C3), capture (C13), workspace ledger (C12), stakeholder registry (C7.1), answer ingestion (C7.6), acceptance log file (C7.7 — v0.1 keeps its fields inline).
- `rules/guard.md` + adapters + rule-copy consistency script (v0.1 keeps G1–G8 only in SKILL.md).
- Slash commands (`/gw-*`, `/gw-ask`).
- Hooks and hook-enforced gates.
- Diagram verification (C14.4), code-intelligence accelerators (C14.5).
- Learning hooks (C10). v0.1 only offers a plain-English explanation on request.
- Team storage mode.
