# C11 — Handoff

Use when work continues in another session or agent. Write `handoff/` in the task folder:

1. **`spec.md` — implementation spec.** Scope and non-goals · contract(s) · claims with scope
   (status/source/date/commit) · decisions with status · accepted assumptions (who, why,
   what reverses) · **one** blocker list · verification plan. Reconcile first: one blocker
   list, superseded items removed, no append-only history. Don't add "don't relitigate X"
   lines; state the decision and its reason once.
2. **`background.md`** — history, who is involved, communication notes. Kept separate so
   the spec stays short. Private: nothing here is meant for teammates.
3. **`prompt.md` — execution prompt**, separate from the spec. It tells the next agent what
   to do, uses decision-closing wording (C8), and contains a retrieval marker line:
   `GW-MARKER: <random word>`. It asks the receiving agent to begin with:
   the marker, then scope in 3 lines, then the open material unknowns and accepted
   assumptions. The marker shows the instructions arrived; the restatement is how the
   user checks they were understood.

Then run the C6 implementability check on `spec.md` (fresh context if available).
Use `templates/handoff.md`.
