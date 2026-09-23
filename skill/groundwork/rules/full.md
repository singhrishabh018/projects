# Full-mode rules

Read once when triage selects full mode. Guard rules G1–G8 still apply.

## F1 Evidence standard — claims

Every material claim is written as:
`[status · source · scope] statement`

| Dimension | Values |
|---|---|
| status | `observed` · `inferred` · `unknown` · `contradicted` |
| source | code · config/manifest · documentation · runtime observation · owner statement · vendor statement |
| scope | environment · repo@commit or version · observed-at date |

A citation proves what its source says, nothing more. The same topic yields different claims:
- `[observed · config · infra-repo@a1b2c3, 2026-09-23]` the prod config sets a 30s request timeout
- `[observed · runtime · prod, 2026-09-23 14:00]` requests were timing out at 30s at that time
- `[observed · owner statement · service owner, 2026-09-23]` owner expects the timeout to be 30s
- `[observed · documentation · wiki page, last edited 2026-03-03]` the page says status `closed`
  means "refunded". Whether the code still behaves that way is a separate claim.

Claims from earlier sessions are re-checked against their sources before a current
decision relies on them.

## Unknowns, assumptions, decisions (§5.2)

| Unknown status | Meaning |
|---|---|
| `open` | identified; no answer sought yet |
| `awaiting` | evidence/answer requested — from whom, when, via what |
| `resolved` | answered; link the claim that resolves it |
| `accepted-assumption` | proceeding under uncertainty; record **who** accepted, **why**, **what would reverse it** |

- An accepted assumption authorises proceeding; it is not a fact. It stays visible in the
  decision record and handoff until resolved.
- **Silence is never approval.** Each question declares its no-answer default: *already
  authorised* · *safely reversible and flagged* · *affected work stays blocked*.

### Answers from the user (non-expert driver)

Record every answer as `[observed · owner statement · user · date]`. For a **material
technical** unknown, the answer resolves it only if:
- it agrees with code/config/runtime evidence you can see, or
- the user says they checked a named source (query result, dashboard, owner reply).

Otherwise record it as `accepted-assumption` (the user may authorise proceeding), with a
one-line plain-language consequence ("if this is wrong, some orders will be charged twice").
If code or config contradicts the answer, mark it `contradicted`, show the evidence once,
and ask again with the four answer options. A blanket "yes to all" accepts only the items
the user was shown one by one; everything else keeps its status.

## F2 Materiality (§5.3)

Always-material triggers (the list in `SKILL.md`) must be examined and recorded; they can't
be classified as routine. Examined and disproved is fine: record it `contradicted` in one
line and move on — no question, no stop.

| Classification | Action |
|---|---|
| Material, adequately supported | Record evidence and decision; proceed. No extra approval. |
| Material, unresolved | Mark affected work; seek evidence or decision (`phases/c7-questions.md`); continue independent work. |
| Non-material | Proceed. Consequential judgment calls go in the **non-material scan list**: one line each, choices that could plausibly change design or behaviour (not naming/formatting), so the user can catch a misclassification in under a minute. |

## F3 Independent review where available

Design review (C6) and verification (C9) run in a fresh context — a subagent given only the
inputs the phase lists — when the host offers one. Otherwise self-review, labelled
**not independent**, with a gate record. Fresh context reduces bias; it doesn't prove
correctness.

**Review budget:** C6 max 2 rounds, stop after round 1 if no material gaps. C9 one full
round plus one re-check after fixes. Then report remaining gaps. Never label a result
"passed".

## F4 Severity ≠ confidence

Record both separately. A low-confidence, high-severity finding stays in the main findings,
labelled *needs evidence*.

## F5 Requirements define needs, not implementations

Keep a stakeholder's need ("we must be able to see what was sent") even when a generic best
practice argues otherwise; evaluate ways of meeting it like any other design choice. Judge
severity against the requirements and the failure model, not a checklist.

## F6 Reuse first

New abstractions, helpers or clients cite the requirement that needs them and the existing
candidates that were rejected, with why.

## F7 Proportional stopping

An unresolved material unknown blocks only the slices that depend on it (see the
affected-work map). Everything else proceeds.

## When a gate can't complete (§5.6)

Never skip silently, never pass silently. Append to `gates.md` (template:
`templates/gate-record.md`):

```
Gate:          <which gate>
Reason:        missing access | unanswered question | reviewer unavailable |
               review budget exhausted | connector failure | other
Status:        incomplete
Affected work: <slices / decisions that depend on it>
Can proceed:   <work that doesn't>
Blocked:       <work that does>
Next action:   <what would complete it, and who owns it>
```

| Situation | Default |
|---|---|
| Missing access (logs, DB, partner UI) | Claim stays unconfirmed; give the user the exact check to run (answer option 2); dependent work blocked unless an assumption is accepted |
| Unanswered question | Unknown stays `awaiting`; apply its declared no-answer default |
| Reviewer unavailable | Self-review labelled *not independent*; final report says so |
| Review budget exhausted | List remaining material gaps; no "passed" |
| Connector failure | Affected claims `unknown` with a retry note; offer paste/export fallback |

## Final report (every full-mode task)

End with: what changed · what was verified and how · open unknowns and accepted
assumptions (with consequence) · incomplete gates · whether review was independent.
