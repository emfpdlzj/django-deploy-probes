from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class ProbeCacheHeadersTestCase(SimpleTestCase):
    def test_probe_responses_are_not_cacheable(self):
        for name in ("healthz", "readyz", "startupz", "version"):
            with self.subTest(name=name):
                response = self.client.get(reverse(f"django_deploy_probes:{name}"))

                self.assertIn("no-store", response.headers["Cache-Control"])

    @override_settings(DEPLOY_PROBES={"EXPOSE_VERSION": False})
    def test_forbidden_version_response_is_not_cacheable(self):
        response = self.client.get(reverse("django_deploy_probes:version"))

        self.assertEqual(response.status_code, 403)
        self.assertIn("no-store", response.headers["Cache-Control"])
