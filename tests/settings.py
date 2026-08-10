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

DEPLOY_PROBES = {
    "SERVICE_NAME": "test-service",
}
