# Probe: common (every full-mode task)

Answer each item for the touched flow + one hop, across **all** repos in the workspace.
Record answers as claims (`[status · source · scope]`); "not found" is an answer too.
Search by the concept, not just the symbol: field names, topic/queue/table names, env
var names, and string literals, across repos (`grep -rn`, or a code-search tool).

1. **Data movement** — what enters and leaves the touched code: topics/queues, HTTP/RPC
   calls, tables, files, events. Who produces each input, who consumes each output
   (search other repos for the same name).
2. **Deploy topology and per-instance state** — how many instances run (per environment),
   and what each keeps in memory (buffers, caches, counters, locks). In-memory state +
   more than one instance is always material. Stack detail: `probes/deploy-topology.md`.
3. **Schedules and timing** — cron/scheduled jobs, batch or publish jobs, TTLs, flush
   intervals, and when data becomes visible downstream.
4. **Filters, flags, eligibility** — what decides whether an item is processed or sent.
   Look beyond the service: SQL views/procedures, upstream jobs, config lists, feature
   flags. If two places decide the same concept with different signals, that's a proxy
   mismatch (G3).
5. **Contracts and silent failure** — every external or cross-service contract touched:
   field names, formats, required/optional, and what happens on a wrong value (error vs
   silently ignored). Stack detail: `probes/external-api.md`.
6. **Env profiles and secrets** — per-environment config, flag defaults, prod identifiers
   reachable from lower environments, secrets in code/config/logs (report location, never
   the value).
7. **Build, test, lint, CI** — the commands each touched repo uses (README, Makefile,
   package files, CI config), and whether they run here.
8. **Reuse and golden examples** — existing clients, helpers, retry/HTTP/serialization
   utilities and patterns that already do part of the job; the 1–3 closest existing
   implementations to copy the shape of.
