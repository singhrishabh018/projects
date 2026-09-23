# C5 — Decision record (draft, living)

Purpose: important behaviour is chosen on purpose, not whatever the code happened to do.

Create `decisions.md` from `templates/decisions.md` as a **draft** as soon as the first
real choice appears; update it as evidence and answers arrive. Target ≤ 2–3 pages.
One record per feature, shared across repos: every repo's slice cites the same decisions.

## Per decision

question · options · choice · rationale · rejected alternatives (why) · owner ·
reversible (Y/N) · supporting claims (ids from `research.md`) · status:
`proposed` → `supported` (evidence backs it) · `awaiting` (question out) ·
`accepted-assumption` (who, why, what reverses it) · `decided` (owner chose).

- **Owner.** Scope, priority and business meaning belong to the user or a named owner.
  Technical choices the agent can back with evidence may be `supported` without asking.
  Technical choices it can't back go to C7; the user may accept the recommended option
  as an assumption, which never turns it into a fact.
- The agent never records a human decision the human didn't make ("excluded per prior
  agreement") and never narrows scope on its own.

## Also in the record

- **Scope / non-goals** (from C2).
- **Proxy register**: each proxy, the concept it stands for, confirmed or not.
- **Failure model** (if triaged): delivery semantics, what happens on failure, how it's
  noticed and reconciled.
- **Volume math** (if triaged): back-of-envelope numbers that decide the design (events/day,
  instances, batch sizes, time to flush, rate limits). Show the arithmetic.
- **Non-material scan list**: one line per consequential judgment call you classified as
  non-material. Not naming or formatting.
- **Affected-work map**: which slices depend on which unknowns/decisions. This is what
  lets independent work continue (F7) and what option 4 of a question refers to.
- **Deferred** items (with why).

## Gate (per slice)

A slice may be implemented when every decision it depends on is `supported`, `decided`
or `accepted-assumption`. New evidence against a decision reopens it and stops only the
slices that depend on it.
