from django.test import SimpleTestCase, override_settings

from django_deploy_probes.conf import get_deploy_probes_settings


class DeployProbesSettingsTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"SERVICE_NAME": "api", "TIMEOUT": 0.5})
    def test_settings_loader_merges_configured_values_with_defaults(self):
        probes_settings = get_deploy_probes_settings()

        self.assertEqual(probes_settings["SERVICE_NAME"], "api")
        self.assertEqual(probes_settings["TIMEOUT"], 0.5)
        self.assertEqual(probes_settings["VERSION"], "unknown")
        self.assertEqual(probes_settings["READY_CHECKS"], [])
        self.assertEqual(probes_settings["READY_CUSTOM_CHECKS"], [])
        self.assertEqual(probes_settings["STARTUP_CUSTOM_CHECKS"], [])

    @override_settings(DEPLOY_PROBES={"CELERY": {"BROKER": True}})
    def test_settings_loader_merges_nested_configured_values_with_defaults(self):
        probes_settings = get_deploy_probes_settings()

        self.assertIs(probes_settings["CELERY"]["BROKER"], True)
        self.assertIs(probes_settings["CELERY"]["WORKERS"], False)
        self.assertIs(probes_settings["CELERY"]["RESULT_BACKEND"], False)
        self.assertEqual(probes_settings["CELERY"]["TIMEOUT"], 1.0)

    def test_settings_loader_includes_safe_open_source_defaults(self):
        probes_settings = get_deploy_probes_settings()

        self.assertEqual(probes_settings["DETAIL_LEVEL"], "none")
        self.assertIs(probes_settings["EXPOSE_CHECK_MESSAGES"], False)
        self.assertIn("127.0.0.1/32", probes_settings["INTERNAL_IP_NETWORKS"])
        self.assertEqual(probes_settings["TRUSTED_PROXY_NETWORKS"], [])
        self.assertIsNone(probes_settings["CLIENT_IP_HEADER"])
