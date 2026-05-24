import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "compose-example-secret")
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
    "SERVICE_NAME": "compose-example",
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
