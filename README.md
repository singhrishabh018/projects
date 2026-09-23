# Groundwork

A portable agent skill that makes a coding agent do the groundwork a senior engineer does
before a big change: understand the ask, learn how the real system works across repos,
surface decisions and unknowns early, build the minimum, and get checked by something other
than itself. On small tasks it stays out of the way (guard mode).

Status: **v0.1 in progress** (spec v0.3). Private use.

## What's in the box

```
skill/groundwork/        ← the installable skill folder
  SKILL.md               triage, guard rules G1–G8, how to ask the user, full-mode router
  phases/                C1–C9, C11, C14: one file per build-flow phase, read on demand
  probes/                common checklist + deploy topology + external API
  templates/             requirements, decisions, questions, gate record, verification, handoff
eval/                    evaluation harness and cases (M3)
docs/                    M0 plan (scope, spec gaps, verified host facts), M1/M2 checks
NOTES-deferred.md        ideas intentionally left out of v0.1
```

## Install

Install **one copy** globally. The folder name must stay `groundwork` (Cursor requires the
`name` field to match the folder).

### Claude Code (global)

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skill/groundwork" ~/.claude/skills/groundwork   # or: cp -r skill/groundwork ~/.claude/skills/
```

- Loads automatically when the description matches the task; force it with `/groundwork`.
- Check: start a session and ask "what skills do you have?" — `groundwork` should be listed.
- Once loaded, the skill stays in context for the rest of the conversation.

### Cursor (global)

Cursor reads `~/.cursor/skills/`, `~/.agents/skills/`, and — for compatibility —
`~/.claude/skills/`. Pick **one**:

```bash
# if you already installed for Claude Code on this machine: nothing to do, Cursor reads ~/.claude/skills
# otherwise:
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/skill/groundwork" ~/.cursor/skills/groundwork
```

Don't install in both `~/.claude/skills` and `~/.cursor/skills` on the same machine; you may
get the skill listed twice (not tested).

- Check: **Customize → Skills** should list `groundwork`.
- Cursor attaches a `/`-invoked skill to **one message**. For a long full-mode task, either
  let the agent pick it up automatically or use it as a Custom Mode (Alt+Enter) so it stays
  on for the whole session.

### Where it writes

Full-mode artifacts go to `~/.groundwork/` (override with `GROUNDWORK_HOME`), outside all
repositories. It never writes files into your repositories except the code change you asked
for. Guard mode writes nothing.

### Optional: always-on guard pointer

If you want guard rules considered on every task (not just when the skill auto-loads), add
this one line to your personal instructions (`~/.claude/CLAUDE.md`, or Cursor user rules).
Not installed by default:

```
For any task that changes code or asks how a system works, load the `groundwork` skill and follow its triage line.
```

### Hands-on check (Cursor)

1. Skill loads from the global location: it appears in Customize → Skills.
2. Guard rules appear: on a small edit, the first line of the reply is
   `Groundwork: guard — …`.
3. A phase file loads on heavy work: on a cross-repo change, the reply starts
   `Groundwork: full — …` and the agent reads
   `phases/c1-triage.md`.

## Modes

- `off` — nothing. `guard` — G1–G8 only, no files. `full` — phases with artifacts.
- Say `groundwork off | guard | full` at any time; your choice wins.

## Companions

- **save-token-jev** (MIT, github.com/IAmUnbounded/save-token-jev-clean) — suggested
  companion for context compaction on long full-mode sessions. Not required; not bundled.
- Works alongside process skills (planning/TDD) and minimalism skills; Groundwork covers
  evidence, system facts and questions, not coding style.

## License

MIT.
