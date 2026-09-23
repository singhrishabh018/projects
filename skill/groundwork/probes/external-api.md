# Probe: external API or partner contract

Use when the change sends data to, or reads data from, a system outside the workspace.

- **Source of truth for the contract:** partner docs, an OpenAPI/JSON schema, a sample
  payload, a client library in the workspace, or tests. Record each as a claim with its
  date/version. Workspace code is a claim about what *we* send, not what *they* accept.
- **Field names, types and formats:** exact spelling and casing, number/decimal/currency
  formats, date/time formats and timezones, enums, required vs optional.
- **What success means:** does a 2xx/202 mean "accepted and applied", "queued", or just
  "received"? Is there a way to read back what was applied (status endpoint, report,
  callback, reconciliation file)?
- **Silent failure:** what happens to unknown fields, wrong formats, unknown ids? Rejected
  with an error, or silently dropped/ignored? If unknown, it's a material unknown: ask
  (C7) and plan verification that doesn't rely on the status code.
- **Idempotency, ordering, limits:** duplicate sends, out-of-order updates, batch size
  limits, rate limits and what happens when exceeded.
- **Existing client:** reuse the workspace's client/helper for this partner if one
  exists (auth, retries, serialization); don't write a second one.

Verification (C8): assert on the payload the partner accepts (names, formats), using the
contract source, and where possible a read-back. "Request returned 2xx" proves delivery at
most.
