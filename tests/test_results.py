from unittest import mock

from django.test import SimpleTestCase

from django_deploy_probes.checks.results import (
    check_is_ok,
    failure_result_for_exception,
    is_timeout_exception,
    normalize_check_result,
    run_check,
    run_named_checks,
)


class ReadTimeoutError(Exception):
    pass


class ResultsTestCase(SimpleTestCase):
    def test_check_is_ok_supports_string_and_dict_results(self):
        self.assertTrue(check_is_ok("ok"))
        self.assertTrue(check_is_ok({"status": "ok"}))
        self.assertFalse(check_is_ok("fail"))
        self.assertFalse(check_is_ok({"status": "fail"}))

    def test_normalize_check_result_adds_missing_status(self):
        self.assertEqual(normalize_check_result("ok"), {"status": "ok"})
        self.assertEqual(normalize_check_result("fail"), {"status": "fail"})
        self.assertEqual(
            normalize_check_result({"message": "timeout"}),
            {"status": "fail", "message": "timeout"},
        )

    def test_run_check_adds_normalized_duration_metadata(self):
        with mock.patch(
            "django_deploy_probes.checks.results.perf_counter",
            side_effect=[10.0, 10.01234],
        ):
            result = run_check(
                lambda: {"message": "timeout"},
                include_duration=True,
            )

        self.assertEqual(
            result,
            {"status": "fail", "message": "timeout", "duration_ms": 12.34},
        )

    def test_run_named_checks_times_one_custom_check_execution(self):
        with mock.patch(
            "django_deploy_probes.checks.results.perf_counter",
            side_effect=[10.0, 10.01234],
        ):
            results = run_named_checks(
                lambda: {
                    "database.default": "ok",
                    "external_api": {"message": "timeout"},
                },
                include_duration=True,
            )

        self.assertEqual(
            results,
            {
                "database.default": {"status": "ok", "duration_ms": 12.34},
                "external_api": {
                    "status": "fail",
                    "message": "timeout",
                    "duration_ms": 12.34,
                },
            },
        )

    def test_run_check_returns_raw_result_when_disabled(self):
        result = run_check(lambda: "ok", include_duration=False)

        self.assertEqual(result, "ok")

    def test_timeout_detection_supports_builtin_and_backend_exceptions(self):
        self.assertTrue(is_timeout_exception(TimeoutError()))
        self.assertTrue(is_timeout_exception(ReadTimeoutError()))
        self.assertFalse(is_timeout_exception(RuntimeError()))

    def test_timeout_detection_walks_wrapped_exception_chain(self):
        try:
            try:
                raise TimeoutError("socket timed out")
            except TimeoutError as exc:
                raise RuntimeError("backend request failed") from exc
        except RuntimeError as exc:
            self.assertTrue(is_timeout_exception(exc))

    def test_exception_failure_result_uses_timeout_safe_reason(self):
        self.assertEqual(
            failure_result_for_exception(TimeoutError(), "query_failed", "safe"),
            {"status": "fail", "reason": "timeout"},
        )
        self.assertEqual(
            failure_result_for_exception(TimeoutError(), "query_failed", "none"),
            "fail",
        )
