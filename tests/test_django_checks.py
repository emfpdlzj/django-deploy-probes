from django.core.checks import run_checks
from django.test import SimpleTestCase, override_settings


class DjangoChecksTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES="invalid")
    def test_non_dict_deploy_probes_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E001", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"UNUSED_FLAG": True})
    def test_unknown_setting_key_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.W001", {message.id for message in messages})

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

    @override_settings(DEPLOY_PROBES={"TRUSTED_PROXY_NETWORKS": ["not-a-cidr"]})
    def test_invalid_trusted_proxy_network_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E011", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"CLIENT_IP_HEADER": ["X-Forwarded-For"]})
    def test_invalid_client_ip_header_type_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E012", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"CLIENT_IP_HEADER": "X-Forwarded-For"})
    def test_client_ip_header_without_trusted_proxies_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.W004", {message.id for message in messages})

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

    @override_settings(DEPLOY_PROBES={"HEADER_TOKEN_VALIDATION": True})
    def test_invalid_header_token_validation_type_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E006", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CUSTOM_CHECKS": "tests.checks.ready"})
    def test_invalid_custom_check_list_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E010", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CUSTOM_CHECKS": [123]})
    def test_invalid_custom_check_entry_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E023", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CUSTOM_CHECKS": ["tests.missing.check"]})
    def test_unimportable_custom_check_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E024", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CUSTOM_CHECKS": [
                "tests.test_readyz.custom_true_check",
                "tests.test_readyz.custom_true_check",
            ]
        }
    )
    def test_duplicate_custom_check_path_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E025", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"REQUIRE_READY_CHECKS": True, "READY_CHECKS": []})
    def test_empty_required_ready_checks_are_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.W002", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"REQUIRE_STARTUP_CHECKS": True, "STARTUP_CHECKS": []})
    def test_empty_required_startup_checks_are_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.W003", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["redis"], "REDIS": {}})
    def test_missing_redis_config_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E008", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["redis"],
            "REDIS": {"default": {}},
        }
    )
    def test_missing_redis_location_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E009", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"READY_CHECKS": ["storage"], "STORAGE": {}})
    def test_missing_storage_config_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E013", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["storage"],
            "STORAGE": {"default": {"CHECK": "ping"}},
        }
    )
    def test_invalid_storage_check_mode_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E015", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["storage"],
            "STORAGE": {"default": {"CHECK": "exists"}},
        }
    )
    def test_missing_storage_exists_path_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E016", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["storage"],
            "STORAGE": {
                "default": {"CHECK": "exists", "PATH": "probe.txt", "ALLOW_MISSING": "yes"}
            },
        }
    )
    def test_invalid_storage_allow_missing_type_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E017", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["storage"],
            "STORAGE": {"default": "invalid"},
        }
    )
    def test_non_dict_storage_alias_config_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E014", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["storage"],
            "STORAGE": {
                "default": {
                    "CHECK": "write",
                    "PREFIX": 123,
                }
            },
        }
    )
    def test_invalid_storage_prefix_type_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E018", {message.id for message in messages})

    @override_settings(DEPLOY_PROBES={"TIMEOUT": 0.5})
    def test_removed_global_timeout_is_reported(self):
        messages = run_checks()
        message_ids = {message.id for message in messages}

        self.assertIn("django_deploy_probes.E019", message_ids)
        self.assertNotIn("django_deploy_probes.W001", message_ids)

    @override_settings(
        DEPLOY_PROBES={
            "STARTUP_CHECKS": ["redis"],
            "REDIS": {
                "default": {
                    "LOCATION": "redis://localhost:6379/0",
                    "TIMEOUT": 0,
                }
            },
        }
    )
    def test_invalid_redis_timeout_is_reported_for_startup_check(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E020", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": "invalid",
        }
    )
    def test_invalid_celery_config_type_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E021", {message.id for message in messages})

    @override_settings(
        DEPLOY_PROBES={
            "READY_CHECKS": ["celery"],
            "CELERY": {
                "BROKER": True,
                "TIMEOUT": False,
            },
        }
    )
    def test_invalid_celery_timeout_is_reported(self):
        messages = run_checks()

        self.assertIn("django_deploy_probes.E022", {message.id for message in messages})
