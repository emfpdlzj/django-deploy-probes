# django-deploy-probes

Production-ready deployment probes for Django applications, with HTTP endpoints and an in-process CLI runner.

Use `django-deploy-probes` for CI/CD deployment validation, Docker health checks, Kubernetes probes, blue-green deployments, and rollback checks.

[![PyPI](https://img.shields.io/pypi/v/django-deploy-probes.svg?label=PyPI)](https://pypi.org/project/django-deploy-probes/)
[![Django Packages](https://img.shields.io/badge/Django%20Packages-django--deploy--probes-0c4b33.svg)](https://djangopackages.org/packages/p/django-deploy-probes/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2%20%7C%206.0-0C4B33.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-5C3EE8.svg)](https://docs.astral.sh/uv/)

## Documentation

- [Documentation site](https://emfpdlzj.github.io/django-deploy-probes/)
- [Basic setup](docs/basic.md)
- [Endpoint reference](docs/api.md)
- [Security options](docs/security.md)
- [Docker integration](docs/docker.md)
- [Docker Compose integration](docs/docker-compose.md)
- [Kubernetes probes](docs/kubernetes.md)
- [GitHub Actions deployment validation](docs/recipes/github-actions.md)

## Install

```bash
pip install django-deploy-probes
```

Supported runtimes:

- Python 3.10 through 3.14
- Django 5.2 LTS and Django 6.0

The `0.3.x` release line remains available for projects that still require Django 4.2.

Optional extras:

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[openapi]"
pip install "django-deploy-probes[all]"
```

## Quick Start

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

Verify over HTTP:

```bash
curl -f http://localhost:8000/healthz
curl -f http://localhost:8000/readyz
curl -f http://localhost:8000/version
```

Or run the same probes in-process from Django:

```bash
python manage.py deploy_probes healthz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes startupz --json
python manage.py deploy_probes version --json
```

The CLI reuses the same probe payload contract as the HTTP endpoints. Use it for CI/CD steps, pre-deploy validation, container bootstrap checks, and local debugging. For Kubernetes liveness, readiness, and startup probes, keep using HTTP endpoints as the default integration.

Custom check messages are hidden by default. If you enable `EXPOSE_CHECK_MESSAGES=True`, do not include secrets or sensitive values in those messages.

Security checks use `REMOTE_ADDR` by default. If probes are accessed through a trusted reverse proxy, configure `TRUSTED_PROXY_NETWORKS` and `CLIENT_IP_HEADER` to resolve the original client IP safely.

Storage checks use Django storage aliases, so the same probe can validate local filesystems, S3-compatible backends, and any custom storage backend wired through `STORAGES`.

### Common settings

```python
DEPLOY_PROBES = {
    "SERVICE_NAME": "my-django-app",
    "ENVIRONMENT": "prod",
    "VERSION": "1.2.0",
    "READY_CHECKS": ["database", "redis", "celery", "storage"],
    "STARTUP_CHECKS": ["migrations"],
    "READY_CUSTOM_CHECKS": [],
    "STARTUP_CUSTOM_CHECKS": [],
    "DATABASES": ["default"],
    "STORAGE": {
        "default": {
            "CHECK": "exists",
            "PATH": "probes/ready.txt",
        },
        "s3_media": {
            "CHECK": "write",
            "PREFIX": "deploy-probes",
        },
    },
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
    "TRUSTED_PROXY_NETWORKS": [],
    "CLIENT_IP_HEADER": None,
}
```

`STORAGE` supports two practical modes:

- `CHECK="exists"`: verify that a known probe object exists.
- `CHECK="write"`: create and delete a temporary object to verify write access.

For S3, `exists` is safer when you already manage a sentinel object like `probes/ready.txt`. Use `write` when you want to validate bucket write/delete permissions during readiness checks.

### Timeout contract

There is no global probe timeout. Redis and Celery apply their `TIMEOUT` values only
to operations whose client APIs support a real timeout:

- `REDIS[alias]["TIMEOUT"]`: Redis connect and socket timeout.
- `CELERY["TIMEOUT"]`: Celery broker connection and worker ping timeout.

Database, migration, storage, Celery result backend, and custom checks use their
backend-native timeout configuration. Checks run sequentially, so set Kubernetes
`timeoutSeconds` or an upstream load balancer timeout above the worst-case sum of the
enabled checks.

With `DETAIL_LEVEL="safe"`, recognized timeout exceptions return
`{"status": "fail", "reason": "timeout"}`. See the
[timeout contract](docs/api.md#timeout-contract) for configuration guidance.

## Development

```bash
uv sync --dev
uv run pytest -q
uv run mkdocs build --strict
```

Publishing is handled by `.github/workflows/publish.yml` when a GitHub release is published. Documentation is deployed to GitHub Pages from `main` by `.github/workflows/docs.yml`.
