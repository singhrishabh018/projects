# Partner inventory API (v2) — our notes

Copied from the partner's integration guide, last checked 2026-06-10.

## POST /v2/inventory

Body: `{"items": [ ... ]}`, 1–500 items per call.

| Field | Type | Required | Notes |
|---|---|---|---|
| `sku` | string | yes | our SKU |
| `qty` | integer ≥ 0 | yes | sellable quantity |
| `updated_at` | ISO-8601 datetime | yes | |
| `location` | string | no | our warehouse code |
| `restock_eta` | string `YYYY-MM-DD` | no | expected restock date |

Behaviour to know about:
- The API answers **202 Accepted** for any well-formed JSON body. Validation happens later,
  asynchronously, and is not reported back.
- **Unknown fields are ignored without error.** A misspelled field name is simply dropped.
- **Values in the wrong format are dropped without error** (e.g. `restock_eta` as a
  timestamp instead of `YYYY-MM-DD`). An item missing `qty` is dropped entirely.
- Rate limit: 10 requests/second per token.

## POST /v2/locations/{code}/reset

Sets qty to 0 for every SKU at that location. Empty body. 202 Accepted.
Used when a warehouse closes or is taken offline.
