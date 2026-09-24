# Proposal: a harder eval case — not built

Purpose: test the hypothesis in `docs/M3-findings.md` §2 — that the visible cases are too
small to discriminate because a capable baseline reads the whole workspace anyway. This case
is designed so that's no longer true. **Not implemented.**

## Design requirements (from your instructions)

1. A workspace large enough that reading it all is impractical in a normal turn budget.
2. The deciding fact sits in an unobvious file, in a different repo than the one being
   changed, that nothing in the task prompt or the obvious search terms points to directly.
3. One fact that exists **only** in a simulated person's answer — nowhere in any repo, doc,
   or connector fixture.

## Shape

**Repos:** 7–9, not 4. Mix of real work and decoys:
- 2–3 repos directly relevant to the task (one to edit, one or two adjacent services).
- 2–3 repos that are plausible-looking but irrelevant — same tech stack, similar naming,
  nothing the task needs. Their job is to cost the agent time if it searches indiscriminately,
  and to make "read everything" a genuinely bad strategy rather than just a slow one.
- 1–2 infra/ops-style repos (deploy config, a data pipeline, a migration-scripts repo) that
  look like decoys but hold the deciding fact.
- 1 repo that's the obvious place to look and is a near-miss: it has something that looks
  like the answer (a similarly-named config value, a stale comment) but isn't it — testing
  whether the agent verifies or just takes the first plausible hit.

**Size per repo:** 15–40 files, several directories deep (not everything at top level),
100–2,000 lines each. Total workspace: roughly 150–300 files, 8,000–20,000 lines. A `grep -r`
for the obvious task keywords should return real hits in the relevant repos but **not** in
the repo holding the deciding fact — that's what makes it unobvious. The deciding fact should
require either: a cross-reference from something the agent *does* read (a config key whose
value lives in another repo; a "see also" that isn't a literal filename match), or a
call/data-flow hop (the value is read from an env var whose default is set three repos away).

**The deciding fact:** e.g. a per-tenant override that changes the effective behaviour, set
in a rarely-touched ops repo's config, not mentioned in the primary repo's README, tests, or
docs, and not matching the task's obvious search terms (different naming convention on
purpose — this is itself an instance of the proxy problem the skill targets).

**The person-only fact:** something no repo would ever contain — an operational reason
("we don't do X because it broke prod twice last year"), a business rule ("that tier is
being deprecated next quarter, don't build for it"), or a pending decision ("the team is
already discussing changing this, ask before committing to an approach"). Only obtainable by
asking a person (C7); the driver-sim answers it only if the agent asks the *right* question
of the *right* role. If the agent never asks, this fact stays permanently unknown — a
legitimate outcome the scorer must accept (per SKILL.md's own no-answer defaults), not treat
as a failure to invent the fact another way.

**Answer key:** same format as existing cases (`facts`, `unknowns`, `must_do`/`must_not_do`,
`option4`, `checks`), plus one `facts` entry whose `mention_regex` can only be satisfied
after the driver reply (its `first_mention_index` should land in a `driver`-kind timeline
event or later, never before) — this makes "the agent asked and used the answer" mechanically
checkable, distinct from "the agent found it in a file."

**Driver:** scripted, holding the person-only fact behind a specific trigger (the agent must
ask about the right topic, not just "any questions?"); default reply otherwise deflects
without giving it away, so a lucky guess or an untargeted question doesn't score it.

## What "caught before code" and "premature implementation" mean here

Unchanged mechanically, but now meaningfully harder to pass by luck: the baseline has no
procedural reason to open the ops repo or ask a person, so a baseline "catch" would mean the
model's own judgment (not the workspace's small size) did the work — which is exactly the
comparison worth having.

## Cost estimate — inferred, not measured

Scaling from Stage 1's heaviest case (E9: with $1.40–1.53, baseline $0.46–0.47, 4-repo,
tens-of-files workspace) by workspace size and expected extra discovery turns (more repos to
survey, more grep/read cycles to rule out decoys, a driver round for the person-only fact):

| | Estimate per run |
|---|---|
| Baseline (may not find the ops-repo fact or think to ask; fewer turns) | $1–3 |
| With skill (systematic one-hop-per-repo discovery, routes the unknown, asks) | $4–10 |
| Judge (longer transcript, longer diff) | $0.60–1.20 |
| **Total per run** | **$6–14** |

At n=3 both arms (6 runs) for one case: **≈ $35–85**. Building 2 cases (one straightforward
version of this design, one where the deciding fact requires a two-hop trace rather than one)
at n=3: **≈ $70–170**, plus a smoke test (1 run per arm, as Stage 1 established the discipline
for) before committing to the full n. This is comparable to or larger than the original
Stage-2 estimate for five *easy* cases — each harder case buys more information per dollar if
§2's hypothesis is right, since a null result here is a real answer rather than a restatement
of "small workspace, strong baseline."

## Build cost (my time, not API cost)

Materially more than the current workspace: 150–300 files with plausible, internally
consistent content (not lorem-ipsum — the decoys have to be *genuinely* plausible or the
agent will correctly ignore them for the wrong reason) is a larger authoring job than the
current 4-repo, ~35-file workspace. Realistic estimate: a full day-equivalent of generation
and validation work per case, most of it mechanical (generating consistent decoy services)
rather than judgment-heavy.

## Open question for you, not decided here

Whether to build this as a **new synthetic workspace** (fully controlled, but authored content
risks looking synthetic in a way a model may learn to discount) or as a **redacted slice of a
real multi-repo codebase** (harder to author cleanly, but the "unobvious file" property comes
for free from a real system's actual history, and it's closer to what you're about to test
directly by using the skill on real work). Given you're already running the skill on real
work in parallel, the real-codebase route may be the better use of remaining effort here —
worth deciding after you see what actually happens there.
