# C6 — Design review (two checks)

Purpose: the author of a design is the worst judge of what it's missing.

## Checks

1. **Completeness:** does `decisions.md` satisfy every requirement and external
   constraint in the *original sources*? Inputs: the original sources (not only
   `requirements.md`) + `decisions.md`.
2. **Implementability:** could another agent build it without making material guesses?
   Inputs: `decisions.md` + read access to the repos.

## How

- If the host can start a **fresh-context subagent**, run each check there. Give it only
  the inputs above plus this instruction: "List material gaps only: missing requirement,
  unsupported claim, contradiction, a guess an implementer would have to make. For each:
  what, where, why it matters, confidence. Do not propose extra features." Don't pass your
  own reasoning or conclusions.
- Otherwise, do it yourself and label the review **not independent** with a gate record.
- A reviewer can inherit a wrong premise from the record; that's why completeness checks
  against the original sources.

## Budget

Max 2 rounds. Stop after round 1 if there are no material gaps. After round 2, list
the remaining gaps (gate record: review budget exhausted). Never write "review passed".

## Output

`design-review.md`: per round — reviewer (independent: yes/no), inputs given, gaps found,
what changed in `decisions.md`, gaps remaining.
