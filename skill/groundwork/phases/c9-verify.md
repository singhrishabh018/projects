# C9 — Implementation verification

Purpose: the builder doesn't certify its own work.

## Reviewer

A **fresh-context subagent** if the host has one. Give it: the original sources and
`requirements.md`, `decisions.md`, `plan.md`, the diff, and repo access. Not your
reasoning. Otherwise self-review, labelled **not independent**, with a gate record.

## The review must include

1. **Proof of work**: git state per repo (branch, HEAD, `git status --short`), files
   actually read, commands actually run with their output (tail). Anything not run is
   listed as not run.
2. **Review scope**: changed files · unchanged dependencies examined (callers, consumers,
   config, deploy overrides, schedules) · material exclusions and why.
3. **Checks**: decision conformance · requirement coverage against C2 (not only C5) ·
   contract conformance · convention match against the golden examples · regression and
   blast radius · cross-repo consistency of shared decisions (same concept, same signal) ·
   env safety (flags default off where required, no prod identifiers in lower envs, no
   secrets in code/config/logs) · traceability and git hygiene.
4. **Findings**, each with severity `CORRECTNESS` · `HARDENING` · `DEFER` and, separately,
   confidence (F4). Judge severity against the requirements and failure model.
   Every conclusion links to a finding; no summary claims without one.
5. **Over-engineering pass**: what can be removed or simplified. Delegate to a minimalism
   review skill if one is installed.
6. **Hypothesis mode**: if the user or another agent gives a hypothesis, answer
   `observed` · `inferred` · `unknown` · `contradicted` with evidence, and flag any
   reversal of an earlier conclusion.

## Budget and result

One full round, fix, then one re-check of the fixes. Then report what's left. The result
is never "passed": it's a list of what was checked, what was found, what's fixed, what
remains, and whether the review was independent.

## Output

`verification.md` (template: `templates/verification.md`).
