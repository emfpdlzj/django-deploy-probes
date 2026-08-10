from unittest import mock

from django.test import SimpleTestCase

from django_deploy_probes.checks.registry import run_configured_checks


class RegistryTestCase(SimpleTestCase):
    def test_unknown_check_uses_safe_failure_result(self):
        checks = run_configured_checks(
            {
                "DETAIL_LEVEL": "safe",
                "INCLUDE_CHECK_DURATIONS": False,
                "EXPOSE_CHECK_MESSAGES": False,
            },
            ["missing"],
        )

        self.assertEqual(checks, {"missing": {"status": "fail", "reason": "unknown_check"}})

    def test_builtin_and_custom_checks_include_durations_when_enabled(self):
        with mock.patch(
            "django_deploy_probes.checks.registry.check_databases",
            return_value={"database.default": {"status": "ok", "duration_ms": 1.0}},
        ):
            checks = run_configured_checks(
                {
                    "DATABASES": ["default"],
                    "DETAIL_LEVEL": "none",
                    "EXPOSE_CHECK_MESSAGES": True,
                    "INCLUDE_CHECK_DURATIONS": True,
                },
                ["database"],
                custom_check_paths=["tests.test_readyz.custom_dict_check"],
            )

        self.assertEqual(checks["database.default"]["status"], "ok")
        self.assertIn("duration_ms", checks["database.default"])
        self.assertEqual(checks["external_api"]["status"], "fail")
        self.assertEqual(checks["external_api"]["message"], "timeout")
        self.assertIn("duration_ms", checks["external_api"])

    def test_custom_checks_hide_messages_when_message_exposure_is_disabled(self):
        checks = run_configured_checks(
            {
                "DETAIL_LEVEL": "none",
                "EXPOSE_CHECK_MESSAGES": False,
                "INCLUDE_CHECK_DURATIONS": False,
            },
            [],
            custom_check_paths=["tests.test_readyz.custom_dict_check"],
        )

        self.assertEqual(checks, {"external_api": "fail"})

    def test_duplicate_result_names_fail_instead_of_overwriting(self):
        checks = run_configured_checks(
            {
                "DETAIL_LEVEL": "safe",
                "EXPOSE_CHECK_MESSAGES": False,
                "INCLUDE_CHECK_DURATIONS": False,
            },
            [],
            custom_check_paths=[
                "tests.test_readyz.custom_true_check",
                "tests.test_readyz.custom_true_check",
            ],
        )

        self.assertEqual(
            checks,
            {
                "custom_true_check": {
                    "status": "fail",
                    "reason": "duplicate_check_name",
                }
            },
        )
