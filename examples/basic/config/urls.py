from django.urls import include, path


urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
