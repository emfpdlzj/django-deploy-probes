# django-deploy-probes

Production-ready HTTP deployment probe endpoints for Django applications.

Use `django-deploy-probes` for CI/CD deployment validation, Docker health checks, Kubernetes probes, blue-green deployments, and rollback checks.

[![PyPI](https://img.shields.io/pypi/v/django-deploy-probes.svg?label=PyPI)](https://pypi.org/project/django-deploy-probes/)
[![Django Packages](https://img.shields.io/badge/Django%20Packages-django--deploy--probes-0c4b33.svg)](https://djangopackages.org/packages/p/django-deploy-probes/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-3776AB.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-%3E%3D4.2-0C4B33.svg)](https://www.djangoproject.com/)
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

Verify:

```bash
curl -f http://localhost:8000/healthz
curl -f http://localhost:8000/readyz
curl -f http://localhost:8000/version
```

## Development

```bash
uv sync --dev
uv run pytest -q
uv run mkdocs build --strict
```

Publishing is handled by `.github/workflows/publish.yml` when a GitHub release is published. Documentation is deployed to GitHub Pages from `main` by `.github/workflows/docs.yml`.
