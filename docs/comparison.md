# Comparison with django-probes

`django-deploy-probes` and `django-probes` solve related but different deployment problems.

## django-deploy-probes

- Provides HTTP endpoints: `/healthz`, `/readyz`, `/startupz`, and `/version`.
- Targets runtime deployment verification, Kubernetes probes, Docker health checks, and blue-green validation.
- Checks multiple dependencies: database, Redis, Celery, migrations, and custom checks.
- Keeps operational endpoints secret-safe by default.
- Supports optional drf-spectacular OpenAPI metadata.

## django-probes

- Provides a Django management command for waiting on database availability.
- Is useful in init containers or startup scripts before running migrations or the application.
- Does not expose HTTP probe endpoints for traffic routing or runtime readiness.

## When to Use This Package

Use `django-deploy-probes` when your deployment platform needs HTTP endpoints to decide whether a Django process is alive, ready for traffic, started, or running the expected version.

Use a management-command style tool when your startup script needs to block until the database is reachable before continuing.
