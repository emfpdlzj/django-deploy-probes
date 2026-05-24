from django.core.checks import run_checks
from django.test import SimpleTestCase, override_settings


class DjangoChecksTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"DETAIL_LEVEL": "verbose"})
    def test_invalid_detail_level_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E004", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["missing"]})
    def test_unknown_ready_check_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E003", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"INTERNAL_IP_NETWORKS": ["not-a-cidr"]})
    def test_invalid_internal_network_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E005", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "HEADER_TOKEN_VALIDATION": {
                "HEADER_NAME": "X-Probe-Token",
            },
        }
    )
    def test_missing_probe_token_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E007", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CUSTOM_CHECKS": "tests.checks.ready"})
    def test_invalid_custom_check_list_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E010", {message.id for message in messages})
