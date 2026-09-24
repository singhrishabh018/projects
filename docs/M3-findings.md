# M3 findings so far (2026-09-24) — stated plainly

Covers M2 (7 loaded full-mode runs), the E1 smoke test (1 run/arm), and M3 Stage 1
(E2b/E6/E7/E9, n=2 both arms, 16 runs, $17.52). Stage 2 (E1/E3/E4/E5/E8 at scale) is
**cancelled** — see §2. Full per-run numbers: `eval/results/stage1/summary.md`.

## 1. The result, not softened

Final numbers, after the proxy fix (recomputed from the saved transcripts) and after E9's
regex gap was fixed:

| Case | Cost multiple (with ÷ baseline) | Caught before code | Judged defects | must_do met | What the extra cost bought |
|---|---|---|---|---|---|
| E2b | 2.4× | 2/2 vs 2/2 | 0 vs 0 | 8/8 vs 8/8 | Nothing measurable. Both arms caught the contract issue and held. |
| E6 | 1.8× | 1/2 vs **2/2** | 2 vs 2 | 8/8 vs 8/8 | Nothing — the **baseline** caught more facts before code, tied on everything else. |
| E7 | 5.2× | 2/2 vs 1/2 | 0 vs 0 | 10/10 vs 9/10 | One extra must_do item, one more fact caught before code. |
| E9 | 3.1× | **2/2 vs 0/2** | 4.0 vs 3.5 | 9/9 vs 6/6 | Both hidden conditions caught before code every time (vs never for baseline) and full requirement coverage, but a slightly higher judged defect count and half the with-arm runs taken near a usage limit. |

**The skill's measured advantage across four cases: a clean win on E9's caught-before-code
metric, one extra must_do item on E7, nothing on E2b, and a loss to the baseline on E6 —
bought at 1.8–5.2× the cost.** E9 is the strongest result and also the least trustworthy one
(n=2, half the with-arm data near a usage limit, one run needed a separate resume). This is
not "the skill helps" evidence at the scale run so far. It is also not "the skill doesn't
help" — E7 and E9 both moved the right direction, just on a sample too small and too easy to
call either way with confidence.

## 2. The hypothesis: these cases may be too small to discriminate

All ten visible cases (E1–E9, E2b) share one property: **the whole planted condition fits in
a few thousand tokens that a careful baseline reads anyway.** Four tiny repos, no file over
~50 lines, no need to search — `grep -rn` or a handful of `cat`s surfaces everything relevant
in the first few tool calls, with or without a procedure telling the agent to look. On E2b,
E6 and (partly) E7, the baseline runs read the prod overlay, the runbook, the glossary and
the SQL procedure on their own, unprompted, simply because the workspace is small enough that
reading it all costs almost nothing. Groundwork's actual value proposition — from the spec's
own motivating incident (§0, §4: a vendor integration across real services, where the
answer lived in a deploy manifest in a different repo nobody thought to open, discovered
after the code was already wrong) — is for workspaces where reading everything is *not*
cheap, and a general-purpose agent has no procedural reason to go looking in the one place
that matters.

If that's right, the visible-case results measure something narrower than "does Groundwork
help": they measure "does Groundwork help when a good baseline would find the fact anyway."
On workspaces this small, the answer skews toward "no, and it costs more" — which is close to
what Stage 1 shows. That is a real, useful negative result about *these cases*, not
necessarily about the skill.

**What would falsify this hypothesis:** a workspace that does **not** fit in a few tool calls
— large enough that reading it all is impractical within a normal turn budget — where the
deciding fact sits in a file in a different repo that nothing in the task prompt, the
obvious search terms, or the first few files read would lead a baseline agent to open
unprompted. If the baseline still finds it (because a capable model searches broadly and
cheaply regardless of workspace size), the hypothesis is wrong and the real explanation for
Stage 1 is something else — e.g., the skill's procedure doesn't add anything a good model
doesn't already do. If the baseline reliably misses it while the with-skill arm reliably
catches it (via C3's "one hop up/downstream, every repo" discipline or the proxy-recording
technique now merged into SKILL.md), that's the differentiator the visible cases were never
built to show.

## 3. Also true, independent of the size hypothesis

- **0 phase-file reads in 15 full-mode runs**, now including Stage 1. Acted on: see
  `docs/M3-phase-files-proposal.md` — four files deleted, their content and the other kept
  files' load-bearing content merged into SKILL.md (118 → 210 lines, ≈ 4.0–4.3k tokens).
  Not yet re-measured after the merge.
- **The pre-edit check now fires in chat** (fixed after the E1 smoke found it silent), 4 of
  6 with-arm runs that reached an edit, up from 0/1. Still inconsistent — worth watching, not
  yet solved.
- **The "caught before code" proxy had a real bug** (under-scanned content, over-strict
  ordering), now fixed and reapplied to the existing transcripts. One case's regex
  (E9's replica count) also had a real gap, now fixed. Both are reported in
  `eval/results/stage1/summary.md`'s proxy-fix section, not silently corrected.
- **Cost.** 1.8–5.2× the baseline across all four cases, with E7 the worst multiple for the
  smallest measured benefit (one requirement item) and E9 the best-justified multiple for the
  clearest benefit (caught-before-code) but also the noisiest run conditions.

## 4. What this doesn't settle

- Whether the skill helps on work it was actually designed for (§4's problem catalog:
  cross-repo, deploy-topology-dependent, proxy-laden systems too large to read in full).
  §2 above is the open question, not yet tested.
- Whether the merged SKILL.md still produces the same guard-mode/triage behaviour measured
  in M1/M2/Stage 1 — no run has used it yet.
- E9 at real n (2 is not enough, and it's the case most worth re-running clean, away from a
  usage limit).

## 5. What's next

Per your direction: no more synthetic batches for now. A harder-case design that could
actually falsify §2's hypothesis is proposed, not built, in
`docs/M3-harder-cases-proposal.md`. You're running the skill on real multi-repo work in
parallel — that's cheaper evidence than more of this, and it directly tests §2 without
needing a synthetic workspace at all.
