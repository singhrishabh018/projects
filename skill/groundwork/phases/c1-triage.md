# C1 — Triage and task setup

Purpose: pick the least process that still catches what matters on this task.

## Steps

1. Restate the ask in one sentence. If you can't, go straight to C2.
2. Check the always-material triggers (SKILL.md) against what the change touches. For each
   one that applies, note it in a word; that list drives what follows.
3. Choose phases. Default for full mode: C2 → C3/C4 → C5 → C6 → C8 → implement → C9,
   with C7 opened whenever a material unknown appears. Drop what the task doesn't need,
   and say why:
   - one external call in familiar, well-tested code → guard rules + a verification plan (C8 §verification only)
   - no design choice left once facts are known → skip C6
   - single session, no continuation → skip C11
4. Conditional sections for the decision record:
   - **failure model** when delivery, retries, ordering, data correctness or money matter
   - **volume math** when throughput, batching, buffering, rates or schedules matter
5. Create the task folder (outside every repo):
   `${GROUNDWORK_HOME:-~/.groundwork}/workspaces/<workspace-id>/tasks/<YYYYMMDD-slug>/`
   workspace-id: `$GROUNDWORK_WORKSPACE`, or sorted repo-root folder names joined by `+`
   plus the first 6 hex chars of `sha1` of the sorted absolute paths. For example:
   `printf '%s\n' /abs/repoA /abs/repoB | sort | sha1sum | cut -c1-6`
   If it can't be written, keep artifacts in the conversation and add a gate record.

## Output (top of `requirements.md`)

```
Mode: full · Flow: build
Triggers: <e.g. cross-repo, external contract>
Phases: <list> · Skipped: <phase — why>
Conditional: failure model <y/n>, volume math <y/n>
Why: <2–3 lines>
```

The user can override any of this; record the override and continue.
