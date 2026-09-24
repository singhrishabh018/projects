# Phase-files proposal (2026-09-24) — do not implement yet

Triggered by: 0 phase-file reads in **15 loaded full-mode runs** now (M2: 7 runs; E1 smoke:
1; Stage 1: E2b/E6/E7/E9, 7 with-arm runs). Every one of those runs read `SKILL.md` and
nothing else. The question asked: is the honest answer "almost nothing in the phase files is
unique"? **No.** Most phase files carry real content that lives nowhere else. The problem is
narrower and worse: **content that matters is stranded in files nobody opens.**

## 1. What's NOT already covered, file by file

"Covered" means: stated in SKILL.md, or conveyed by a template's field names/structure alone
(a template can teach shape without prose). ★ = load-bearing — cutting it silently would
remove a real capability, not just a reminder.

| File | Lines | Already covered by SKILL.md/templates | **Not covered — real, unique content** |
|---|---|---|---|
| **c1-triage.md** | 36 | Trigger list (verbatim in SKILL.md); phase sequence 1–11 (verbatim in SKILL.md); task-folder path/workspace-id formula (verbatim in SKILL.md) | Failure-model / volume-math triage rule (when each applies) — **nowhere else**. Skip-condition examples (minor, derivable). |
| **c2-requirements.md** | 34 | Source/requirement/contradiction/superseded fields (template table columns); "don't resolve silently" (G4) | "Recency/authority is a suggestion, not a resolution" — real nuance, not stated elsewhere. "The agent never narrows scope on its own" — stated once more, verbatim, in c5. |
| **★ c3-discovery.md** | 41 | "One hop out" scope (SKILL.md phase-list line); G2/G3 in one sentence each | **The claim format itself**: `[status · source · scope]`, the 4 statuses, the 6 source types. **This is the entire evidence model (§5.1) and it currently has no other home.** **Proxy recording format** (`proxy: X used as Y at file:line`) + the cross-repo mismatch-check technique — this is literally what caught E6. Golden-examples/reuse listing format (minor). Claim revalidation note (minor). |
| **★ c4-research.md** | 26 | Nothing | **All of it is unique**: the neutral-question technique with examples (the P5 fix — "what decides", not "where do I edit"), and the disconfirming-search structure (assumption / would-be-wrong-if / searched / found). Nothing else in the skill teaches either technique. |
| **c5-decisions.md** | 41 | Decision fields (template, near-verbatim); failure-model/volume-math placeholders (template) | Owner rule (which decisions need no question) — real, ~2 lines. Per-slice implementability gate ("supported, decided, or accepted-assumption") — real, ~1 line. "Non-material scan list ≠ naming/formatting" — real, ~1 line. Affected-work map's *purpose* explanation is now largely redundant with SKILL.md's own pre-edit-check line. |
| **★ c6-design-review.md** | 32 | "Self-review, labelled not independent" (gate-record template, verification template); "never say passed" (G5) | **The completeness-vs-implementability distinction itself** — not stated anywhere else. **The fresh-context subagent's exact prompt** ("list material gaps only... do not propose extra features") — without it, nobody knows what to tell the subagent. **The "max 2 rounds" budget number** — a decided project policy (§5, O5), currently written down nowhere else. |
| **★ c7-questions.md** | 49 | ~80% of the question *shape* is already duplicated verbatim in SKILL.md ("Asking the user") | **Routing table** (code→research, docs→lookup, person→draft) — unique. **"Option 2 = exact step, not 'check the config'"** — the specific negative example that fixed an M1 defect; not elsewhere. **Option 3 = owner role + evidence (CODEOWNERS, git blame, ticket reporter)** — unique. **≤4 questions per person** — unique number. **"Draft-only, the skill drafts, the user sends"** — a decided project policy (O10) that currently has **no other home at all**. **"Routing ≠ unblocking"** — unique, prevents an agent treating "I asked" as license to proceed. |
| **★ c8-plan.md** | 44 | Nothing structural (no template for `plan.md`) | Blast-radius definition. **"No speculative extras (rate limiters, caches, persistence, config knobs) without a requirement or failure-model reason"** — the actual anti-over-engineering rule (P15); SKILL.md's G2 only covers reuse, not this. "Tests derived from requirements/decisions, not the implementation" + "assert on what the other side accepts, not a status code" — the P26/E7 fix, stated generally (the external-api probe has a narrower version, and that probe is even less likely to be read than C3). **The decision-closing wording itself** (`"Decided X because Y. If evidence shows Y is false, stop and report."`) — referenced by c11/handoff's template but *defined* only here. |
| **★ c9-verify.md** | 40 | Proof-of-work fields, review-scope fields, findings/severity columns (verification template) | **The 6-item verification checklist** (decision conformance, requirement coverage against C2 not only C5, contract conformance, convention match, cross-repo consistency, env safety, hygiene) — real, specific, not templated anywhere. Hypothesis mode — entirely unique, a real capability. Over-engineering pass pointer. **"1 round + 1 re-check" budget** — a decided policy (O5), written nowhere else. |
| **c11-handoff.md** | 20 | ~90% conveyed by `templates/handoff.md` (three-file split, GW-MARKER, restate-on-receipt) | The reconciliation discipline ("one blocker list, superseded removed, no append-only history, no 'don't relitigate X' lines") — real, not in the template. "Then run C6 on spec.md" — a sequencing pointer. |
| **★ c14-connectors.md** | 35 | Connector-failure default (gate-record template, partially) | **The roles table itself** (tickets/docs/conversations/meetings/diagrams/ownership/code-intel/runtime → which phase uses each) — the only place this mapping exists. Provenance fields, secret-redaction wording, "retry once then mark unknown" — real specifics. |

**Bottom line:** C3, C4, C6, C7, C8, C9 and C14 each carry genuinely unique, load-bearing
content — several of them decided project policies (the 2-round and 1-round-plus-re-check
review budgets, draft-only outreach) that right now live *only* in a file with a measured
**0% read rate**. C1, C2, C5 and C11 are 60–90% duplicated by SKILL.md or their own
templates and are the real candidates for a clean cut.

## 2. What a merged SKILL.md would look like

Two options, not one — the size cost differs a lot.

### Option A — merge only what's genuinely irreplaceable (targeted)

Add to SKILL.md, keep everything else in phase files (accepting they may still go unread,
but now for detail rather than for things that must never be missed):

- **Claim format** (from C3): one line — `[status · source · scope]`; status =
  observed/inferred/unknown/contradicted; source = code/config/docs/runtime/owner
  statement/vendor statement. (+3 lines)
- **Proxy technique** (from C3): the recording format + "check whether another repo decides
  the same concept with a different signal." (+2 lines)
- **Neutral-question + disconfirming-search technique** (from C4), compressed to the pattern
  without the worked example. (+4 lines)
- **Design-review two-check + budget** (from C6): completeness vs implementability, one line
  each; "max 2 rounds, stop at 1 if no gaps." (+3 lines)
- **Subagent review prompt** (from C6/C9, shared): the exact instruction text to hand a
  fresh-context reviewer. (+3 lines)
- **Question routing + draft-only + ≤4/person** (from C7): condensed to a short list; option
  2/3 specifics folded into the existing "Asking the user" block. (+5 lines)
- **Anti-speculative-extras rule + decision-closing wording** (from C8). (+3 lines)
- **9-item verification checklist + hypothesis mode + "1 round + 1 re-check"** (from C9),
  condensed to a list. (+5 lines)
- **Connector roles table** (from C14), condensed to one line per role. (+5 lines)
- **Reconciliation discipline** (from C11). (+2 lines)

**Net addition: roughly +35–40 lines** (the numbers above are lines added, already netting
out overlap with existing SKILL.md text). C1, C2, C5, C11 are deleted outright (their
few unique lines are folded into the additions above or into their templates). C3, C4, C6,
C7, C8, C9, C14 stay as separate files, now covering *depth and detail* rather than
*anything essential* — so a 0% read rate on them stops being a correctness risk.

### Option B — inline everything, drop progressive loading for the build flow

If 0/15 is the real read rate, "progressive loading" isn't a design that's working for
these files — it's a design that silently drops content. The harder-nosed option: fold the
*entire* unique-content column above into SKILL.md (not just the ★ rows), and keep phase
files only as an appendix an agent can consult for the full worked examples (neutral
questions, disconfirming-search worked case, etc.) — but nothing essential depends on that
appendix being opened. This is the "SKILL.md is the skill; files are optional detail" model,
matched to what's actually being measured rather than to the original progressive-loading
design.

**Net addition: roughly +130–160 lines.**

## 3. Resulting token size (estimated from M2's measured ratio: 118 lines ≈ 2.27k tokens ≈ 19 tokens/line)

| | Lines | Estimated tokens |
|---|---|---|
| Current SKILL.md | 118 | ≈ 2.27k (measured, M2) |
| Option A (+35–40 lines) | ≈ 155 | ≈ 2.9–3.0k |
| Option B (+130–160 lines) | ≈ 250–280 | ≈ 4.7–5.3k |

M0 noted the harness keeps only the **first 5,000 tokens** of an invoked skill through
compaction (shared 25k budget across all invoked skills). Option A stays comfortably under
that. **Option B lands right at or past the 5k compaction line** — on a long full-mode
session, content added this way could itself be the first thing compaction drops, which
would be a strange way to "fix" the problem of content going unread. This is a real argument
against B unless compaction behavior is separately verified.

## 4. What we'd lose either way

- **Full worked examples.** C4's neutral-question list and disconfirming-search example,
  C3's proxy example, C9's verification-checklist prose — compressed to one-liners in either
  option lose their teaching value for an agent that's never seen the pattern before. This
  is the real cost of compression, not just line count.
- **Niche capabilities nobody has exercised yet.** Hypothesis mode (C9) and the full
  escalation/meeting-agenda question formats (C7) are narrow enough that compressing them to
  a passing mention risks them being dropped in practice even after merging — they'd need a
  real test case to know if the compressed version still works.
- **The self-documenting structure.** Right now, a human (you) can open exactly the phase
  file for the step in question and read a complete, standalone account of it. After a merge,
  that account is spread across a longer SKILL.md and the original phase file (kept for
  detail) — slightly worse for a human skimming the skill's design, better for what an agent
  actually loads.
- **Nothing is lost on C1/C2/C5/C11** beyond what's listed in §1 — those are honestly mostly
  redundant, and cutting them loses only the ~10 lines of unique content already folded into
  the estimates above.

## 5. Recommendation

**Option A**, not B: it captures everything that's a decided policy or a named,
load-bearing technique (the two review budgets, draft-only outreach, the claim format, the
proxy technique, the anti-speculative-extras rule, the verification checklist), stays well
under the compaction line, and deletes the four files that were genuinely redundant (C1, C2,
C5, C11). It does **not** pretend the remaining phase files (C3, C4, C6, C7, C8, C9, C14)
are still "the skill's real content" in the way the original progressive-loading design
assumed — after Option A, they're detail and worked examples, not load-bearing rules. If a
later eval shows an unread phase file still hides something that matters, that's the signal
to promote it into SKILL.md too, one line at a time, the same way this fix promoted the
pre-edit check.

**Not implemented.** This is the proposal only, per the instruction to stop before Stage 2.
