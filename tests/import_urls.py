from django.urls import path

from django_deploy_probes.views import healthz, readyz, version


urlpatterns = [
    path("healthz/", healthz, name="import-healthz"),
    path("readyz/", readyz, name="import-readyz"),
    path("version/", version, name="import-version"),
]
