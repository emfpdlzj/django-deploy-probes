from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from tests.test_readyz import ConnectionMock


class DeployProbesCommandTestCase(SimpleTestCase):
    def test_healthz_can_render_json(self):
        stdout = StringIO()

        call_command("deploy_probes", "healthz", "--json", stdout=stdout)

        self.assertEqual(stdout.getvalue().strip(), '{"status": "ok"}')

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_readyz_returns_exit_code_0_when_probe_passes(self):
        stdout = StringIO()
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            call_command("deploy_probes", "readyz", "--json", stdout=stdout)

        self.assertEqual(
            stdout.getvalue().strip(),
            '{"status": "ready", "checks": {"database.default": "ok"}}',
        )

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_readyz_plain_output_renders_multiline_check_summary(self):
        stdout = StringIO()
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            call_command("deploy_probes", "readyz", stdout=stdout)

        self.assertEqual(stdout.getvalue().strip(), "ready\ndatabase.default: ok")

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["database"], "DATABASES": ["default"]})
    def test_readyz_returns_exit_code_1_when_probe_fails(self):
        stdout = StringIO()
        connection = ConnectionMock(should_fail=True)

        with (
            mock.patch("django_deploy_probes.checks.database.connections", {"default": connection}),
            self.assertRaises(SystemExit) as exc_info,
        ):
            call_command("deploy_probes", "readyz", "--json", stdout=stdout)

        self.assertEqual(exc_info.exception.code, 1)
        self.assertEqual(
            stdout.getvalue().strip(),
            '{"status": "not_ready", "checks": {"database.default": "fail"}}',
        )

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["database"],
            "DATABASES": ["default"],
            "INCLUDE_CHECK_DURATIONS": True,
        }
    )
    def test_readyz_plain_output_formats_dict_check_results(self):
        stdout = StringIO()
        connection = ConnectionMock()

        with mock.patch(
            "django_deploy_probes.checks.database.connections", {"default": connection}
        ):
            call_command("deploy_probes", "readyz", stdout=stdout)

        lines = stdout.getvalue().strip().splitlines()
        self.assertEqual(lines[0], "ready")
        self.assertIn('database.default: {"status": "ok", "duration_ms": ', lines[1])

    @override_settings(DEPLOY_PROBES={"EXPOSE_VERSION": False})
    def test_version_remains_available_from_cli(self):
        stdout = StringIO()

        call_command("deploy_probes", "version", "--json", stdout=stdout)

        self.assertEqual(
            stdout.getvalue().strip(),
            '{"service": "django-app", "environment": "local", "version": "unknown"}',
        )

    def test_version_plain_output_renders_key_value_lines(self):
        stdout = StringIO()

        call_command("deploy_probes", "version", stdout=stdout)

        self.assertEqual(
            stdout.getvalue().strip(),
            "service=test-service\nenvironment=local\nversion=unknown",
        )

    @override_settings(DEPLOY_PROBES={"DETAIL_LEVEL": "verbose"})
    def test_command_returns_exit_code_2_for_invalid_settings(self):
        stdout = StringIO()
        stderr = StringIO()

        with self.assertRaises(SystemExit) as exc_info:
            call_command("deploy_probes", "healthz", "--json", stdout=stdout, stderr=stderr)

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("DETAIL_LEVEL", stderr.getvalue())

    def test_command_returns_exit_code_3_for_unexpected_execution_failure(self):
        stdout = StringIO()
        stderr = StringIO()

        with (
            mock.patch(
                "django_deploy_probes.management.commands.deploy_probes.run_probe",
                side_effect=RuntimeError("boom"),
            ),
            self.assertRaises(SystemExit) as exc_info,
        ):
            call_command("deploy_probes", "healthz", "--json", stdout=stdout, stderr=stderr)

        self.assertEqual(exc_info.exception.code, 3)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("boom", stderr.getvalue())
