from django.urls import path

from django_deploy_probes.views import healthz, readyz, startupz, version


app_name = "django_deploy_probes"

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("readyz", readyz, name="readyz"),
    path("startupz", startupz, name="startupz"),
    path("version", version, name="version"),
]
