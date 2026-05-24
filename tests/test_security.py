from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class SecurityTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"INTERNAL_IP_ONLY": True})
    def test_internal_ip_request_is_allowed(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="10.1.2.3",
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(DEPLOY_PROBES={"INTERNAL_IP_ONLY": True})
    def test_external_ip_request_is_forbidden(self):
        response = self.client.get(
            reverse("django_deploy_probes:readyz"),
            REMOTE_ADDR="8.8.8.8",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["203.0.113.0/24"],
        }
    )
    def test_configured_internal_ip_network_is_allowed(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
                "TOKEN": "secret-token",
            },
        }
    )
    def test_header_token_match_is_allowed(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            HTTP_X_PROBE_TOKEN="secret-token",
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
                "TOKEN": "secret-token",
            },
        }
    )
    def test_header_token_mismatch_is_forbidden(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            HTTP_X_PROBE_TOKEN="wrong-token",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
                "TOKEN": "secret-token",
                "PROTECT_HEALTHZ": False,
            },
        }
    )
    def test_healthz_is_not_protected_when_protect_healthz_is_false(self):
        response = self.client.get(reverse("django_deploy_probes:healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
                "TOKEN": "secret-token",
                "PROTECT_HEALTHZ": True,
            },
        }
    )
    def test_healthz_is_protected_when_protect_healthz_is_true(self):
        response = self.client.get(reverse("django_deploy_probes:healthz"))

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
                "TOKEN": "secret-token",
            },
        }
    )
    def test_secret_token_is_not_exposed_in_forbidden_response(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            HTTP_X_PROBE_TOKEN="wrong-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("secret-token", response.content.decode())
