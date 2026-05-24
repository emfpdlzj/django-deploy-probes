# Docker Compose Integration

## Goal

Run `/readyz` with database and Redis checks in Docker Compose.

## Final Result

```bash
docker compose up --build
curl -fsS http://127.0.0.1:8000/readyz
```

Expected output:

```json
{"status":"ready","checks":{"database.default":"ok","redis.default":"ok"}}
```

## File Structure

```text
myapp/
  Dockerfile
  docker-compose.yml
  requirements.txt
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
pip install django "django-deploy-probes[redis]" gunicorn
pip freeze > requirements.txt
django-admin startproject config .
```

## Full Code

`docker-compose.yml`

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      DJANGO_ENV: prod
      APP_VERSION: 0.1.0
      GIT_COMMIT: local
      GIT_BRANCH: main
      BUILD_TIME: "2026-05-17T00:00:00+09:00"
      DEPLOY_SLOT: green
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://127.0.0.1:8000/healthz"]
      interval: 10s
      timeout: 3s
      retries: 3

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
```

`Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py migrate --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

`config/settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "compose-local-secret")
DEBUG = False
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
    "SERVICE_NAME": "compose-django-app",
    "ENVIRONMENT": os.getenv("DJANGO_ENV", "prod"),
    "VERSION": os.getenv("APP_VERSION", "unknown"),
    "COMMIT": os.getenv("GIT_COMMIT", "unknown"),
    "BRANCH": os.getenv("GIT_BRANCH", "unknown"),
    "BUILD_TIME": os.getenv("BUILD_TIME", "unknown"),
    "SLOT": os.getenv("DEPLOY_SLOT", "unknown"),
    "READY_CHECKS": ["database", "redis"],
    "DATABASES": ["default"],
    "REDIS": {
        "default": {
            "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
            "TIMEOUT": 1.0,
        }
    },
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
docker compose up --build
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
```

## Failure Checks

Stop Redis and verify `/readyz` fails:

```bash
docker compose stop redis
curl -i http://127.0.0.1:8000/readyz
```

Expected status:

```text
HTTP/1.1 503 Service Unavailable
```

Restart Redis:

```bash
docker compose start redis
curl -fsS http://127.0.0.1:8000/readyz
```

## Next Step

Use [Kubernetes probes](kubernetes.md) for rolling deployments.

