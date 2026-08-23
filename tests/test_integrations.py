import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock, skipUnless

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

    @skipUnless(
        os.environ.get("DEPLOY_PROBES_POSTGRES_HOST"),
        "PostgreSQL integration settings are not set",
    )
    def test_database_and_migration_probes_use_postgresql(self):
        from django.db import connection

        self.assertEqual(connection.vendor, "postgresql")

        with self.settings(
            DEPLOY_PROBES={
                "READY_CHECKS": ["database"],
                "STARTUP_CHECKS": ["migrations"],
                "DATABASES": ["default"],
                "MIGRATIONS": {"DATABASE": "default"},
            }
        ):
            ready_response = self.client.get(reverse("django_deploy_probes:readyz"))
            startup_response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(ready_response.status_code, 200)
        self.assertEqual(ready_response.json()["checks"], {"database.default": "ok"})
        self.assertEqual(startup_response.status_code, 200)
        self.assertEqual(startup_response.json()["checks"], {"migrations": "ok"})


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

    def test_celery_broker_and_result_backend_use_real_redis(self):
        from celery import Celery

        redis_url = os.environ["DEPLOY_PROBES_REDIS_URL"]
        celery_app = Celery("deploy-probes-integration", broker=redis_url, backend=redis_url)
        try:
            with (
                mock.patch(
                    "django_deploy_probes.checks.celery._get_celery_app",
                    return_value=celery_app,
                ),
                self.settings(
                    DEPLOY_PROBES={
                        "READY_CHECKS": ["celery"],
                        "CELERY": {
                            "BROKER": True,
                            "RESULT_BACKEND": True,
                            "TIMEOUT": 1.0,
                        },
                    }
                ),
            ):
                response = self.client.get(reverse("django_deploy_probes:readyz"))
        finally:
            celery_app.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["checks"],
            {
                "celery.broker": "ok",
                "celery.result_backend": "ok",
            },
        )


@skipUnless(os.environ.get("DEPLOY_PROBES_S3_ENDPOINT"), "S3 integration settings are not set")
class S3StorageIntegrationTestCase(TestCase):
    bucket_name = "django-deploy-probes"
    sentinel_path = "probes/ready.txt"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import boto3

        cls.s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ["DEPLOY_PROBES_S3_ENDPOINT"],
            aws_access_key_id=os.environ["DEPLOY_PROBES_S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["DEPLOY_PROBES_S3_SECRET_KEY"],
            region_name="us-east-1",
        )
        cls.s3_client.create_bucket(Bucket=cls.bucket_name)
        cls.s3_client.put_object(
            Bucket=cls.bucket_name,
            Key=cls.sentinel_path,
            Body=b"ready\n",
        )

    @classmethod
    def tearDownClass(cls):
        objects = cls.s3_client.list_objects_v2(Bucket=cls.bucket_name).get("Contents", [])
        for item in objects:
            cls.s3_client.delete_object(Bucket=cls.bucket_name, Key=item["Key"])
        cls.s3_client.delete_bucket(Bucket=cls.bucket_name)
        super().tearDownClass()

    def _storage_settings(self, check_config):
        return self.settings(
            STORAGES={
                "probe": {
                    "BACKEND": "storages.backends.s3.S3Storage",
                    "OPTIONS": {
                        "bucket_name": self.bucket_name,
                        "endpoint_url": os.environ["DEPLOY_PROBES_S3_ENDPOINT"],
                        "access_key": os.environ["DEPLOY_PROBES_S3_ACCESS_KEY"],
                        "secret_key": os.environ["DEPLOY_PROBES_S3_SECRET_KEY"],
                        "region_name": "us-east-1",
                    },
                }
            },
            DEPLOY_PROBES={
                "READY_CHECKS": ["storage"],
                "STORAGE": {"probe": check_config},
            },
        )

    def test_s3_exists_probe_reads_a_sentinel_object(self):
        with self._storage_settings({"CHECK": "exists", "PATH": self.sentinel_path}):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"storage.probe": "ok"})

    def test_s3_write_probe_removes_the_temporary_object(self):
        with self._storage_settings({"CHECK": "write", "PREFIX": "integration"}):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"storage.probe": "ok"})
        keys = {
            item["Key"]
            for item in self.s3_client.list_objects_v2(Bucket=self.bucket_name).get("Contents", [])
        }
        self.assertEqual(keys, {self.sentinel_path})
