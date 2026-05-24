from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "basic-example-secret"
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
    "SERVICE_NAME": "basic-example",
    "ENVIRONMENT": "local",
    "VERSION": "0.1.0",
    "COMMIT": "local",
    "BRANCH": "main",
    "BUILD_TIME": "2026-05-17T00:00:00+09:00",
    "SLOT": "local",
    "READY_CHECKS": ["database"],
    "DATABASES": ["default"],
}
