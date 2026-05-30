import os
import subprocess
import sys

from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class ImportUsageTestCase(SimpleTestCase):
    def test_package_root_import_does_not_require_configured_django_settings(self):
        env = os.environ.copy()
        env.pop("DJANGO_SETTINGS_MODULE", None)

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import django_deploy_probes; print(django_deploy_probes.__version__)",
            ],
            check=False,
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0.2.0")

    def test_package_root_keeps_view_imports_out_of_public_exports(self):
        import django_deploy_probes

        self.assertEqual(django_deploy_probes.__all__, ["__version__"])
        self.assertFalse(hasattr(django_deploy_probes, "healthz"))
        self.assertFalse(hasattr(django_deploy_probes, "readyz"))
        self.assertFalse(hasattr(django_deploy_probes, "version"))

    @override_settings(ROOT_URLCONF="tests.import_urls")
    def test_import_style_healthz_url(self):
        response = self.client.get(reverse("import-healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(ROOT_URLCONF="tests.import_urls")
    def test_import_style_readyz_url(self):
        response = self.client.get(reverse("import-readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})

    @override_settings(ROOT_URLCONF="tests.import_urls")
    def test_import_style_version_url(self):
        response = self.client.get(reverse("import-version"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "test-service")
