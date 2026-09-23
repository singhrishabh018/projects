# C4 — Research: neutral questions and disconfirming search

Purpose: stop research from only finding "where to put the change".

## Steps

1. Before searching for the change location, write 3–7 **neutral questions** about how the
   system works, e.g. "What decides whether an item is sent?", "How many instances run,
   and what state does each keep?", "When does data become visible downstream?",
   "What does the external side do with a malformed or unknown field?".
   Answer them with C3 claims.
2. For each **working assumption** behind the likely design (things you'd otherwise take
   for granted), write what would prove it wrong, then look for exactly that:
   ```
   A1 assumption: <...>
      would be wrong if: <...>
      searched: <where/how>  →  found: <claim or "nothing">
   ```
   Assumptions you can't test stay visible as unknowns.
3. A concern that evidence disproves is recorded `contradicted` in one line with the
   evidence, and dropped. No question, no stop.

## Output

Append to `research.md`: Neutral questions (with answers or `unknown`) · Assumptions and
disconfirming search.
