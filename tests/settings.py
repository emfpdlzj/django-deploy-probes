import os


SECRET_KEY = "test-secret-key"
ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django_deploy_probes",
]
ALLOWED_HOSTS = ["testserver"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

if os.environ.get("DEPLOY_PROBES_POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["DEPLOY_PROBES_POSTGRES_HOST"],
            "PORT": os.environ.get("DEPLOY_PROBES_POSTGRES_PORT", "5432"),
            "NAME": os.environ.get("DEPLOY_PROBES_POSTGRES_DB", "deploy_probes"),
            "USER": os.environ.get("DEPLOY_PROBES_POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("DEPLOY_PROBES_POSTGRES_PASSWORD", ""),
        }
    }

DEPLOY_PROBES = {
    "SERVICE_NAME": "test-service",
}
