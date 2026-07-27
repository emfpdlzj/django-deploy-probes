from unittest import mock

from django.test import SimpleTestCase

from django_deploy_probes.checks.celery import check_celery
from django_deploy_probes.checks.custom import check_custom_checks
from django_deploy_probes.checks.database import check_databases
from django_deploy_probes.checks.migrations import check_migrations
from django_deploy_probes.checks.redis import check_redis
from django_deploy_probes.checks.storage import check_storage


class ReadTimeoutError(Exception):
    pass


def custom_timeout_check():
    raise TimeoutError("custom dependency timed out")


class TimeoutContractTestCase(SimpleTestCase):
    def test_database_timeout_uses_safe_timeout_reason(self):
        connection = mock.MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = TimeoutError("database timed out")

        with mock.patch(
            "django_deploy_probes.checks.database.connections",
            {"default": connection},
        ):
            results = check_databases(["default"], detail_level="safe")

        self.assertEqual(
            results,
            {"database.default": {"status": "fail", "reason": "timeout"}},
        )

    def test_redis_timeout_uses_safe_timeout_reason(self):
        client = mock.Mock()
        client.ping.side_effect = ReadTimeoutError("redis timed out")

        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            return_value=client,
        ):
            results = check_redis(
                {
                    "default": {
                        "LOCATION": "redis://localhost:6379/0",
                        "TIMEOUT": 0.5,
                    }
                },
                detail_level="safe",
            )

        self.assertEqual(
            results,
            {"redis.default": {"status": "fail", "reason": "timeout"}},
        )

    def test_celery_broker_timeout_uses_safe_timeout_reason(self):
        app = mock.MagicMock()
        connection = app.connection_for_read.return_value.__enter__.return_value
        connection.ensure_connection.side_effect = TimeoutError("broker timed out")

        with mock.patch(
            "django_deploy_probes.checks.celery._get_celery_app",
            return_value=app,
        ):
            results = check_celery(
                {
                    "BROKER": True,
                    "WORKERS": False,
                    "RESULT_BACKEND": False,
                    "TIMEOUT": 0.5,
                },
                detail_level="safe",
            )

        self.assertEqual(
            results,
            {"celery.broker": {"status": "fail", "reason": "timeout"}},
        )
        connection.ensure_connection.assert_called_once_with(max_retries=1, timeout=0.5)

    def test_celery_result_backend_uses_backend_native_timeout(self):
        app = mock.Mock()
        app.backend.get.side_effect = ReadTimeoutError("result backend timed out")

        with mock.patch(
            "django_deploy_probes.checks.celery._get_celery_app",
            return_value=app,
        ):
            results = check_celery(
                {
                    "BROKER": False,
                    "WORKERS": False,
                    "RESULT_BACKEND": True,
                    "TIMEOUT": 0.5,
                },
                detail_level="safe",
            )

        self.assertEqual(
            results,
            {"celery.result_backend": {"status": "fail", "reason": "timeout"}},
        )
        app.backend.get.assert_called_once_with("django-deploy-probes-readyz")

    def test_storage_timeout_uses_safe_timeout_reason(self):
        storage = mock.Mock()
        storage.exists.side_effect = ReadTimeoutError("storage timed out")

        with mock.patch(
            "django_deploy_probes.checks.storage.storages",
            {"default": storage},
        ):
            results = check_storage(
                {
                    "default": {
                        "CHECK": "exists",
                        "PATH": "probes/ready.txt",
                    }
                },
                detail_level="safe",
            )

        self.assertEqual(
            results,
            {"storage.default": {"status": "fail", "reason": "timeout"}},
        )

    def test_migration_timeout_uses_safe_timeout_reason(self):
        with mock.patch(
            "django_deploy_probes.checks.migrations.MigrationExecutor",
            side_effect=TimeoutError("migration query timed out"),
        ):
            results = check_migrations(
                {"DATABASE": "default"},
                detail_level="safe",
            )

        self.assertEqual(
            results,
            {"migrations": {"status": "fail", "reason": "timeout"}},
        )

    def test_custom_timeout_uses_safe_timeout_reason(self):
        results = check_custom_checks(
            ["tests.test_timeout_contract.custom_timeout_check"],
            detail_level="safe",
        )

        self.assertEqual(
            results,
            {"custom_timeout_check": {"status": "fail", "reason": "timeout"}},
        )
