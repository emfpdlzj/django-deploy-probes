from django.apps import AppConfig


class DeployProbesConfig(AppConfig):
    name = "django_deploy_probes"
    verbose_name = "Django Deploy Probes"

    def ready(self):
        import django_deploy_probes.django_checks  # noqa: F401
