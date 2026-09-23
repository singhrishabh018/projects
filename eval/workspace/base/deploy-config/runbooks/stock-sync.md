# stock-sync runbook

- Prod: see `overlays/prod/stock-sync.yaml` (one pod per partition of `stock.changed`).
  Each pod consumes only its own partitions; pods share nothing except the sent-log volume.
- Traffic (last quarter): about 6,000 stock.changed events per day, ~85% between 08:00 and
  20:00 UTC. Overnight it drops to roughly 30–40 events per hour across all partitions.
- Partner freshness expectation: see the partner agreement notes in the tracker.
