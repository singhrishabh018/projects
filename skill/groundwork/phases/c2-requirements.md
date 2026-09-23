# C2 — Requirements record

Purpose: know exactly what is being asked, by whom, and where the sources disagree,
before looking for where to change code.

## Steps

1. Gather sources: the prompt, anything pasted, and connector items (`phases/c14-connectors.md`).
   Keep each source's provenance: kind · key/URL · author · last updated · retrieved at.
2. Extract requirements, one line each, with id `R1…`, source, date and owner.
   Quote stakeholder asks **verbatim** ("we must be able to see what was sent").
   A requirement states a need, not an implementation (F5).
3. List **contradictions** `X1…` between sources (ticket vs doc vs thread vs code vs
   prompt). For each: the two statements, their sources and dates, and a status:
   `resolved` (by whom/what) · `awaiting` (question drafted) · `accepted-assumption`.
   Never pick a side silently; the more recent or more authoritative source is a
   *suggestion* to show the user, not a resolution.
4. Mark **superseded** statements (and why) so later phases don't reuse them.
5. List **material unknowns** `U1…` with status (`open` · `awaiting` · `resolved` ·
   `accepted-assumption`). Open C7 for each one a person must answer.
6. Scope and non-goals: what's in, what's out, and who said so. The agent never narrows
   scope on its own; a scope change is a question to the user.

The user is the authority on scope and priority. They are not, by default, the authority
on how the system behaves (see answer rules in `rules/full.md`).

## Output

`requirements.md` (template: `templates/requirements.md`).

## Gate

Every contradiction is `resolved`, `awaiting` or `accepted-assumption`; none silently
chosen. Work that doesn't depend on an open contradiction continues.
