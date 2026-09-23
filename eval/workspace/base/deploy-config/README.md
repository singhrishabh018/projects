# deploy-config

Kubernetes-style manifests for the catalog-sync services.
`services/<name>/base.yaml` is the base; `overlays/<env>/<name>.yaml` patches it per
environment (the overlay wins). `jobs/schedules.yaml` lists scheduled jobs.
