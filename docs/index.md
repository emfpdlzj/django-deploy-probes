# django-deploy-probes

Production-ready HTTP deployment probe endpoints for Django applications.

Use this package when you need lightweight runtime endpoints for CI/CD validation, Docker health checks, Kubernetes probes, blue-green deployments, and rollback checks.

## Endpoints

| Endpoint | Purpose | Typical use |
| --- | --- | --- |
| `/healthz` | Process liveness | Docker `HEALTHCHECK`, Kubernetes `livenessProbe` |
| `/readyz` | Dependency-aware readiness | Blue-green validation, Kubernetes `readinessProbe` |
| `/startupz` | Startup/bootstrap readiness | Pending migration checks before traffic |
| `/version` | Build and deployment metadata | Slot verification, rollback validation |

## Install

```bash
pip install django-deploy-probes
```

Optional checks are available as extras:

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[openapi]"
pip install "django-deploy-probes[all]"
```

## Quick Start

Add the app so Django system checks can validate probe settings:

```python
INSTALLED_APPS = [
    "django_deploy_probes",
]
```

Include the URL configuration:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

Verify the endpoints:

```bash
curl -f http://localhost:8000/healthz
curl -f http://localhost:8000/readyz
curl -f http://localhost:8000/version
```

## Read Next

- [Basic setup](basic.md)
- [Endpoint reference](api.md)
- [Security options](security.md)
- [Docker integration](docker.md)
- [Kubernetes probes](kubernetes.md)
- [GitHub Actions deployment validation](recipes/github-actions.md)

## Security Note

Probe endpoints are operational endpoints. Keep readiness and version metadata internal or protect them with the package security options before exposing them outside a trusted network.
