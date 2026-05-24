from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from tests.test_readyz import custom_false_check, custom_true_check


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


class StartupzTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"STARTUP_CHECKS": []})
    def test_startupz_returns_200_when_no_startup_checks_are_required(self):
        response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "started", "checks": {}})

    @override_settings(DEPLOY_PROBES={"STARTUP_CHECKS": [], "REQUIRE_STARTUP_CHECKS": True})
    def test_startupz_can_require_at_least_one_check(self):
        response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "not_started", "checks": {}})

    @override_settings(
        DEPLOY_PROBES={
            "STARTUP_CHECKS": ["migrations"],
            "MIGRATIONS": {
                "DATABASE": "default",
            },
        }
    )
    def test_startupz_returns_200_when_migrations_are_applied(self):
        executor = MigrationExecutorMock(targets=[("app", "0001_initial")], plan=[])

        with (
            mock.patch(
                "django_deploy_probes.checks.migrations.connections", {"default": mock.Mock()}
            ),
            mock.patch(
                "django_deploy_probes.checks.migrations.MigrationExecutor",
                return_value=executor,
            ),
        ):
            response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "started", "checks": {"migrations": "ok"}})

    @override_settings(
        DEPLOY_PROBES={
            "STARTUP_CHECKS": ["migrations"],
            "MIGRATIONS": {
                "DATABASE": "default",
            },
        }
    )
    def test_startupz_returns_503_when_migrations_are_unapplied(self):
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
            response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"status": "not_started", "checks": {"migrations": "fail"}}
        )

    @override_settings(
        DEPLOY_PROBES={
            "CUSTOM_CHECKS": [
                "tests.test_readyz.custom_false_check",
            ],
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_false_check",
            ],
            "STARTUP_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_true_check",
            ],
        }
    )
    def test_startupz_uses_only_startup_custom_checks(self):
        self.assertIs(custom_false_check(), False)
        self.assertIs(custom_true_check(), True)

        response = self.client.get(reverse("django_deploy_probes:startupz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "started", "checks": {"custom_true_check": "ok"}},
        )
