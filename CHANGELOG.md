# Changelog

## v0.6.0

Strengthen production confidence with stricter configuration validation, real backend integration
coverage, current runtime support, and deployment-focused operations documentation.

### Highlights

- Validate probe settings with the same recursive merge used at runtime and reject invalid or
  duplicate checks, aliases, metadata, boolean flags, header-token options, and OpenAPI setup.
- Reject Celery readiness configurations that enable no broker, worker, or result-backend operation.
- Treat configured custom readiness and startup checks as satisfying the corresponding
  `REQUIRE_*_CHECKS` setting.
- Exercise database and migration probes against PostgreSQL, storage probes against MinIO through
  Django's S3 storage backend, and Celery broker and result-backend probes against Redis in CI.
- Add Django 6.1 support while retaining Django 5.2 LTS and 6.0 coverage across their supported
  Python versions.
- Enforce a 90% coverage floor, define stable Ruff rule selection, group dependency updates, and
  update GitHub Actions and locked dependencies.
- Add a production operations guide, failure-drill checklist, contributor guide, and an expanded
  comparison with other Django health-check packages.

### Upgrade notes

- Existing valid endpoint payloads, HTTP status codes, management-command exit codes, and setting
  defaults are unchanged.
- `python manage.py check` and `python manage.py deploy_probes ...` now reject configurations that
  were already invalid but could previously reach runtime. Fix reported aliases and types before
  deployment.
- When `ENABLE_OPENAPI=True`, install the `openapi` extra so Django REST Framework and
  drf-spectacular are available.
- When `celery` appears in `READY_CHECKS` or `STARTUP_CHECKS`, enable at least one of `BROKER`,
  `WORKERS`, or `RESULT_BACKEND`.

## v0.5.1

Harden probe result accuracy, HTTP cache safety, configuration validation, and backend
compatibility verification.

### Highlights

- Measure `duration_ms` independently for every database, Redis, storage, Celery, migration,
  and custom check result instead of copying one batch duration to every result.
- Mark every HTTP probe response, including forbidden responses, as non-cacheable.
- Validate that custom check paths are unique, importable, and callable during Django system
  checks.
- Turn duplicate runtime result names into an explicit probe failure instead of silently
  overwriting an earlier result.
- Install all optional extras across the supported CI matrix and add real Django database,
  filesystem storage, and Redis integration tests.
- Add weekly dependency updates for uv and GitHub Actions.
- Move the package maturity classifier from Alpha to Beta and align support guidance with the
  repository's enabled communication channels.

## v0.5.0

Make timeout behavior an explicit, backend-enforced contract.

### Highlights

- Remove the unused top-level `DEPLOY_PROBES["TIMEOUT"]` setting and report it as a
  Django system check error.
- Define `REDIS[*]["TIMEOUT"]` as the Redis connect and socket timeout.
- Define `CELERY["TIMEOUT"]` as the broker connection and worker ping timeout.
- Clarify that database, migration, storage, Celery result backend, and custom checks
  must use their backend-native timeout configuration.
- Return the stable safe failure reason `reason="timeout"` when a recognized timeout
  exception is raised.
- Validate Redis and Celery timeout values before deployment.
- Keep checks sequential and document how to size the platform probe timeout around
  the worst-case configured check duration.

### Upgrade notes

- Remove any top-level `DEPLOY_PROBES["TIMEOUT"]` value. It was accepted but never
  enforced in earlier releases.
- Configure database driver and statement timeouts in Django `DATABASES`, storage
  timeouts in the storage backend, and result backend timeouts in Celery itself.
- Custom checks must configure timeout behavior in their own network client and let
  timeout exceptions propagate.
- No endpoint URL, successful response payload, or management command exit code changed.

## v0.4.0

Modernize the supported runtime baseline around maintained Python and Django releases.

### Highlights

- Add Django 6.0 compatibility and CI coverage on Python 3.12 through 3.14.
- Keep Django 5.2 LTS coverage on Python 3.10 through 3.14.
- Drop support for end-of-life Python 3.9 and Django releases before 5.2.
- Run the compatibility suite with Python deprecation warnings enabled.
- Publish the supported runtime policy in the README, support guide, and security policy.

### Upgrade notes

- Projects using Django 4.2, 5.0, or 5.1 should remain on `django-deploy-probes<0.4`
  until they upgrade to Django 5.2 or later.
- Python 3.9 users should remain on `django-deploy-probes<0.4` or upgrade Python.
- No probe endpoint, setting, payload, or management command behavior changed in this release.

## v0.3.1

Stabilize release hygiene, strengthen edge-case coverage, and harden publish automation.

### Highlights

- Add regression tests for registry, result normalization, security helper, and Django system check edge cases.
- Add release hygiene tests to keep package version, changelog, and localized build/install docs aligned.
- Add wheel smoke-install verification to publish workflows before PyPI or TestPyPI upload.
- Add strict MkDocs validation to the main CI workflow and refresh example version strings in docs.

## v0.3.0

Add an in-process CLI runner for deployment probes.

### Highlights

- Add `python manage.py deploy_probes <healthz|readyz|startupz|version>` management command.
- Keep the CLI JSON payload contract aligned with the HTTP probe responses.
- Add explicit CLI exit codes for probe pass, probe failure, invalid configuration, and unexpected execution failure.
- Extract shared probe execution into a common runner used by both HTTP views and the CLI.
- Document CLI usage for CI/CD, pre-deploy validation, and local debugging.

## v0.2.1

Add Django storage probe checks for deployment readiness validation.

### Highlights

- Add builtin `storage` checks for Django storage aliases, including S3-style backends.
- Support `exists` mode for sentinel object validation.
- Support `write` mode for temporary write/delete validation.
- Add Django system checks for invalid storage probe configuration.
- Update documentation with storage and S3 usage examples.

## v0.2.0 - Proxy-Aware Probe Security

This release improves probe security for deployments behind trusted reverse proxies such as ALB,
Nginx, and Kubernetes ingress.

### Highlights

- Add `TRUSTED_PROXY_NETWORKS` for explicitly trusted proxy CIDRs.
- Add `CLIENT_IP_HEADER` for resolving the original client IP from trusted proxy headers.
- Keep `REMOTE_ADDR` as the safe default when trusted proxy settings are not configured.
- Ignore forwarded IP headers unless the request comes from a trusted proxy network.
- Add Django system checks for proxy CIDR and client IP header validation.
- Expand tests and documentation for reverse proxy probe deployments.

## v0.1.0 - Initial Release

`django-deploy-probes` provides lightweight deployment probe endpoints for Django applications.

This release is focused on deployment validation workflows such as blue/green deployments, rolling deployments, Kubernetes probes, Docker health checks, Nginx upstream switching, and CI/CD verification.

### Highlights

- Add `healthz` endpoint for process liveness checks.
- Add `readyz` endpoint for traffic readiness checks.
- Add `startupz` endpoint for startup/bootstrap checks.
- Add `version` endpoint for deployed application metadata.
- Add builtin `storage` checks for Django storage aliases, including S3-style backends.
- Support both include-style and import-style Django URL configuration.
- Support optional readiness checks for Django databases, Redis, Celery, migrations, and custom checks.
- Add optional package extras for Redis and Celery integrations.
- Add basic probe access controls for internal IP and header token validation.
- Add configurable internal IP networks, secret-safe custom check messages, and optional safe
  failure reasons.
- Add GitHub Actions CI and Trusted Publishing release workflow.

### Installation

Install the base package:

```bash
pip install django-deploy-probes
```

Install optional Redis and Celery readiness check dependencies:

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[all]"
```

### Quick Start

Include all probe URLs:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

This exposes:

- `GET /healthz`
- `GET /readyz`
- `GET /startupz`
- `GET /version`

Alternatively, import the views directly:

```python
from django.urls import path
from django_deploy_probes.views import healthz, readyz, startupz, version

urlpatterns = [
    path("healthz/", healthz),
    path("readyz/", readyz),
    path("startupz/", startupz),
    path("version/", version),
]
```

Configure deployment metadata and readiness checks in Django settings:

```python
DEPLOY_PROBES = {
    "SERVICE_NAME": "my-django-app",
    "ENVIRONMENT": "prod",
    "VERSION": "1.2.0",
    "COMMIT": "a1b2c3d",
    "BRANCH": "main",
    "BUILD_TIME": "2026-05-13T10:00:00+09:00",
    "SLOT": "green",
    "READY_CHECKS": [
        "database",
        "redis",
        "celery",
    ],
    "DATABASES": [
        "default",
    ],
    "REDIS": {
        "default": {
            "LOCATION": "redis://localhost:6379/0",
            "TIMEOUT": 1.0,
        },
    },
    "CELERY": {
        "BROKER": True,
        "WORKERS": False,
        "RESULT_BACKEND": False,
        "TIMEOUT": 1.0,
    },
    "DETAIL_LEVEL": "none",
    "EXPOSE_CHECK_MESSAGES": False,
}
```

### Endpoint Behavior

`GET /healthz` returns `200` when the Django process is alive:

```json
{
  "status": "ok"
}
```

`GET /readyz` returns `200` when all enabled readiness checks pass:

```json
{
  "status": "ready",
  "checks": {
    "database.default": "ok",
    "redis.default": "ok",
    "celery.broker": "ok"
  }
}
```

`GET /readyz` returns `503` when any enabled readiness check fails:

```json
{
  "status": "not_ready",
  "checks": {
    "database.default": "ok",
    "redis.default": "fail",
    "celery.broker": "ok"
  }
}
```

`GET /version` returns configured deployment metadata:

```json
{
  "service": "my-django-app",
  "environment": "prod",
  "version": "1.2.0",
  "commit": "a1b2c3d",
  "branch": "main",
  "build_time": "2026-05-13T10:00:00+09:00",
  "slot": "green"
}
```

### Supported Versions

- Python: 3.9+
- Django: 4.2+
- Redis extra: `redis>=4.5`
- Celery extra: `celery>=5.3`

Package classifiers include Python 3.9 through 3.14 and Django 4.2 / 5.x.

### Known Limitations

- `healthz` is intentionally minimal and does not check databases, cache, Redis, Celery, migrations, or external services.
- `readyz` only checks dependencies that are explicitly enabled in `DEPLOY_PROBES["READY_CHECKS"]`.
- Redis and Celery checks require installing the corresponding optional extras.
- Security checks use `REMOTE_ADDR` by default and do not trust `X-Forwarded-For`; configure trusted proxy handling separately at the application or infrastructure layer.
- Custom readiness check messages are hidden by default; do not include secrets or sensitive values
  if `EXPOSE_CHECK_MESSAGES=True`.
- This package is not a metrics, tracing, APM, or full monitoring system.

### Next Version Plans

- Expand documentation for production deployment patterns.
- Add more examples for Kubernetes, Docker, Nginx, and CI/CD validation.
- Add more examples for custom readiness checks.
- Consider richer readiness check result details while keeping secret-safe defaults.
- Continue compatibility testing across supported Python and Django versions.
