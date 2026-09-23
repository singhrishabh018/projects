# Send restock date to partner (stock-sync) — 2026-09-23

## Decisions
1. Map event `restock_date` (epoch ms) -> partner `restock_eta` (YYYY-MM-DD).
   Partner ignores unknown field names and drops wrong-format values, both silently,
   and answers 202 regardless. Pass-through would have been a silent no-op.
   [observed · stock-sync/docs/partner-api.md:15,20-21]
2. Omit the key when restock_date is null or absent. Field is optional partner-side;
   `null` is not YYYY-MM-DD and would be dropped anyway.
   [observed · schemas/stock_changed.json:12,15 — nullable and not in `required`]
3. Render the date in UTC, matching the schema's own label and the existing
   `updated_at` conversion in payload.py.

## Accepted assumption [confirmed by user 2026-09-23]
User answered "go with your recommendation" — a deferral to the recommendation,
not an assertion of the producer's timezone convention. It stays an accepted
assumption rather than a verified fact, though it agrees with the schema label.

The producer's `restock_date` epoch ms denotes the intended calendar day *in UTC*.
If it is instead local-midnight-at-the-warehouse, dates can land one day early.
Consequence: restock ETA shown to customers off by one day for some warehouses.
Reversed by: the producer team confirming the timezone convention.
Not blocking: schema line 12 says "epoch milliseconds UTC" explicitly.

## Verified
`python -m unittest discover -s tests` in stock-sync: 9 tests, OK (3 new).
Tests use the in-repo FakePartner, which records requests and always returns 202 —
it does NOT validate the partner's field names or formats. So the tests prove our
payload shape, not partner acceptance. Unverified against the real partner API.

## Downstream checked
stock.sent carries the same dict into warehouse `stock_sent.raw` (JSONB);
load_stock_sent.sql reads only sku/qty/updated_at, so the extra key is inert.
No warehouse change needed. [observed · warehouse-sql/procs/load_stock_sent.sql,
tables/stock_sent.sql]
