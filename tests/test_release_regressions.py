from unittest import mock

from django.test import SimpleTestCase, override_settings

from django_deploy_probes.checks.redis import _get_redis_client


class ReleaseRegressionTestCase(SimpleTestCase):
    @override_settings(
        DEPLOY_PROBES={"HEADER_TOKEN_VALIDATION": {"TOKEN": "secret", "PROTECT_HEALTHZ": True}}
    )
    def test_non_ascii_request_tokens_return_forbidden(self):
        for endpoint in ("readyz", "startupz", "version", "healthz"):
            for token in ("한글", "caf\u00e9"):
                with self.subTest(endpoint=endpoint, token=token):
                    self.assertEqual(
                        self.client.get(f"/{endpoint}", HTTP_X_PROBE_TOKEN=token).status_code, 403
                    )

    @override_settings(DEPLOY_PROBES={"HEADER_TOKEN_VALIDATION": {"TOKEN": "caf\u00e9"}})
    def test_configured_unicode_token_uses_utf8_comparison(self):
        self.assertEqual(
            self.client.get("/readyz", HTTP_X_PROBE_TOKEN="caf\u00e9").status_code, 200
        )

    def test_redis_url_timeout_options_cannot_override_probe_timeout(self):
        try:
            import redis
        except ImportError:
            self.skipTest("Redis extra is not installed")
        for scheme in ("redis", "rediss", "unix"):
            location = f"{scheme}://localhost/0?socket_timeout=30&socket_connect_timeout=20&db=2&client_name=probe%20name"
            client = _get_redis_client(location, 0.1)
            try:
                options = client.connection_pool.connection_kwargs
                self.assertEqual(options["socket_timeout"], 0.1)
                self.assertEqual(options["socket_connect_timeout"], 0.1)
                self.assertEqual(options["db"], 2)
                self.assertEqual(options["client_name"], "probe name")
            finally:
                client.close()
        with mock.patch.object(redis.Redis, "from_url") as factory:
            _get_redis_client("redis://localhost?socket%5Ftimeout=bad&socket_timeout=60", 0.5)
        self.assertNotIn("socket_timeout", factory.call_args.args[0])
