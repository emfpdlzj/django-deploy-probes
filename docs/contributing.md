# Contributing Guide

Contributions are welcome when they strengthen deployment decisions without turning the package
into a monitoring platform. Start with the repository's
[contribution guidelines](https://github.com/emfpdlzj/django-deploy-probes/blob/main/CONTRIBUTING.md)
and open an issue when a change affects public settings or response contracts.

## Good Contribution Areas

- Reproduce and fix a backend-specific probe failure.
- Add a production backend integration case.
- Improve a Docker, Kubernetes, load balancer, or CI/CD recipe.
- Add a secret-safe failure classification.
- Strengthen Django system checks for configuration errors.
- Improve accessibility, translations, or first-time setup documentation.
- Test a supported Python or Django release candidate.

Small documentation corrections and focused test improvements can be submitted directly. For a
new built-in check, explain why it is commonly required for traffic readiness and why a custom
check is insufficient.

## Scope Questions

Before proposing a feature, ask:

1. Does a deployment platform or release pipeline need this result to make a current decision?
2. Can failure remain secret-safe by default?
3. Can the underlying client enforce a real timeout?
4. Can the behavior be tested without relying only on mocks?
5. Does it preserve the lightweight `/healthz` contract?

History storage, dashboards, alert delivery, metrics aggregation, and tracing belong in monitoring
or observability systems rather than this package.

## Test Levels

Run the focused tests while developing, then the complete checks before opening a pull request:

```bash
uv run pytest -q tests/test_readyz.py
uv run ruff check .
uv run ruff format --check .
uv run pytest -q --cov
uv run mkdocs build --strict
uv build
```

The coverage suite must remain at or above 90%. The CI compatibility matrix covers Python 3.10
through 3.14 and Django 5.2 LTS, 6.0, and 6.1. A separate integration job exercises PostgreSQL,
Redis, Celery, filesystem storage, and S3-compatible storage.

## Compatibility Rules

Treat these as public contracts:

- Endpoint names and HTTP status codes.
- JSON status fields and check result normalization.
- Management-command exit codes.
- Settings names, defaults, and Django system-check identifiers.
- Secret-safe default behavior.

Behavior changes require tests and documentation in the same pull request. Breaking changes need a
clear migration path and a major-version discussion. New safe failure reasons and stricter rejection
of previously invalid configuration can be introduced in a minor release when documented.

## Issue Reports

Use the repository's [bug report](https://github.com/emfpdlzj/django-deploy-probes/issues/new/choose)
and include the Python, Django, and package versions; sanitized `DEPLOY_PROBES` settings; the probe
status and payload; and the relevant backend. Never include credentials, tokens, connection URLs,
or sensitive custom-check messages.
