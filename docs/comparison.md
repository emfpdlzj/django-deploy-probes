# Choosing a Django Health Check Package

Several Django packages expose health information, but they optimize for different jobs.
Choose by the decision that consumes the result: an orchestrator deciding whether to route
traffic, an external monitor inspecting dependencies, or a startup script waiting for a service.

## At a Glance

| Capability | django-deploy-probes | django-health-check | django-watchman | django-alive | django-probes |
| --- | --- | --- | --- | --- | --- |
| Primary job | Deployment and traffic-routing decisions | Extensible service health monitoring | Backing-service status and dashboard | Lightweight alive/health endpoints | Wait for services during startup |
| Dedicated liveness endpoint | `/healthz` | Deployment-specific configuration | `/watchman/ping/` and bare status views | `/-/alive/` | No HTTP endpoint |
| Dedicated readiness endpoint | `/readyz` | One extensible health endpoint | One status endpoint | `/-/health/` | No HTTP endpoint |
| Dedicated startup endpoint | `/startupz` | Not a separate contract | Not a separate contract | Not a separate contract | Management command |
| Deployment metadata | `/version` with optional build fields | Not a built-in deployment contract | Not a built-in deployment contract | Not a built-in deployment contract | No |
| CLI execution | Same payload contract as HTTP | `health_check` command | Management command | `healthcheck` command | Core workflow |
| Built-in focus | Database, migrations, Redis, Celery, storage | Broad plugin catalog including cache and system resources | Database, cache, email, storage, custom checks | Database, cache, static files, migrations | Service availability before startup |
| Access controls | Internal CIDRs, trusted proxies, header token | Deployment-specific | Token authentication | Deployment-specific | Not applicable |

The table describes built-in behavior, not everything that can be implemented with custom checks.
Review each project's current documentation before migrating an existing production deployment.

## When django-deploy-probes Fits

Use this package when the important questions are:

- Is the Django process alive without touching an external dependency?
- Is this instance ready to receive traffic now?
- Have startup requirements, such as migrations, completed?
- Is the expected version, commit, or deployment slot running?
- Can CI and HTTP callers evaluate the same probe payload?

These questions map directly to Kubernetes liveness, readiness, and startup probes, Docker health
checks, load balancer routing, blue-green switching, deployment verification, and rollback checks.

## When Another Package Fits Better

Choose [django-health-check](https://github.com/codingjoe/django-health-check) when you want a
large plugin catalog, HTML and JSON health output, or host-level checks such as disk and memory.

Choose [django-watchman](https://django-watchman.readthedocs.io/) when you want a backing-service
dashboard, a single status endpoint, token authentication, and integrations aimed at external
monitoring.

Choose [django-alive](https://github.com/lincolnloop/django-alive) when two lightweight alive and
health endpoints, plus a small custom-check interface, cover your deployment.

Choose [django-probes](https://github.com/painless-software/django-probes) when a startup script or
init container needs to wait for a database or another service and HTTP routing probes are
unnecessary.

These packages can coexist when the consumers are different. For example, an orchestrator can use
`django-deploy-probes` for traffic decisions while an internal monitoring system uses a richer
dashboard. Avoid running expensive monitoring checks from a high-frequency liveness probe.

## Scope Boundary

`django-deploy-probes` intentionally does not store probe history, send alerts, aggregate metrics,
or replace an observability platform. It returns a current, secret-safe deployment decision. Use
monitoring and tracing systems for trends, alerting, diagnosis, and capacity planning.
