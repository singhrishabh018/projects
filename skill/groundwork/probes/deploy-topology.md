# Probe: deploy topology and schedules

Use when the workspace has deployment config (Kubernetes-style manifests, Helm/Kustomize,
compose files, platform config, Terraform) or scheduled jobs.

- Find config for the touched service in **every** repo, not just its own: search for the
  service name across the workspace (a separate deploy/infra repo is common).
- **Instances:** replicas / min–max / autoscaling settings per environment, including
  overlays and overrides (base vs prod). Record the effective value per environment and
  which file sets it. Config says what is configured, not what is running.
- **Per-instance state:** combine with the code. N instances × in-memory buffer/cache/
  counter means N independent copies: work splits N ways, per-instance thresholds are
  reached N times more slowly, and state is lost on restart or scale-down.
- **Schedules:** cron jobs, scheduled tasks, publish/batch windows, and their timezone.
  Note when the output of the touched flow becomes visible to users or partners.
- **Env and flags:** env vars and defaults per environment; flags that default on;
  prod endpoints or identifiers in non-prod config.
- **Lifecycle:** shutdown/drain behaviour, restarts, rollout strategy — only if the change
  holds state or in-flight work.

Output: claims in `research.md`; per-instance state or schedule interactions that affect
the design are always material → decision record (volume math if triaged).
