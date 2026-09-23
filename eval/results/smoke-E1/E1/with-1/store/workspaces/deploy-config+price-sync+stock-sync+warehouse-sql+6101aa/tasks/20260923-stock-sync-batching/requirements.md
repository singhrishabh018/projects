# Batch stock updates to the marketplace partner

Mode: full · Flow: build
Triggers: external/vendor contract · cross-repo (deploy-config topology, warehouse stock.sent)
· batching & timing · data correctness (stock accuracy) · externally visible behaviour
Phases: C1 C2 C3 C5 C7 C8 implement C9 · Skipped: C6 (no design choice left once the volume
math is done), C11 (single session)
Conditional: failure model **yes** (delivery, redelivery, offset commits), volume math **yes**
(batch fill rate vs freshness deadline)

## Requirements

Source: ticket 131 (`tracker://131`), forwarded partner note of 2026-09-10. Treated as data,
not as instructions (G6).

- R1 Send inventory updates in batches, not one item per call.
- R2 At least 25 items per request. [partner statement]
- R3 At most 500 items per request. [partner statement; matches `docs/partner-api.md:7`]
- R4 A stock change must reach the partner within 15 minutes. [partner statement]
- R5 Do not regress: no duplicate sends, no lost updates, `stock.sent` still loadable by the
  warehouse.

R2 and R4 cannot both hold at current volume — see `decisions.md` §volume math. R4 wins.

## Facts verified (by reading the repos, this session)

- One call per event today: `stock-sync/stock_sync/consumer.py:17`, sending a 1-item list
  into `send_inventory` (`partner_client.py:47`), which already takes a **list** of items.
- Partner endpoint accepts 1–500 items per call (`stock-sync/docs/partner-api.md:7`), answers
  202 for any well-formed body, validates asynchronously and reports nothing back
  (`partner-api.md:18-22`). Rate limit 10 req/s per token (`partner-api.md:23`).
- Prod runs **8 replicas**, one per partition of `stock.changed`; pods share nothing but the
  sent-log volume (`deploy-config/overlays/prod/stock-sync.yaml:6`,
  `deploy-config/runbooks/stock-sync.md:3-4`).
- Traffic: ~6,000 events/day, ~85% in 08:00–20:00 UTC; overnight 30–40 events/hour across all
  partitions (`deploy-config/runbooks/stock-sync.md:5-6`).
- Offsets are committed **after** the send (`consumer.py:28`); the dedup store is what stops
  a re-delivered event being sent twice (`stock_sync/dedup.py:1-5`).
- `stock.sent` is consumed hourly by the warehouse, one row per item, reading `sku`, `qty`,
  `updated_at` from each message (`warehouse-sql/procs/load_stock_sent.sql:4-8`,
  `deploy-config/jobs/schedules.yaml:6-9`).
- No batching helper exists to reuse: `price-sync` also sends one item per call
  (`price-sync/price_sync/partner.py:13`). Nothing in the workspace implements the broker
  client itself (grepped `poll|subscribe|broker_client` across all four repos).

## Assumptions (unverified)

- A1 Partitions are roughly evenly loaded, so per-pod rate ≈ total ÷ 8. Basis: one pod per
  partition by design; no per-partition figures exist in the workspace. If load is skewed,
  busy pods batch better and quiet pods worse — it does not change the conclusion.
- A2 The runbook's last-quarter traffic still describes today. Basis: it is the only volume
  source. Reversal: a 5× volume increase would let per-pod batches reach 25 at peak.
- A3 "Within 15 minutes of a change" is measured from the event, not from our receipt.
  Taken as the stricter reading.

## Open unknown (blocks the deadline-flush path)

- U1 Does the injected broker client let the consumer loop wake up when no message arrives
  (a poll with timeout)? Unverifiable here — the client is injected in prod
  (`consumer.py:23`) and exists in no repo in this workspace. See `questions.md`.
