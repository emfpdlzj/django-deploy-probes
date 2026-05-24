# Changelog

## v0.1.0 - Initial Release

`django-deploy-probes` provides lightweight deployment probe endpoints for Django applications.

This release is focused on deployment validation workflows such as blue/green deployments, rolling deployments, Kubernetes probes, Docker health checks, Nginx upstream switching, and CI/CD verification.

### Highlights

- Add `healthz` endpoint for process liveness checks.
- Add `readyz` endpoint for traffic readiness checks.
- Add `startupz` endpoint for startup/bootstrap checks.
- Add `version` endpoint for deployed application metadata.
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
