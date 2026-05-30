from ipaddress import ip_network

from django.core.checks import Error, Warning, register
from django.conf import settings

from django_deploy_probes.checks.registry import BUILTIN_CHECKS
from django_deploy_probes.conf import DEFAULT_DEPLOY_PROBES


VALID_DETAIL_LEVELS = {"none", "safe"}


@register()
def check_deploy_probes_settings(app_configs, **kwargs):
    configured = getattr(settings, "DEPLOY_PROBES", {})
    messages = []

    if not isinstance(configured, dict):
        return [
            Error(
                "DEPLOY_PROBES must be a dictionary.",
                id="django_deploy_probes.E001",
            )
        ]

    merged = DEFAULT_DEPLOY_PROBES | configured
    messages.extend(_check_unknown_keys(configured))
    messages.extend(_check_check_list("READY_CHECKS", merged))
    messages.extend(_check_check_list("STARTUP_CHECKS", merged))
    messages.extend(_check_custom_check_list("CUSTOM_CHECKS", merged))
    messages.extend(_check_custom_check_list("READY_CUSTOM_CHECKS", merged))
    messages.extend(_check_custom_check_list("STARTUP_CUSTOM_CHECKS", merged))
    messages.extend(_check_detail_level(merged))
    messages.extend(_check_internal_networks(merged))
    messages.extend(_check_trusted_proxy_networks(merged))
    messages.extend(_check_client_ip_header(merged))
    messages.extend(_check_header_token(merged))
    messages.extend(_check_redis_config(merged))
    messages.extend(_check_require_checks(merged))
    return messages


def _check_unknown_keys(configured):
    return [
        Warning(
            f"Unknown DEPLOY_PROBES setting: {key}.",
            id="django_deploy_probes.W001",
        )
        for key in configured
        if key not in DEFAULT_DEPLOY_PROBES
    ]


def _check_check_list(key, probes_settings):
    value = probes_settings.get(key)
    if not isinstance(value, (list, tuple)):
        return [
            Error(
                f"DEPLOY_PROBES['{key}'] must be a list or tuple.",
                id="django_deploy_probes.E002",
            )
        ]

    messages = []
    for check_name in value:
        if check_name not in BUILTIN_CHECKS:
            messages.append(
                Error(
                    f"Unknown DEPLOY_PROBES['{key}'] check: {check_name}.",
                    id="django_deploy_probes.E003",
                )
            )
    return messages


def _check_custom_check_list(key, probes_settings):
    value = probes_settings.get(key)
    if not isinstance(value, (list, tuple)):
        return [
            Error(
                f"DEPLOY_PROBES['{key}'] must be a list or tuple.",
                id="django_deploy_probes.E010",
            )
        ]
    return []


def _check_detail_level(probes_settings):
    if probes_settings.get("DETAIL_LEVEL") in VALID_DETAIL_LEVELS:
        return []
    return [
        Error(
            "DEPLOY_PROBES['DETAIL_LEVEL'] must be 'none' or 'safe'.",
            id="django_deploy_probes.E004",
        )
    ]


def _check_internal_networks(probes_settings):
    return _check_network_list(
        key="INTERNAL_IP_NETWORKS",
        value=probes_settings.get("INTERNAL_IP_NETWORKS", []),
        error_id="django_deploy_probes.E005",
    )


def _check_trusted_proxy_networks(probes_settings):
    return _check_network_list(
        key="TRUSTED_PROXY_NETWORKS",
        value=probes_settings.get("TRUSTED_PROXY_NETWORKS", []),
        error_id="django_deploy_probes.E011",
    )


def _check_network_list(key, value, error_id):
    if not isinstance(value, (list, tuple)):
        return [
            Error(
                f"DEPLOY_PROBES['{key}'] must be a list or tuple.",
                id=error_id,
            )
        ]

    messages = []
    for network in value:
        try:
            ip_network(network)
        except ValueError:
            messages.append(
                Error(
                    f"Invalid {key} entry: {network}.",
                    id=error_id,
                )
            )
    return messages


def _check_client_ip_header(probes_settings):
    client_ip_header = probes_settings.get("CLIENT_IP_HEADER")
    if client_ip_header in (None, False, ""):
        return []

    if not isinstance(client_ip_header, str):
        return [
            Error(
                "DEPLOY_PROBES['CLIENT_IP_HEADER'] must be a string or None.",
                id="django_deploy_probes.E012",
            )
        ]

    if not probes_settings.get("TRUSTED_PROXY_NETWORKS"):
        return [
            Warning(
                "CLIENT_IP_HEADER is configured without TRUSTED_PROXY_NETWORKS and will be ignored.",
                id="django_deploy_probes.W004",
            )
        ]

    return []


def _check_header_token(probes_settings):
    header_token_validation = probes_settings.get("HEADER_TOKEN_VALIDATION")
    if not header_token_validation:
        return []
    if not isinstance(header_token_validation, dict):
        return [
            Error(
                "DEPLOY_PROBES['HEADER_TOKEN_VALIDATION'] must be False or a dictionary.",
                id="django_deploy_probes.E006",
            )
        ]
    if not header_token_validation.get("TOKEN"):
        return [
            Error(
                "DEPLOY_PROBES['HEADER_TOKEN_VALIDATION']['TOKEN'] is required when enabled.",
                id="django_deploy_probes.E007",
            )
        ]
    return []


def _check_redis_config(probes_settings):
    if "redis" not in probes_settings.get("READY_CHECKS", []):
        return []

    redis_settings = probes_settings.get("REDIS")
    if not isinstance(redis_settings, dict) or not redis_settings:
        return [
            Error(
                "DEPLOY_PROBES['REDIS'] must define at least one Redis alias when redis is enabled.",
                id="django_deploy_probes.E008",
            )
        ]

    messages = []
    for alias, config in redis_settings.items():
        if not isinstance(config, dict) or not config.get("LOCATION"):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['REDIS']['{alias}']['LOCATION'] is required.",
                    id="django_deploy_probes.E009",
                )
            )
    return messages


def _check_require_checks(probes_settings):
    messages = []
    if probes_settings.get("REQUIRE_READY_CHECKS") and not probes_settings.get("READY_CHECKS"):
        messages.append(
            Warning(
                "REQUIRE_READY_CHECKS=True but READY_CHECKS is empty.",
                id="django_deploy_probes.W002",
            )
        )
    if probes_settings.get("REQUIRE_STARTUP_CHECKS") and not probes_settings.get("STARTUP_CHECKS"):
        messages.append(
            Warning(
                "REQUIRE_STARTUP_CHECKS=True but STARTUP_CHECKS is empty.",
                id="django_deploy_probes.W003",
            )
        )
    return messages
