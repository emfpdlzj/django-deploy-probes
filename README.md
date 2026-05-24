# django-deploy-probes

Production-ready HTTP deployment probe endpoints for Django applications. Unlike `django-probes`, this package does not provide management commands; it exposes lightweight `/healthz`, `/readyz`, `/startupz`, and `/version` views for runtime deployment checks.

Use these endpoints for CI/CD, Docker, Kubernetes, and blue-green deployments.

[![PyPI](https://img.shields.io/pypi/v/django-deploy-probes.svg?label=PyPI)](https://pypi.org/project/django-deploy-probes/)
[![Django Packages](https://img.shields.io/badge/Django%20Packages-django--deploy--probes-0c4b33.svg)](https://djangopackages.org/packages/p/django-deploy-probes/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-3776AB.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-%3E%3D4.2-0C4B33.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-5C3EE8.svg)](https://docs.astral.sh/uv/)

## Features

- Lightweight `healthz` endpoint for liveness checks.
- Dependency-aware `readyz` endpoint for deployment readiness checks.
- `startupz` endpoint for startup/bootstrap checks such as pending migrations.
- `version` endpoint for validating service metadata, with optional build details when explicitly enabled.
- Optional Redis, Celery, migration, and custom readiness checks for production deployments.
- Secret-safe response defaults, with optional safe failure reasons and check durations for CI/CD debugging.

## Quick Start

- [Install the package](#installation)
- [Configure Django URLs](#include-style-url-configuration)

## Installation

```bash
pip install django-deploy-probes
```

Optional Redis and Celery readiness checks are available as extras:

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[all]"
```

Optional Swagger/OpenAPI documentation support is available as a separate extra:

```bash
pip install "django-deploy-probes[openapi]"
```

### Include-style URL configuration

Add the app so Django system checks can validate your probe settings:

```python
INSTALLED_APPS = [
    "django_deploy_probes",
]
```

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

### Import-style URL configuration

```python
from django.urls import path
from django_deploy_probes.views import healthz, readyz, startupz, version

urlpatterns = [
    path("healthz", healthz),
    path("readyz", readyz),
    path("startupz", startupz),
    path("version", version),
]
```

Custom check messages are hidden by default. If you enable `EXPOSE_CHECK_MESSAGES=True`, do not include secrets or sensitive values in those messages.

Security checks use `REMOTE_ADDR` by default and do not trust `X-Forwarded-For`; configure your reverse proxy separately when probes are accessed through a proxy.

### Common settings

```python
DEPLOY_PROBES = {
    "SERVICE_NAME": "my-django-app",
    "ENVIRONMENT": "prod",
    "VERSION": "1.2.0",
    "READY_CHECKS": ["database", "redis", "celery"],
    "STARTUP_CHECKS": ["migrations"],
    "READY_CUSTOM_CHECKS": [],
    "STARTUP_CUSTOM_CHECKS": [],
    "DATABASES": ["default"],
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
    "INCLUDE_CHECK_DURATIONS": False,
    "REQUIRE_READY_CHECKS": False,
    "REQUIRE_STARTUP_CHECKS": False,
    "EXPOSE_CHECK_MESSAGES": False,
    "INTERNAL_IP_ONLY": False,
    "INTERNAL_IP_NETWORKS": [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ],
}
```

Set `DETAIL_LEVEL="safe"` to include stable failure reasons such as
`redis_package_missing` or `unapplied_migrations`.

Set `INCLUDE_CHECK_DURATIONS=True` to wrap each check result with a `status` and
`duration_ms` value. This is useful in CI/CD diagnostics, but keep it disabled if
you want the smallest possible response body.

## Optional Swagger/OpenAPI

Probe endpoints are not added to Swagger/OpenAPI documentation by default. They are operational endpoints and should normally stay internal or be protected with the package security options documented in [Security options](docs/security.md).

To document `/healthz`, `/readyz`, `/startupz`, and `/version` with drf-spectacular, install the OpenAPI extra:

```bash
pip install "django-deploy-probes[openapi]"
```

Enable probe documentation explicitly in `settings.py`:

```python
INSTALLED_APPS = [
    "django_deploy_probes",
    "rest_framework",
    "drf_spectacular",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

DEPLOY_PROBES = {
    "ENABLE_OPENAPI": True,
    "OPENAPI_TAG": "Deployment Probes",
}
```

Add drf-spectacular schema and Swagger UI URLs in your project `urls.py`:

```python
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
```

If `ENABLE_OPENAPI=True` but drf-spectacular is not installed, the probe views continue to work without schema metadata. drf-yasg is not implemented in this phase and is reserved for future compatibility work.

## Tutorials

- [Tutorial index](docs/tutorial.md)
- [Basic setup](docs/basic.md)
- [Docker integration](docs/docker.md)
- [Docker Compose integration](docs/docker-compose.md)
- [Kubernetes probes](docs/kubernetes.md)
- [API reference](docs/api.md)
- [Security options](docs/security.md)
- [Comparison with django-probes](docs/comparison.md)
- [GitHub Actions deployment validation](docs/recipes/github-actions.md)
- [Nginx blue-green switching](docs/recipes/nginx-blue-green.md)
- [AWS ECS/ALB health checks](docs/recipes/aws-ecs-alb.md)

## Runnable Examples

- [Basic example](examples/basic)
- [Docker example](examples/docker)
- [Docker Compose example](examples/docker-compose)
- [Kubernetes example](examples/kubernetes)
- [Security example](examples/security)

## Build and Publish

### Build

```bash
uv build
```

Generated distributions are written to `dist/`.

Generated files:

- `dist/django_deploy_probes-0.1.0.tar.gz`
- `dist/django_deploy_probes-0.1.0-py3-none-any.whl`

### Installation Test

After building, install the wheel in a clean environment:

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.1.0-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### PyPI Publish

Publishing is handled by `.github/workflows/publish.yml` when a GitHub release is published.
Configure PyPI Trusted Publishing for the repository before the first release.
