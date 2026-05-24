from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import reverse


def custom_true_check():
    return True


def custom_false_check():
    return False


def custom_dict_check():
    return {"name": "external_api", "status": "fail", "message": "timeout"}


def custom_raises_check():
    raise RuntimeError("custom check failed")


class CursorMock:
    def __init__(self, should_fail=False):
        self.execute = mock.Mock(side_effect=Exception("db failed") if should_fail else None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class ConnectionMock:
    def __init__(self, should_fail=False):
        self.cursor_mock = CursorMock(should_fail=should_fail)

    def cursor(self):
        return self.cursor_mock


class RedisClientMock:
    def __init__(self, should_fail=False):
        self.ping = mock.Mock(side_effect=Exception("redis failed") if should_fail else None)


class CeleryAppMock:
    def __init__(
        self,
        broker_should_fail=False,
        workers_response=None,
        result_backend_should_fail=False,
    ):
        self.connection = mock.Mock()
        self.connection.__enter__ = mock.Mock(return_value=self.connection)
        self.connection.__exit__ = mock.Mock(return_value=False)
        self.connection.ensure_connection = mock.Mock(
            side_effect=Exception("celery broker failed") if broker_should_fail else None
        )
        self.connection_for_read = mock.Mock(return_value=self.connection)
        self.control = mock.Mock()
        self.control.ping = mock.Mock(
            return_value=[{"worker@example": {"ok": "pong"}}]
            if workers_response is None
            else workers_response
        )
        self.backend = mock.Mock()
        self.backend.get = mock.Mock(
            side_effect=(
                Exception("celery result backend failed") if result_backend_should_fail else None
            )
        )


class MigrationGraphMock:
    def __init__(self, targets):
        self.leaf_nodes = mock.Mock(return_value=targets)


class MigrationLoaderMock:
    def __init__(self, targets):
        self.graph = MigrationGraphMock(targets)


class MigrationExecutorMock:
    def __init__(self, targets, plan):
        self.loader = MigrationLoaderMock(targets)
        self.migration_plan = mock.Mock(return_value=plan)


class ReadyzTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_readyz_returns_200_when_database_is_ok(self):
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {"database.default": "ok"}})
        connection.cursor_mock.execute.assert_called_once_with("SELECT 1")

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_readyz_returns_503_when_database_fails(self):
        connection = ConnectionMock(should_fail=True)

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"database.default": "fail"}},
        )
        connection.cursor_mock.execute.assert_called_once_with("SELECT 1")

    @override_settings(
        DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default", "replica"]}
    )
    def test_readyz_checks_configured_database_aliases(self):
        default_connection = ConnectionMock()
        replica_connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections",
            {"default": default_connection, "replica": replica_connection},
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ready",
                "checks": {
                    "database.default": "ok",
                    "database.replica": "ok",
                },
            },
        )
        default_connection.cursor_mock.execute.assert_called_once_with("SELECT 1")
        replica_connection.cursor_mock.execute.assert_called_once_with("SELECT 1")

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": [], "DATABASES": ["default"]})
    def test_readyz_does_not_check_database_when_database_is_not_enabled(self):
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})
        connection.cursor_mock.execute.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": [],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
            },
        }
    )
    def test_readyz_does_not_check_redis_when_redis_is_not_enabled(self):
        with mock.patch("django_deploy_probes.checks.registry.check_redis") as check_redis:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})
        check_redis.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
            },
        }
    )
    def test_readyz_returns_200_when_redis_ping_is_ok(self):
        client = RedisClientMock()

        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            return_value=client,
        ) as get_redis_client:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {"redis.default": "ok"}})
        get_redis_client.assert_called_once_with("redis://localhost:6379/0", 0.5)
        client.ping.assert_called_once_with()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
            },
        }
    )
    def test_readyz_returns_503_when_redis_ping_fails(self):
        client = RedisClientMock(should_fail=True)

        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            return_value=client,
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"redis.default": "fail"}},
        )
        client.ping.assert_called_once_with()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
                "cache": {
                    "LOCATION": "redis://localhost:6379/1",
                    "TIMEOUT": 0.25,
                },
            },
        }
    )
    def test_readyz_checks_configured_redis_aliases(self):
        clients = [RedisClientMock(), RedisClientMock()]

        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            side_effect=clients,
        ) as get_redis_client:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ready",
                "checks": {
                    "redis.default": "ok",
                    "redis.cache": "ok",
                },
            },
        )
        self.assertEqual(
            get_redis_client.call_args_list,
            [
                mock.call("redis://localhost:6379/0", 0.5),
                mock.call("redis://localhost:6379/1", 0.25),
            ],
        )
        clients[0].ping.assert_called_once_with()
        clients[1].ping.assert_called_once_with()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
            },
        }
    )
    def test_readyz_marks_redis_fail_when_redis_package_is_not_installed(self):
        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            side_effect=ImportError("No module named redis"),
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"redis.default": "fail"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": [],
            "CELERY": {
                "BROKER": True,
                "RESULT_BACKEND": True,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_does_not_check_celery_when_celery_is_not_enabled(self):
        with mock.patch("django_deploy_probes.checks.registry.check_celery") as check_celery:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})
        check_celery.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": True,
                "RESULT_BACKEND": False,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_returns_200_when_celery_broker_check_is_ok(self):
        app = CeleryAppMock()

        with mock.patch("django_deploy_probes.checks.celery._get_celery_app", return_value=app):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {"celery.broker": "ok"}})
        app.connection_for_read.assert_called_once_with()
        app.connection.ensure_connection.assert_called_once_with(max_retries=1, timeout=0.5)
        app.control.ping.assert_not_called()
        app.backend.get.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": True,
                "RESULT_BACKEND": False,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_returns_503_when_celery_broker_check_fails(self):
        app = CeleryAppMock(broker_should_fail=True)

        with mock.patch("django_deploy_probes.checks.celery._get_celery_app", return_value=app):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"celery.broker": "fail"}},
        )
        app.connection_for_read.assert_called_once_with()
        app.connection.ensure_connection.assert_called_once_with(max_retries=1, timeout=0.5)
        app.control.ping.assert_not_called()
        app.backend.get.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": False,
                "WORKERS": True,
                "RESULT_BACKEND": False,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_checks_celery_workers_when_enabled(self):
        app = CeleryAppMock()

        with mock.patch("django_deploy_probes.checks.celery._get_celery_app", return_value=app):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {"celery.workers": "ok"}})
        app.connection_for_read.assert_not_called()
        app.control.ping.assert_called_once_with(timeout=0.5)

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": False,
                "WORKERS": True,
                "RESULT_BACKEND": False,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_returns_503_when_no_celery_workers_respond(self):
        app = CeleryAppMock(workers_response=[])

        with mock.patch("django_deploy_probes.checks.celery._get_celery_app", return_value=app):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"celery.workers": "fail"}},
        )
        app.control.ping.assert_called_once_with(timeout=0.5)

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": False,
                "RESULT_BACKEND": True,
                "TIMEOUT": 0.25,
            },
        }
    )
    def test_readyz_checks_celery_result_backend_when_enabled(self):
        app = CeleryAppMock()

        with mock.patch("django_deploy_probes.checks.celery._get_celery_app", return_value=app):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ready", "checks": {"celery.result_backend": "ok"}},
        )
        app.control.ping.assert_not_called()
        app.backend.get.assert_called_once_with("django-deploy-probes-readyz")

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": True,
                "RESULT_BACKEND": True,
                "TIMEOUT": 0.5,
            },
        }
    )
    def test_readyz_marks_celery_fail_when_celery_package_is_not_installed(self):
        with mock.patch(
            "django_deploy_probes.checks.celery._get_celery_app",
            side_effect=ImportError("No module named celery"),
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "not_ready",
                "checks": {
                    "celery.broker": "fail",
                    "celery.result_backend": "fail",
                },
            },
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": [],
            "MIGRATIONS": {
                "DATABASE": "default",
            },
        }
    )
    def test_readyz_does_not_check_migrations_when_migrations_is_not_enabled(self):
        with mock.patch(
            "django_deploy_probes.checks.registry.check_migrations"
        ) as check_migrations:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})
        check_migrations.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["migrations"],
            "MIGRATIONS": {
                "DATABASE": "replica",
            },
        }
    )
    def test_readyz_returns_200_when_no_unapplied_migrations_exist(self):
        executor = MigrationExecutorMock(targets=[("app", "0001_initial")], plan=[])
        connection = mock.Mock()

        with (
            mock.patch(
                "django_deploy_probes.checks.migrations.connections", {"replica": connection}
            ),
            mock.patch(
                "django_deploy_probes.checks.migrations.MigrationExecutor",
                return_value=executor,
            ) as migration_executor,
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {"migrations": "ok"}})
        migration_executor.assert_called_once_with(connection)
        executor.loader.graph.leaf_nodes.assert_called_once_with()
        executor.migration_plan.assert_called_once_with([("app", "0001_initial")])

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["migrations"],
            "MIGRATIONS": {
                "DATABASE": "default",
            },
        }
    )
    def test_readyz_returns_503_when_unapplied_migrations_exist(self):
        executor = MigrationExecutorMock(
            targets=[("app", "0002_next")],
            plan=[(("app", "0002_next"), False)],
        )

        with (
            mock.patch(
                "django_deploy_probes.checks.migrations.connections", {"default": mock.Mock()}
            ),
            mock.patch(
                "django_deploy_probes.checks.migrations.MigrationExecutor",
                return_value=executor,
            ),
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"migrations": "fail"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["migrations"],
            "MIGRATIONS": {
                "DATABASE": "default",
            },
        }
    )
    def test_readyz_returns_503_when_migration_check_raises_exception(self):
        with mock.patch(
            "django_deploy_probes.checks.migrations.MigrationExecutor",
            side_effect=Exception("migration check failed"),
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"migrations": "fail"}},
        )

    @override_settings(DEPLOY_PROBES={"CUSTOM_CHECKS": []})
    def test_readyz_does_not_run_custom_checks_when_custom_checks_is_empty(self):
        with mock.patch(
            "django_deploy_probes.checks.registry.check_custom_checks"
        ) as check_custom_checks:
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "checks": {}})
        check_custom_checks.assert_not_called()

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_true_check",
            ],
        }
    )
    def test_readyz_returns_200_when_custom_check_returns_true(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ready", "checks": {"custom_true_check": "ok"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_false_check",
            ],
        }
    )
    def test_readyz_returns_503_when_custom_check_returns_false(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"custom_false_check": "fail"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_dict_check",
            ],
        }
    )
    def test_readyz_uses_custom_check_dict_name_status_and_message(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"external_api": "fail"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "EXPOSE_CHECK_MESSAGES": True,
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_dict_check",
            ],
        }
    )
    def test_readyz_uses_custom_check_message_when_explicitly_enabled(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "not_ready",
                "checks": {
                    "external_api": {
                        "status": "fail",
                        "message": "timeout",
                    },
                },
            },
        )

    @override_settings(
        DEPLOY_PROBES={
            "DETAIL_LEVEL": "safe",
            "READY_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0.5,
                },
            },
        }
    )
    def test_readyz_can_return_safe_failure_reason(self):
        with mock.patch(
            "django_deploy_probes.checks.redis._get_redis_client",
            side_effect=ImportError("No module named redis"),
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "not_ready",
                "checks": {
                    "redis.default": {
                        "status": "fail",
                        "reason": "redis_package_missing",
                    },
                },
            },
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.missing_custom_check",
            ],
        }
    )
    def test_readyz_returns_503_when_custom_check_import_fails(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"missing_custom_check": "fail"}},
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_raises_check",
            ],
        }
    )
    def test_readyz_returns_503_when_custom_check_raises_exception(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "checks": {"custom_raises_check": "fail"}},
        )

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": [], "REQUIRE_READY_CHECKS": True})
    def test_readyz_can_require_at_least_one_check(self):
        response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "not_ready", "checks": {}})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["database"],
            "DATABASES": ["default"],
            "INCLUDE_CHECK_DURATIONS": True,
        }
    )
    def test_readyz_can_include_check_duration(self):
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            response = self.client.get(reverse("django_deploy_probes:readyz"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["checks"]["database.default"]["status"], "ok")
        self.assertIsInstance(payload["checks"]["database.default"]["duration_ms"], float)
