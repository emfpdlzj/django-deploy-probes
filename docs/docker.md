# Docker Integration

## Goal

Run a Django app with `django-deploy-probes` and Docker `HEALTHCHECK`.

## Final Result

```bash
docker build -t django-probes-demo .
docker run --rm -p 8000:8000 django-probes-demo
curl -fsS http://127.0.0.1:8000/healthz
```

## File Structure

```text
myapp/
  Dockerfile
  requirements.txt
  manage.py
  config/
    __init__.py
    settings.py
    urls.py
```

## Install

```bash
mkdir myapp
cd myapp
python -m venv .venv
source .venv/bin/activate
pip install django django-deploy-probes gunicorn
pip freeze > requirements.txt
django-admin startproject config .
```

## Full Code

`Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV APP_VERSION=0.1.0
ENV GIT_COMMIT=local
ENV GIT_BRANCH=main
ENV BUILD_TIME=2026-05-17T00:00:00+09:00
ENV DEPLOY_SLOT=blue

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py migrate --noinput

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl --fail http://127.0.0.1:8000/healthz || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

`config/settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "docker-local-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
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
    "SERVICE_NAME": "docker-django-app",
    "ENVIRONMENT": os.getenv("DJANGO_ENV", "prod"),
    "VERSION": os.getenv("APP_VERSION", "unknown"),
    "COMMIT": os.getenv("GIT_COMMIT", "unknown"),
    "BRANCH": os.getenv("GIT_BRANCH", "unknown"),
    "BUILD_TIME": os.getenv("BUILD_TIME", "unknown"),
    "SLOT": os.getenv("DEPLOY_SLOT", "unknown"),
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
docker build -t django-probes-demo .
docker run --rm -p 8000:8000 django-probes-demo
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
docker ps --filter name=django-probes-demo
```

## Failure Checks

If Docker health is `unhealthy`, inspect the container:

```bash
docker ps
docker inspect --format='{{json .State.Health}}' CONTAINER_ID
docker logs CONTAINER_ID
```

If `/readyz` returns `503`, run:

```bash
docker exec -it CONTAINER_ID python manage.py migrate --noinput
```

## Next Step

Use [Docker Compose integration](docker-compose.md) when the app depends on Redis or another service.

