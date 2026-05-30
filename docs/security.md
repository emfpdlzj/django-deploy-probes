# Security Options

## Goal

Protect `/startupz`, `/readyz`, and `/version` with an internal IP rule or a probe token.

## Final Result

```bash
curl -i http://127.0.0.1:8000/version
curl -i -H "X-Probe-Token: local-probe-token" http://127.0.0.1:8000/version
```

Expected status codes:

- Missing token: `403`
- Correct token: `200`

## File Structure

```text
myapp/
  manage.py
  config/
    __init__.py
    settings.py
    urls.py
```

## Install

```bash
pip install django django-deploy-probes
```

## Full Code

`config/settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "security-local-secret")
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ROOT_URLCONF = "config.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_deploy_probes",
]

MIDDLEWARE = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEPLOY_PROBES = {
    "SERVICE_NAME": "secure-django-app",
    "ENVIRONMENT": os.getenv("DJANGO_ENV", "local"),
    "VERSION": os.getenv("APP_VERSION", "0.2.0"),
    "COMMIT": os.getenv("GIT_COMMIT", "local"),
    "BRANCH": os.getenv("GIT_BRANCH", "main"),
    "BUILD_TIME": os.getenv("BUILD_TIME", "2026-05-17T00:00:00+09:00"),
    "SLOT": os.getenv("DEPLOY_SLOT", "local"),
    "READY_CHECKS": ["database"],
    "DATABASES": ["default"],
    "HEADER_TOKEN_VALIDATION": {
        "HEADER_NAME": "X-Probe-Token",
        "TOKEN": os.getenv("PROBE_TOKEN", "local-probe-token"),
        "PROTECT_HEALTHZ": False,
    },
    "INTERNAL_IP_NETWORKS": [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ],
}
```

`config/urls.py`

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

## Run

```bash
python manage.py migrate
PROBE_TOKEN=local-probe-token python manage.py runserver 127.0.0.1:8000
```

## Verify

`/healthz` stays open when `PROTECT_HEALTHZ` is `False`:

```bash
curl -i http://127.0.0.1:8000/healthz
```

Missing token fails:

```bash
curl -i http://127.0.0.1:8000/readyz
curl -i http://127.0.0.1:8000/startupz
curl -i http://127.0.0.1:8000/version
```

Correct token succeeds:

```bash
curl -fsS -H "X-Probe-Token: local-probe-token" http://127.0.0.1:8000/readyz
curl -fsS -H "X-Probe-Token: local-probe-token" http://127.0.0.1:8000/startupz
curl -fsS -H "X-Probe-Token: local-probe-token" http://127.0.0.1:8000/version
```

## Failure Checks

If every endpoint returns `403`, check whether healthz protection is enabled:

```python
"PROTECT_HEALTHZ": False
```

If proxy traffic is blocked, check whether Django is seeing the proxy hop in `REMOTE_ADDR`. When
probes are behind a trusted reverse proxy, configure `TRUSTED_PROXY_NETWORKS` and
`CLIENT_IP_HEADER` so internal IP checks can evaluate the original client IP safely.

If your probe traffic comes from a load balancer or private service network, add that CIDR to
`INTERNAL_IP_NETWORKS`.

## Trusted Reverse Proxy

When probes are served behind ALB, Nginx, or an ingress controller, `REMOTE_ADDR` may be the
proxy hop instead of the original client. In that case, configure a narrow trusted proxy CIDR
list and the header that carries the client IP.

```python
DEPLOY_PROBES = {
    "INTERNAL_IP_ONLY": True,
    "INTERNAL_IP_NETWORKS": [
        "10.0.0.0/8",
        "192.168.0.0/16",
    ],
    "TRUSTED_PROXY_NETWORKS": [
        "192.0.2.10/32",
        "192.0.2.11/32",
    ],
    "CLIENT_IP_HEADER": "X-Forwarded-For",
}
```

Rules:

- If `REMOTE_ADDR` is not in `TRUSTED_PROXY_NETWORKS`, forwarded headers are ignored.
- If `CLIENT_IP_HEADER` is `X-Forwarded-For`, the package walks the proxy chain from right to
  left and treats the last untrusted hop as the client IP.
- Keep `TRUSTED_PROXY_NETWORKS` as narrow as possible. Do not trust an entire private range
  unless every host in that range is an authorized proxy.
- If your proxy uses a single-value header such as `X-Real-IP`, set `CLIENT_IP_HEADER` to that
  header name instead.

## Next Step

Use the token in CI/CD deployment validation:

```bash
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" https://app.example.com/readyz
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" https://app.example.com/startupz
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" https://app.example.com/version
```
