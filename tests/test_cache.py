import json
from io import StringIO
from unittest import mock

from django.core.cache import caches
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from django_deploy_probes.checks.cache import check_caches


class CacheProbeTestCase(SimpleTestCase):
    @override_settings(
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "probe": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        },
        DEPLOY_PROBES={"READY_CHECKS": ["cache"], "STARTUP_CHECKS": ["cache"], "CACHES": ["probe"]},
    )
    def test_real_cache_http_and_cli_round_trip_leaves_existing_data_intact(self):
        caches["probe"].set("application-key", "keep")
        try:
            for endpoint, status in (("readyz", "ready"), ("startupz", "started")):
                response = self.client.get(f"/{endpoint}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(), {"status": status, "checks": {"cache.probe": "ok"}}
                )
                output = StringIO()
                call_command("deploy_probes", endpoint, "--json", stdout=output)
                self.assertEqual(json.loads(output.getvalue()), response.json())
            self.assertEqual(caches["probe"].get("application-key"), "keep")
            self.assertEqual(len(caches["probe"]._cache), 1)
        finally:
            caches["probe"].clear()

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
        DEPLOY_PROBES={"READY_CHECKS": ["cache"], "DETAIL_LEVEL": "safe"},
    )
    def test_dummy_cache_fails_http_and_cli(self):
        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["cache.default"]["reason"], "value_mismatch")
        with self.assertRaises(SystemExit) as raised:
            call_command("deploy_probes", "readyz", "--json", stdout=StringIO())
        self.assertEqual(raised.exception.code, 1)

    def test_unique_keys_and_cleanup_after_read_failure(self):
        cache = mock.Mock()
        cache.get.side_effect = TimeoutError("secret cache address")
        with mock.patch("django_deploy_probes.checks.cache.caches", {"one": cache, "two": cache}):
            results = check_caches(["one", "two"], detail_level="safe", include_duration=True)
        for result in results.values():
            self.assertEqual(result["reason"], "timeout")
            self.assertGreaterEqual(result["duration_ms"], 0)
            self.assertNotIn("secret", str(result))
        keys = [call.args[0] for call in cache.set.call_args_list]
        self.assertEqual(len(set(keys)), 2)
        self.assertEqual(cache.delete.call_args_list, [mock.call(key) for key in keys])
        for call in cache.set.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 30)

    def test_write_and_delete_failures_are_safe(self):
        for operation in ("set", "delete"):
            with self.subTest(operation=operation):
                cache = mock.Mock()
                getattr(cache, operation).side_effect = RuntimeError("secret")
                with mock.patch("django_deploy_probes.checks.cache.caches", {"default": cache}):
                    self.assertEqual(check_caches(["default"]), {"cache.default": "fail"})
                cache.delete.assert_called_once()

    def test_failed_delete_is_detected_even_without_exception(self):
        cache = mock.Mock()
        cache.get.side_effect = lambda key: cache.set.call_args.args[1]
        with mock.patch("django_deploy_probes.checks.cache.caches", {"default": cache}):
            results = check_caches(["default"], detail_level="safe")
        self.assertEqual(results["cache.default"], {"status": "fail", "reason": "delete_failed"})

    def test_missing_alias_is_safe(self):
        self.assertEqual(check_caches(["missing"]), {"cache.missing": "fail"})

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["cache"], "STARTUP_CHECKS": ["cache"]})
    def test_healthz_does_not_access_cache(self):
        with mock.patch("django_deploy_probes.checks.cache.caches") as cache_backends:
            self.assertEqual(self.client.get("/healthz").status_code, 200)
        cache_backends.__getitem__.assert_not_called()
