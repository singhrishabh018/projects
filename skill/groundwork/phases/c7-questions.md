# C7 — Questions (outreach lane)

Purpose: get missing answers from the right person early, without stalling other work.
Opens the moment a material unknown appears, in any phase.

## 1. Route each unknown first

| Answerable from | Action |
|---|---|
| code / config in the workspace | research it (C3); don't ask |
| docs / connectors | look it up (C14); don't ask |
| a person (owner, team) | draft a question |
| an external party | draft a question, via the user |
| a decision owner (scope, priority, business meaning) | draft a question |

People only get questions only they can answer.

## 2. Draft

Use `templates/questions.md`. Each question has: a one-line context readable without the
thread · the question (yes/no or pick-one) · why it matters (concrete consequence) and
which work it unblocks · your recommendation (the option that is safe if wrong) · its
**no-answer default**: *already authorised* · *safely reversible and flagged* ·
*affected work stays blocked* · the four answer paths (SKILL.md).

- Option 2 is an exact step a non-expert can follow: a command to paste, a query, or a
  click path. Not "check the config".
- Option 3 is a ready-to-send message addressed to a candidate owner **role**, with the
  evidence for why them (CODEOWNERS, recent committers, ticket reporter) when cheap to find.
- Option 4 = the no-answer default. It names the affected work (from the affected-work
  map) that stays unchanged and the unrelated work that continues. It never performs the
  affected work.
- ≤ 4 questions per person, most important first. Respectful, factual and direct whatever
  the recipient's seniority. External messages don't expose internal debate; business
  stakeholders get plain language.
- Formats on request: chat message (default), email with subject, ticket comment, meeting
  agenda with decision asks, one-page escalation for sign-off.

## 3. Draft-only

The skill drafts; the user sends. Never post, comment or email, even if a connector could,
unless the user explicitly asks for that specific message.

## 4. Status and gate

Mark the unknown `awaiting` (who, via what, when). Routing a question unblocks nothing:
dependent work stays blocked until the unknown is `resolved` or `accepted-assumption`.
Record answers as claims per `rules/full.md` (answers from the user).
Keep doing everything the affected-work map says is independent.
