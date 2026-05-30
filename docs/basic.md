# Basic Setup

## Goal

Add `/healthz`, `/readyz`, `/startupz`, and `/version` to a Django app.

## Final Result

```bash
curl -i http://127.0.0.1:8000/healthz
curl -i http://127.0.0.1:8000/readyz
curl -i http://127.0.0.1:8000/startupz
curl -i http://127.0.0.1:8000/version
```

Expected status codes:

- `/healthz`: `200`
- `/readyz`: `200`
- `/startupz`: `200`
- `/version`: `200`

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
python -m venv .venv
source .venv/bin/activate
pip install django django-deploy-probes
django-admin startproject config .
```

## Full Code

`config/settings.py`

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "local-dev-secret-key"
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
    "SERVICE_NAME": "my-django-app",
    "ENVIRONMENT": "local",
    "VERSION": "0.2.0",
    "COMMIT": "local",
    "BRANCH": "main",
    "BUILD_TIME": "2026-05-17T00:00:00+09:00",
    "SLOT": "local",
    "READY_CHECKS": ["database"],
    "DATABASES": ["default"],
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
python manage.py runserver 127.0.0.1:8000
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/startupz
curl -fsS http://127.0.0.1:8000/version
```

Expected output:

```json
{"status":"ok"}
```

```json
{"status":"ready","checks":{"database.default":"ok"}}
```

```json
{"service":"my-django-app","environment":"local","version":"0.2.0","commit":"local","branch":"main","build_time":"2026-05-17T00:00:00+09:00","slot":"local"}
```

## Failure Checks

If `/readyz` returns `503`, check the database:

```bash
python manage.py migrate
python manage.py dbshell
```

If `/version` returns `403`, check this setting:

```python
DEPLOY_PROBES = {
    "EXPOSE_VERSION": True,
}
```

## Next Step

Use [Docker integration](docker.md) when the app runs in a container.
