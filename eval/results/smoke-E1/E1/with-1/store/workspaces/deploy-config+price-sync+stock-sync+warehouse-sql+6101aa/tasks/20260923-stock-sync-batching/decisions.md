# Decisions — stock-sync batching

## Volume math (conditional section)

Inputs: 6,000 events/day, 85% in the 12h 08:00–20:00 UTC, overnight 30–40/h across all
partitions (`deploy-config/runbooks/stock-sync.md:5-6`); 8 pods, one per partition
(`overlays/prod/stock-sync.yaml:6`). Per-pod rate assumes even partitions (A1).

| Window | All pods | Per pod | Items per pod in 15 min | Time for one pod to reach 25 |
|---|---|---|---|---|
| Peak 08:00–20:00 | 425/h (7.1/min) | 53/h (0.89/min) | ~13 | ~28 min |
| Overnight | ~35/h (0.58/min) | ~4.4/h | ~1 | ~5.7 h |

A pod buffering on its own **never** reaches 25 items inside 15 minutes, even at peak.
Aggregating all 8 pods into one stream would reach 25 in ~3.5 min at peak, but still only
~9 items in 15 minutes overnight.

**So R2 (≥25 items) and R4 (≤15 min) are jointly unsatisfiable at current volume**, by any
design, per-pod or global. This is the conflict to take back to the partner (G4).

Call-volume effect of the chosen design: batching can never send *more* requests than today
(a flush replaces ≥1 individual call). At peak it drops from ~425 calls/h to at most
8 pods × 6 flushes/h = 48/h — roughly a 90% reduction, and it removes the 1-item bursts that
the partner says are hitting their rate limit. Headroom against the 10 req/s limit is large
either way.

### D1 — Freshness wins; the 25-item minimum is best-effort
Flush on whichever comes first: the buffer reaches the target size, or the oldest buffered
item reaches the age deadline. Sending a 13-item batch on time is the safe failure: late
stock makes the partner show wrong availability, which is the harm R4 names. Holding items
to reach 25 would breach R4 by design, every night, indefinitely.
*Decided because the volume math above. If evidence shows per-pod volume is ~2× the runbook
figures at peak, batches fill on size at peak and only the overnight gap remains — reopen
the deadline value, not the design.*

### D2 — Age deadline default 600s (10 min), not 900s
Leaves margin inside the 15-minute promise for retry backoff (`partner_client.py:45`,
up to 7s), the flush itself, and clock/scheduling slack. Configurable.

### D3 — Buffer per pod, in memory; no shared or persistent buffer
Pods share nothing but the sent-log volume (`runbooks/stock-sync.md:4`). A shared buffer
would be a new distributed component, and the math shows it would still not satisfy R2
overnight — so it buys nothing against the actual requirement. In-memory loss is safe
because of D4.

### D4 — Failure model: commit offsets and mark dedup only *after* a successful flush
Today: send → mark → publish → commit (`consumer.py:17-19`, `:28`), so a crash before commit
is covered by redelivery + the dedup store.
With buffering, the same property must hold for the whole batch: buffered messages stay
uncommitted and unmarked until the partner call returns. A crash then loses the in-memory
buffer, the broker redelivers those offsets, the dedup store has not marked them, and they
are sent again. The unsafe alternative — committing on enqueue — would silently drop stock
updates with nothing to re-deliver them (R5).
A failed flush (`PartnerError` after retries) keeps the buffer, marks nothing, commits
nothing, and propagates, exactly as an individual failed send does today.

### D5 — `stock.sent` stays one message per item, published after the flush
`load_stock_sent.sql:4-8` reads `sku`/`qty`/`updated_at` from each message value; publishing
a batch envelope would break the hourly warehouse load (cross-repo blast radius).

### D6 — Dedup filtering moves to enqueue time, plus within-batch
`sent_log.seen` still gates each event on arrival, and a batch is de-duplicated by
`event_id` before sending, since redelivery can put the same event in one buffer twice.

### D7 — No idle-flush dependency on unverified broker behaviour (U1)
The deadline can only fire if the consumer loop regains control while idle. `run()` uses a
poll-with-timeout when the injected client offers one. If it does not, the service logs an
error and runs **unbatched** (today's behaviour) rather than silently holding stock past 15
minutes overnight. Safe if the assumption is wrong, and visible in logs.
*Decided because U1 is unresolved. If the client does support idle polling, batching turns
on with no code change.*

## Open items status (2026-09-23)

- **U2 / Q1 — partner's preference between the 25-item minimum and the 15-minute window:
  `awaiting`.** The user forwarded the drafted message to the account manager on 2026-09-23;
  no reply expected today. The account manager then has to reach the partner's integration
  team, so this may take several days.
  Until it is answered, D1 stands as an **accepted-assumption**: we send on the deadline with
  whatever has accumulated. Who: the user, 2026-09-23, on my recommendation. Consequence in
  one sentence: the partner will receive batches smaller than the 25 items they asked for,
  often much smaller overnight, in exchange for never being more than 15 minutes stale.
  What would reverse it: the partner saying they prefer full 25-item batches even when that
  means stock arrives late — then raise `BATCH_MAX_AGE_SECONDS` (env var, no code change)
  and revisit the freshness claim in `README.md`.
- **U1 / Q2 — broker idle poll: `awaiting`, not yet routed.** Not covered by the message the
  user is forwarding; it goes to whoever owns the broker client, not the partner. Until
  answered, D7 stands: batching code ships but the service runs unbatched wherever the
  injected client has no `poll`, logging an ERROR at startup. Consequence: ticket 131 is not
  actually delivered in production until this is confirmed.

## Affected-work map

| Work | Depends on | Status |
|---|---|---|
| `batcher.py` + tests (buffer, size/age flush, dedup) | — | do now |
| `consumer.handle`/`run` wiring, config knobs | D1–D6 | do now |
| Actual idle flushing in prod | U1 | code ready, degrades to unbatched |
| Partner conversation about R2 vs R4 | user | drafted, not sent |
| `deploy-config` env overrides | none needed (defaults) | not touched |
| `price-sync` (same one-per-call shape) | out of scope | not touched |

## Noted, not changed (pre-existing, outside this ask)

`services/stock-sync/base.yaml:18-20` mounts one PVC (`stock-sync-sent-log`) for the sqlite
dedup store while prod runs 8 replicas. Eight sqlite writers on one shared volume is a
correctness risk that exists today and is unrelated to batching.
