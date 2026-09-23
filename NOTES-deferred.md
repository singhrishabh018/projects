# Deferred ideas (not in v0.1)

Anything here needs a v0.1 result that justifies it (spec §13, v0.2).

## Eval
- **TypeSafe/Jev as an optional eval-scoring layer.** Not built at M3: the harness's own judge covers the scoring §12.4 needs, and nothing so far shows a gap it would fill. If added later: behind an env flag (e.g. `GW_EVAL_JEV=1`), as an extra report column only. Never a dependency of the skill or harness, never gates material decisions or pass/fail.
- **Task-blind research (C4 variant).** Goal hidden during fact-finding. Run as an eval variant only if v0.1 results show goal-anchored research misses things.

- **Blind judging.** The judge can usually tell the arm (triage lines, store notes). Stripping those would need rewriting the transcript; only worth it if judge verdicts look arm-biased.
- **Size-check script** (M0 §4 mentioned one). Dropped: sizes were measured by hand at M2 and accepted; no budget is enforced.
- **Practical check in the daily host (Cursor)** is manual and lives in the root README, not in the harness.

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
