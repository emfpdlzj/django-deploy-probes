SECRET_KEY = "test-secret-key"
ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django_deploy_probes",
]
ALLOWED_HOSTS = ["testserver"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

DEPLOY_PROBES = {
    "SERVICE_NAME": "test-service",
}
