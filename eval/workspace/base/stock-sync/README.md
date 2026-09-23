# stock-sync

Consumes `stock.changed` events from the message broker and pushes stock levels to the
marketplace partner's inventory API. After each successful send it publishes the sent item
to `stock.sent` (the warehouse loads that topic for the "what did we send" report).

Run tests: `python -m unittest discover -s tests`

Config comes from environment variables, see `stock_sync/config.py`.
Deployment manifests live in the `deploy-config` repo.
