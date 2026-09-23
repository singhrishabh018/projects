# C3 — System discovery (task-scoped)

Purpose: learn how the part of the system this change touches actually works, across
repos, with evidence.

## Scope

The flows the change touches, **plus one hop upstream and downstream**, across every repo
in the workspace, not only the repos being changed. Producers, consumers, callers, deploy
config, schedules, filters and data definitions often live in other repos.

## Steps

1. Run `probes/common.md`. Add a stack probe from `probes/` when the task touches that
   stack (deploy config, external API, ...). Use a code-search or code-graph tool if the host
   has one; record its results as claims like any other.
2. Record each material finding as a claim in `research.md`:
   `[status · source · scope] statement`, with scope = repo@commit (`git rev-parse --short HEAD`)
   and date. Status: `observed` · `inferred` · `unknown` · `contradicted`. Source: code ·
   config/manifest · documentation · runtime observation · owner statement · vendor
   statement. A citation proves what its source says, nothing more: config and code show
   what is *configured* or *written*, not what runs; a doc shows what the page says.
3. For every always-material trigger you find, record it, even if it turns out harmless.
4. **Proxies (G3):** when code uses a field/flag/attribute to stand for a concept, record
   `proxy: <X> used as <concept Y> at <file:line>` and look for other places that decide the
   same concept with a *different* signal (sibling services, SQL, jobs, docs). A mismatch
   is a material unknown.
5. **Reuse and conventions:** list reuse candidates (existing clients, helpers, patterns)
   and 1–3 golden examples (closest existing implementations) with paths.
6. Note how to build, test and lint each touched repo (commands, where found).
7. Claims from earlier tasks are re-checked against their source before being relied on.

## Output

`research.md` sections: Claims · Always-material findings · Proxies · Reuse candidates and
golden examples · Commands. Keep it to facts; decisions go in C5.

## Gate

Every material claim has status, source and scope; every always-material trigger found is
recorded; unknowns that matter are in `requirements.md` → Material unknowns.
