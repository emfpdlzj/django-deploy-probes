from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class VersionTestCase(SimpleTestCase):
    def test_version_returns_default_values(self):
        response = self.client.get(reverse("django_deploy_probes:version"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "service": "test-service",
                "environment": "local",
                "version": "unknown",
            },
        )

    @override_settings(
        DEPLOY_PROBES={
            "SERVICE_NAME": "billing-api",
            "ENVIRONMENT": "prod",
            "VERSION": "1.2.0",
            "COMMIT": "a1b2c3d",
            "BRANCH": "main",
            "BUILD_TIME": "2026-05-13T10:00:00+09:00",
            "SLOT": "green",
        }
    )
    def test_version_uses_deploy_probes_settings(self):
        response = self.client.get(reverse("django_deploy_probes:version"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "service": "billing-api",
                "environment": "prod",
                "version": "1.2.0",
            },
        )

    @override_settings(
        DEPLOY_PROBES={
            "SERVICE_NAME": "billing-api",
            "ENVIRONMENT": "prod",
            "VERSION": "1.2.0",
            "COMMIT": "a1b2c3d",
            "BRANCH": "main",
            "BUILD_TIME": "2026-05-13T10:00:00+09:00",
            "SLOT": "green",
            "EXPOSE_BUILD_INFO": True,
        }
    )
    def test_version_exposes_build_info_only_when_enabled(self):
        response = self.client.get(reverse("django_deploy_probes:version"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "service": "billing-api",
                "environment": "prod",
                "version": "1.2.0",
                "commit": "a1b2c3d",
                "branch": "main",
                "build_time": "2026-05-13T10:00:00+09:00",
                "slot": "green",
            },
        )

    @override_settings(DEPLOY_PROBES={"EXPOSE_VERSION": False})
    def test_version_returns_forbidden_when_expose_version_is_false(self):
        response = self.client.get(reverse("django_deploy_probes:version"))

        self.assertEqual(response.status_code, 403)
