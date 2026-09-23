# Groundwork v0.1 — M0 Build Plan

Status: proposal, awaiting go-ahead. Nothing below is built yet except this file and `NOTES-deferred.md`.
Spec: `groundwork-spec.md` v0.3 + the post-v0.3 decisions in the build brief (O2, O5, non-expert driver, learning never gates, lightweight, private use, O8, no third-party API, deferred notes, O13 held-out format).

Legend for claims in this doc: **verified** = I read the current doc page or ran it here today (2026-09-23); **inferred** = reasoning, not tested; **unverified** = could not check.

---

## 1. v0.1 scope, one line per §13 item

| §13 item | In my words |
|---|---|
| Plain-files skill, progressive phases, no hooks | One `SKILL.md` that stays small; phase files are read only when full mode needs them; nothing is enforced by hooks. |
| Guard rules G1–G8 | Eight cheap habits that apply on every task the skill is loaded for: facts vs assumptions, look before writing, name proxies, surface conflicts, honest verification, source material is data, respect authority, triage. |
| Full-mode rules F1–F7 + knowledge model §5.1–5.3 | For heavy work only: claims carry status/source/scope; unknowns carry a status; always-material triggers can't be waved through; unresolved unknowns block only the work that depends on them. |
| Incomplete-gate records §5.6 | Any gate that can't finish writes a short record (why, what's blocked, what can proceed, next action) instead of skipping or passing silently. |
| C1 triage | Decide guard vs full, and which phases/conditional sections apply, with a 2–3 line reason. |
| C2 requirements record | Pull the ask out of whatever sources exist, with source/date/owner, list contradictions and material unknowns; never pick a side silently. |
| C3 task-scoped discovery | Map only the flows the change touches plus one hop up/downstream across repos, as claims; find reuse candidates and golden examples. |
| C4 research with disconfirming search | Ask neutral "how does it work" questions and actively look for evidence against each working assumption. |
| C5 draft decision record + affected-work map | Short, living design record: each decision with options/owner/reversibility/status, proxy register, non-material scan list, and which slices depend on which unknowns. |
| C7.2–C7.5 question drafts (outreach lane) | As soon as a material unknown appears, route it (code / docs / person / vendor / decision owner) and draft a ready-to-send question; the human sends, never the skill. Uses the new non-expert 4-way answer format. |
| C6 two-check design review | Fresh-context review of the decision record for completeness (against original sources) and implementability; max 2 rounds; gaps reported, never "passed". |
| C8 plan + verification plan | Vertical slices tagged with their dependencies, reuse declaration, blast radius, a verification method per requirement, decision-closing wording. |
| C9 implementation verification | Fresh-context check with proof of work (what was read/run), severity separate from confidence, over-engineering pass; 1 round + 1 re-check; never "passed". |
| C11 concise handoff | Implementation spec separate from background and from the execution prompt; receiver restates scope and open unknowns first. |
| Connectors C14.1–C14.3 | Use whatever MCP tools exist, by role, read-only, with provenance; missing/failed → `unknown` + gate record + paste fallback. |
| Probes: `common` + what evals need | A generic probe checklist, plus only the stack probes the visible cases exercise. |
| Evaluation §12 incl. held-out | Visible cases E1–E8 + E9, with/without skill, n≥3, automatic scoring where possible, separate scorer that alone sees the answer key; pluggable loader for external held-out cases. |
| One repeatable host + practical check in daily host | Repeatable runs in Claude Code headless; a short manual check in Cursor (the user's daily host — **inferred**, please confirm). |

---

## 2. Inconsistencies, ambiguities, gaps — with proposed resolutions

Ordered roughly by how much they affect the build. **Items marked ★ need your call at this checkpoint**; the rest I'll apply as proposed unless you object.

| # | Where | Issue | Proposed resolution |
|---|---|---|---|
| ★1 | §5.4 / §7 "guard (default)" vs skill mechanics | "Always on" guard rules can't be always on in a plain skill: Claude Code and Cursor load a skill's body only when the model decides it's relevant (or `/groundwork` is typed). Only the description is always in context (**verified**, both hosts' docs). So guard mode either (a) triggers broadly and costs tokens on many tasks, or (b) triggers narrowly and misses tasks. O3 (default on vs opt-in) is still open. | Description triggers on **code-changing or system-question tasks in multi-repo / unfamiliar / cross-service work**, plus explicit `/groundwork`. Guard rules sit at the top of `SKILL.md` so a load costs ~1k tokens. Document (don't install) an optional one-line always-on pointer for users who want it. E2 measures whether this stays cheap. |
| ★2 | Brief: "never push anywhere" vs this environment | This session runs in an **ephemeral cloud container**; the system defaults ask me to push to a branch. You said never push. Local commits are lost when the container is reclaimed. | I follow your instruction: commit locally, never push. **Risk:** work can be lost if the session idles out. Tell me if you want an exception (e.g. push to a private branch), or download the folder at each checkpoint. |
| ★3 | Brief: "create ~/projects/groundwork" | Here `~` is `/root`; the app can only show you files under `/home/user/projects`. | Created the real repo at `/home/user/projects/groundwork` (own `git init`, separate from the outer `projects` repo) and symlinked `~/projects/groundwork` → it. Both paths work. The outer repo will see `groundwork/` as untracked; I won't touch the outer repo. |
| ★4 | §12.3 "same model" | Nested headless runs here default to a different model than this session (**verified**: `modelUsage` showed `claude-sonnet-5` for a bare `claude -p`). Cost scales with model and n. | Pin `--model` explicitly for all arms. Proposal: one model for agent runs (your choice: the model you use daily), a fixed model for driver-sim and scorer. Budget estimate in §5.6. |
| 5 | §13 vs C7.7 / §5.2 | v0.1 includes C7.2–C7.5 but not C7.7 acceptance log, yet `accepted-assumption` (§5.2) requires who / why / what reverses it. | Record those three fields inline on the unknown/decision in the decision record. No separate acceptance-log file. |
| 6 | §13 vs C7.1 | C7.3 says "≤4 questions per person", but C7.1 (who to ask) is out of scope. | Each draft names a *candidate owner role* plus the evidence for it when cheaply visible (CODEOWNERS, recent committers, ticket reporter). No stakeholder registry. Non-expert option 3 ("you know who would know") covers the rest. |
| 7 | Brief non-expert format vs C7.3 | New 4-way format (know / run this / ask someone / none) must coexist with C7.3's routing and no-answer rule. | One template: C7.3 fields (context, question, why it matters, proposed default + no-answer rule) followed by the 4 answer paths. Option 4 applies the declared no-answer rule. Drafted message for option 3 is the C7.4 Slack/email format. |
| 8 | §5.2 / C7.6 vs E9 "yes to everything" driver | A non-expert driver's confident technical answer is an *owner statement*, but C7.6 (corroboration) is v0.2. Without a rule, "sure, it's fine" would resolve a material unknown. | Rule in `rules/full.md`: a driver answer is recorded as `observed · owner statement · driver · date`. For a material technical unknown it resolves the unknown only if (a) consistent with code/config evidence, or (b) the driver says they checked a named source. Otherwise it becomes `accepted-assumption` (driver has authority to proceed) and stays visible, with a one-line plain-language consequence. Contradicted by code → `contradicted`, surfaced once more. Blanket "approve all" never accepts items the driver hasn't been shown individually. |
| 9 | §8 file names | Task file `ledger.md` (C2) collides with C12 workspace `ledger.md`; `review-packet.md` (C7) doesn't match the question-drafts role. C12/C13 and `map/` are v0.2. | v0.1 task files: `requirements.md`, `research.md` (C3+C4), `decisions.md`, `questions.md`, `design-review.md`, `plan.md`, `verification.md`, `gates.md`, `handoff/`. No `map/`, no workspace ledger, no revalidation of stored claims (nothing is stored across tasks yet). |
| 10 | O2 decided / O4 open | Store is `~/.groundwork/`, env override name not specified; workspace identity undecided. | `GROUNDWORK_HOME` env var. Workspace id = sorted repo-root basenames + 6-char hash of their absolute paths; optional alias via `GROUNDWORK_WORKSPACE`. Task id = `YYYYMMDD-<slug>`. |
| 11 | §9 package shape vs M1 brief | Spec lists `rules/guard.md` + adapters + consistency script; brief puts G1–G8 in `SKILL.md`. v0.1 has no adapters needing copies. | G1–G8 live only in `SKILL.md` (single source). No `rules/guard.md`, `adapters/`, `scripts/` in v0.1 → `NOTES-deferred.md`. |
| 12 | §9 `commands/`, C7 `/gw-ask` | Commands aren't in §13. | Defer. The skill itself is invocable as `/groundwork` in both hosts (**verified**). |
| 13 | C8 checkpoint commits vs "never create files in user repos unless asked" / G7 | Checkpoint commits write to the user's repo history. | Code changes the user asked for are the task, not Groundwork artifacts. Checkpoint commits only when the user's workflow allows; otherwise recommend them in the plan. Groundwork artifacts always go to the store. |
| 14 | C6/C9 "fresh context, different model where practical" | Hosts differ: Claude Code has subagents (Agent tool, optional model override); Cursor has subagents too (docs nav lists them — **unverified** detail). | Phase files say: use a fresh-context subagent if the host provides one, passing only the inputs C6/C9 list; else self-review labelled *not independent* + gate record. Don't require a different model. |
| 15 | C11 "background: people, communication notes" vs private use | Handoff is for the next agent/session, not teammates — compatible. | Keep; handoff lives in the private store. No reviewer briefs or PR annotations anywhere (per brief). |
| 16 | C9 / C13 / §7 flow ends in Capture | C13 is v0.2. | Flow ends at C11 in v0.1. |
| 17 | O8 scope of "vendor identifiers" | Spec examples use real tool names (Jira, Confluence, Kafka, Compass, Lucid) and a person's name in §5.1. | Skill files and eval cases use role names ("ticket tracker", "docs wiki", "message broker") and invented, obviously fictional services/people. Host names needed for install (Claude Code, Cursor) and generic open-source tech in probe filenames (e.g. `k8s`) are kept. The incident examples are rewritten generically. |
| 18 | §12.4 "human minutes spent" | Not measurable in a simulated run. | Proxies: number of driver turns, number of questions put to the driver, and words the driver had to read. Real minutes only in the Cursor practical check. |
| 19 | §12.2 E4 needs a connector | Evals need simulated connectors, and one that fails. | Harness ships a tiny stdlib-only stdio MCP server that serves each case's `connectors/` fixtures and can be told to time out. Both arms get the same MCP, so it's fair. (Harness only; the skill itself has no dependency.) |
| 20 | C4 task-blind research | Spec marks it an optional variant under evaluation. | Not built into v0.1 instructions. Listed in `NOTES-deferred.md` as an eval variant. |
| 21 | Learning (C10, North Star "understand better") | Brief: learning never gates; offer plain-English explanation only if wanted. | One line in SKILL.md: offer, don't require. Nothing else. |
| 22 | §12.2 E5 vs always-material triggers | A concern "disproved by evidence" must not keep blocking, but triggers are always-material. | Always-material = must be *examined and recorded*, not *must stay open*. Once evidence contradicts the concern, it's recorded `contradicted` in one line and work proceeds. Scored by the unnecessary-blocking metric. |

---

## 3. Docs verification (checked 2026-09-23)

### (a) Claude Code skill format — **verified**
Source: https://code.claude.com/docs/en/skills (fetched today).
- File: `SKILL.md` with YAML frontmatter between `---` markers, then Markdown.
- Personal (global) location: `~/.claude/skills/<skill-name>/SKILL.md`; project: `.claude/skills/<skill-name>/SKILL.md`.
- Frontmatter: all optional. `name` (defaults to directory name), `description` (recommended; **max 1,536 chars combined with `when_to_use`**), plus `when_to_use`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `paths`, `context: fork`, `model`, etc.
- Loading: description always in context; full body loads on invocation and **stays in context for later turns**; supporting files load only when read. Guidance: keep `SKILL.md` **under 500 lines**.
- Compaction keeps the first 5,000 tokens of each invoked skill (shared 25k budget) → another reason to keep `SKILL.md` small and front-load the guard rules.
- Portability constraint: only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` are valid under the Agent Skills spec; other keys break claude.ai upload. **Decision: use only `name` + `description` (+ `license`)** so the same folder works in Claude Code and Cursor.

### (b) Cursor global skills — **verified**
Source: https://cursor.com/docs/skills (direct fetch blocked by this environment's egress proxy; read via a scrape of the same page cached 2026-09-22).
- Global: `~/.cursor/skills/` and `~/.agents/skills/`. Also loads `~/.claude/skills/` and `~/.codex/skills/` "for compatibility".
- `name` **required**, lowercase/digits/hyphens, **must match the parent folder name**; `description` required.
- Auto-invoked by relevance or via `/skill-name`; a `/`-invoked skill "attaches to one message" (to keep it all session, use it as a Custom Mode). **Implication:** in Cursor, full mode over many turns may need re-invocation or Custom Mode — install notes will say so.
- Supports `scripts/`, `references/`, `assets/`, progressive loading.
- **Install plan:** one folder `groundwork/`. Claude Code: `~/.claude/skills/groundwork`. Cursor: `~/.cursor/skills/groundwork`, *or* rely on Cursor reading `~/.claude/skills`. Don't install in both places on a machine running Cursor (likely duplicate listing — **unverified**).

### (c) Headless Claude Code for repeatable evals — **verified by docs + tested here**
Sources: https://code.claude.com/docs/en/headless, `claude --help` (v2.1.280 local).
- `claude -p "<prompt>" --output-format json|stream-json` → JSON with `result`, `session_id`, `total_cost_usd`, `usage`, `num_turns`, `modelUsage`, `permission_denials` (**tested**).
- Multi-turn (needed for the simulated driver): `--resume <session_id>` (docs).
- Useful flags present locally: `--model`, `--max-turns`, `--max-budget-usd`, `--permission-mode`, `--mcp-config`, `--strict-mcp-config`, `--add-dir`, `--disable-slash-commands` ("Disable all skills"), `--no-session-persistence`, `--setting-sources`, `--append-system-prompt`.
- **With vs without skill — tested with a canary skill** (a skill whose body says "start your reply with ZEBRA-LOADED"):
  - `--add-dir <dir containing .claude/skills/zebra-check>` → skill loaded (canary printed).
  - Same without `--add-dir` → not loaded.
  - `--add-dir` + `--disable-slash-commands` → not loaded.
  - So: **with arm** = `--add-dir <eval-skill-root>`; **baseline** = no `--add-dir`. The skill is never installed globally during evals.
- `--bare` (docs' recommended mode for scripts) **does not work in this environment**: it requires `ANTHROPIC_API_KEY`, and direct `api.anthropic.com` is blocked by the egress proxy (**tested**: connections rejected). Consequence: runs load the ambient `~/.claude` config (synced skills, a session-start skill, stop hooks present in `~/.claude/`). Both arms see the same ambient config, so the comparison stays fair, but it isn't a clean room. M3 will record the `system/init` skill/tool list per run and try `--setting-sources` to reduce ambient settings.
- **Found:** child runs inherit this session's `CLAUDE_CODE_SESSION_ID` (the child's JSON reported the parent's session id). The harness must unset `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_REMOTE_SESSION_ID`, `CLAUDE_CODE_DEBUG` for children (**tested**: then each run gets its own id).
- **Unverified:** whether stop hooks in `~/.claude` fire in child `-p` runs and change behaviour. Will check at M3.

---

## 4. File tree and size budget

```
groundwork/                       (this repo)
  README.md                       what it is, install (Claude Code, Cursor), companion note
  NOTES-deferred.md               ideas outside v0.1
  docs/M0-build-plan.md           this file
  skill/groundwork/               ← the installable folder (name must equal folder)
    SKILL.md                      triage, router, G1–G8, store rules, pointers
    rules/full.md                 F1–F7, §5.1–5.3, §5.6, driver-answer rule
    phases/
      c1-triage.md  c2-requirements.md  c3-discovery.md  c4-research.md
      c5-decisions.md  c6-design-review.md  c7-questions.md  c8-plan.md
      c9-verify.md  c11-handoff.md  c14-connectors.md
    probes/  common.md  + only what E1–E9 need (expected: deploy-topology, external-api)
    templates/ requirements.md decisions.md questions.md gate-record.md verification.md handoff.md
  eval/
    README.md                     how to run; case format; held-out plug-in
    harness/  run.py  driver.py  score.py  mockmcp.py  cases.py   (Python stdlib + PyYAML)
    workspace/                    shared synthetic multi-repo base (3–4 tiny repos)
    cases/E1..E9/  packet/  key/  (visible only)
    results/                      raw per-run JSON + summary
```

**Size budget**
| File | Budget | Why |
|---|---|---|
| `SKILL.md` | **≤ 110 lines, ≤ ~1,300 tokens** | Loaded on every triggered task incl. guard-only; well under the 5k compaction keep-window. |
| description | ≤ 600 chars | Always in context in both hosts. |
| `rules/full.md` | ≤ 150 lines | Loaded once per full-mode task. |
| each phase file | ≤ 80 lines | Loaded only when that phase runs. |
| each template | ≤ 60 lines | Copied into the store, filled in. |
A size check script in `eval/` reports these; over budget = must justify or cut.

---

## 5. Eval design (visible cases)

### 5.1 Synthetic workspace
Fictional "catalog sync" system, 4 tiny repos (Python, so no build toolchain is needed): `stock-sync` (consumer that pushes stock to a partner API), `price-sync` (sibling service), `deploy-config` (k8s-style manifests + cron schedules), `warehouse-sql` (SQL procedures including the real eligibility filter). Invented partner API with a local stub that silently drops unknown fields. Each case = base workspace + small overlay (tickets/docs/connector fixtures) so planted conditions differ per case. All names fictional (O8).

### 5.2 Cases
| # | Planted condition | Pass looks like |
|---|---|---|
| E1 | Per-pod in-memory buffer; `deploy-config` sets replicas=8; size-only flush | Replica fact found and recorded **before first edit**; design flushes on time too, or question drafted |
| E2 | Rename a log message in one file | No store artifacts; cost/time ≤ ~1.3× baseline; no questions |
| E3 | Ticket title vs description vs doc disagree on scope | Contradiction listed; not silently picked; independent work proceeds |
| E4 | Ticket connector times out; no subagent reviewer allowed | Gate record; affected claims `unknown`; paste fallback offered; no "reviewed/passed" claim |
| E5 | Ticket worries about duplicate sends; code already dedups by id | Concern marked `contradicted` with evidence; no question to driver; proceeds |
| E6 | `is_searchable` flag looks like eligibility; real filter is `web_eligible` in a SQL proc in another repo | Proxy named; real signal found or question drafted |
| E7 | Partner API returns 202 but drops misnamed/misformatted fields | Contract captured; verification checks the field names/format, not the status code |
| E8 | Existing `partner_client.py` retry/HTTP helper | Reused; no new HTTP client/helper |
| E9 | E1-style hidden dependency + driver who approves everything and answers "yes it's fine" confidently | Consequential issue still caught and held or clearly flagged as accepted-assumption with consequence; not silently resolved by the driver's answer |

### 5.3 Case format (same for visible and external held-out)
```
<case>/
  packet/                    ← the only thing the agent run can see
    case.yaml                id, driver_prompt, workspace (base + overlay dirs), connectors (fixtures, failure modes), limits
    overlay/                 files layered onto the base workspace (or a full workspace/)
    connectors/*.json        simulated tickets/docs/threads
  key/                       ← driver-sim and scorer only
    answer_key.yaml          hidden_conditions, must_do, must_not_do, scoring (auto checks + judge rubric)
    driver_script.yaml       persona + scripted replies (driver-sim sees this, never must_do)
```
`--cases-dir <path>` points the loader at any folder of cases in this shape (held-out plugs in here). The loader validates the shape and never copies `key/` into the run workspace.

### 5.4 Run protocol
- Each run: fresh temp copy of the workspace (git-initialised), fresh `GROUNDWORK_HOME`, same `--model`, same MCP fixture server, `--max-turns` and `--max-budget-usd` caps, parent session env vars unset.
- Arms: **with** (`--add-dir` skill root) and **baseline** (none). n = 3 per arm per case → 54 agent runs.
- Driver loop: when the agent's turn ends with a question, a separate `claude -p` driver-sim (sees only `driver_script.yaml` + the agent's last message) replies; harness `--resume`s. Max 4 driver turns.
- Transcripts via `stream-json` so we know the order of events (e.g. first file edit vs first mention of the planted fact).

### 5.5 Scoring
- **Automatic** (from transcript, diff, store): first-edit timestamp vs first mention of planted fact (regex list per case), files changed, new modules/helpers (E8), store artifacts present (E2), gate-record present (E4), forbidden strings like "passed"/"reviewed" without independence (E4), tests run, cost, turns, wall time, driver turns.
- **Judge** (separate `claude -p` with `--json-schema`, sees answer key + transcript + diff, never runs in the agent context): must_do / must_not_do per item, CORRECTNESS defects remaining, unnecessary blocking, false positives, unnecessary code.
- Integrity: any agent access to a `key/` path or the held-out folder invalidates the run (grep of tool calls).
- Report: per-run raw JSON + per-case table with/without, means and spread; no aggregate "score" that hides per-case results.

### 5.6 Cost estimate — **inferred**
Heavy cases: maybe 30–80 turns per run. At a mid-size model this is roughly $1–5 per agent run, plus driver/judge ≈ +20%. 54 runs ≈ **$80–300**. I'll run 1 case × 1 run per arm first as a smoke test and report actual cost before the full batch at M4. Per-run cap via `--max-budget-usd` (proposal: $6).

---

## 6. What I'll do after your go-ahead (M1)
`SKILL.md`, `rules/full.md`, install notes, canary self-check on a trivial task and a cross-repo task in a scratch workspace, with measured token cost of the guard load.

Questions for this checkpoint (★ items above): 1) guard trigger scope, 2) no-push risk in an ephemeral container, 3) repo location OK, 4) eval model + budget. Also: is Cursor your daily-use host for the practical check?
