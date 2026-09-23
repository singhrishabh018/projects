# Gate records — <task>

<!-- Append one block per gate that couldn't complete. Never skip or pass silently. -->

```
Gate:          <C6 design review | C9 verification | connector: tickets | ...>
Reason:        missing access | unanswered question | reviewer unavailable |
               review budget exhausted | connector failure | other
Status:        incomplete
Affected work: <slices / decisions that depend on it>
Can proceed:   <work that doesn't depend on it>
Blocked:       <work that does>
Next action:   <what would complete it, and who owns it>
Recorded:      <date>
```

## Defaults when a gate can't complete

| Situation | Default |
|---|---|
| Missing access (logs, DB, partner UI) | Claim stays unconfirmed; give the user the exact check to run (answer option 2); dependent work blocked unless an assumption is accepted |
| Unanswered question | Unknown stays `awaiting`; apply its declared no-answer default |
| Reviewer unavailable | Self-review labelled *not independent*; final report says so |
| Review budget exhausted | List remaining material gaps; no "passed" |
| Connector failure | Affected claims `unknown` with a retry note; offer paste/export fallback |
