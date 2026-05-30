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
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["10.0.0.0/8"],
            "TRUSTED_PROXY_NETWORKS": ["192.0.2.0/24"],
            "CLIENT_IP_HEADER": "X-Forwarded-For",
        }
    )
    def test_internal_client_is_allowed_through_trusted_proxy(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="10.1.2.3",
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(
        DEPLOY_PROBES={
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["10.0.0.0/8"],
            "TRUSTED_PROXY_NETWORKS": ["192.0.2.0/24"],
            "CLIENT_IP_HEADER": "X-Forwarded-For",
        }
    )
    def test_external_client_is_blocked_through_trusted_proxy(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.7",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["10.0.0.0/8"],
            "TRUSTED_PROXY_NETWORKS": ["192.0.2.0/24"],
            "CLIENT_IP_HEADER": "X-Forwarded-For",
        }
    )
    def test_spoofed_forwarded_header_is_ignored_for_untrusted_proxy(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="198.51.100.9",
            HTTP_X_FORWARDED_FOR="10.1.2.3",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["10.0.0.0/8"],
            "TRUSTED_PROXY_NETWORKS": ["192.0.2.0/24", "10.0.0.0/8"],
            "CLIENT_IP_HEADER": "X-Forwarded-For",
        }
    )
    def test_x_forwarded_for_uses_last_untrusted_hop_as_client_ip(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="198.51.100.7, 10.9.9.9",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(
        DEPLOY_PROBES={
            "INTERNAL_IP_ONLY": True,
            "INTERNAL_IP_NETWORKS": ["10.0.0.0/8"],
            "TRUSTED_PROXY_NETWORKS": ["192.0.2.0/24"],
            "CLIENT_IP_HEADER": "X-Real-IP",
        }
    )
    def test_custom_client_ip_header_is_supported_for_trusted_proxy(self):
        response = self.client.get(
            reverse("django_deploy_probes:version"),
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_REAL_IP="10.1.2.3",
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
