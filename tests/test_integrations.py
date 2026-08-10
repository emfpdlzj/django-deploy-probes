import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless

from django.test import TestCase, override_settings
from django.urls import reverse


class DjangoBackendIntegrationTestCase(TestCase):
    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_database_probe_uses_the_configured_django_database(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"database.default": "ok"})

    def test_storage_probe_uses_the_configured_django_storage(self):
        with TemporaryDirectory() as location:
            with self.settings(
                STORAGES={
                    "probe": {
                        "BACKEND": "django.core.files.storage.FileSystemStorage",
                        "OPTIONS": {"location": location},
                    }
                },
                DEPLOY_PROBES={
                    "READY_CHECKS": ["storage"],
                    "STORAGE": {"probe": {"CHECK": "write"}},
                },
            ):
                response = self.client.get(reverse("django_deploy_probes:readyz"))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["checks"], {"storage.probe": "ok"})
            self.assertFalse(any(path.is_file() for path in Path(location).rglob("*")))


@skipUnless(os.environ.get("DEPLOY_PROBES_REDIS_URL"), "Redis integration URL is not set")
class RedisIntegrationTestCase(TestCase):
    def test_redis_probe_pings_a_real_redis_server(self):
        with self.settings(
            DEPLOY_PROBES={
                "READY_CHECKS": ["redis"],
                "REDIS": {
                    "integration": {
                        "LOCATION": os.environ["DEPLOY_PROBES_REDIS_URL"],
                        "TIMEOUT": 1.0,
                    }
                },
            }
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"redis.integration": "ok"})
