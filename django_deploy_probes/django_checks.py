from importlib.util import find_spec
from ipaddress import ip_network

from django.conf import settings
from django.core.checks import Error, Warning, register
from django.utils.module_loading import import_string

from django_deploy_probes.checks.registry import BUILTIN_CHECKS
from django_deploy_probes.checks.storage import VALID_STORAGE_CHECKS
from django_deploy_probes.conf import DEFAULT_DEPLOY_PROBES, merge_deploy_probes_settings

VALID_DETAIL_LEVELS = {"none", "safe"}
REMOVED_SETTINGS = {"TIMEOUT"}
BOOLEAN_SETTINGS = {
    "ENABLE_OPENAPI",
    "EXPOSE_BUILD_INFO",
    "EXPOSE_CHECK_MESSAGES",
    "EXPOSE_VERSION",
    "INCLUDE_CHECK_DURATIONS",
    "INTERNAL_IP_ONLY",
    "REQUIRE_READY_CHECKS",
    "REQUIRE_STARTUP_CHECKS",
}
METADATA_SETTINGS = {
    "BRANCH",
    "BUILD_TIME",
    "COMMIT",
    "ENVIRONMENT",
    "OPENAPI_TAG",
    "SERVICE_NAME",
    "SLOT",
    "VERSION",
}
CELERY_BOOLEAN_SETTINGS = {"BROKER", "RESULT_BACKEND", "WORKERS"}


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

    merged = merge_deploy_probes_settings(configured)
    messages.extend(_check_removed_settings(configured))
    messages.extend(_check_unknown_keys(configured))
    messages.extend(_check_check_list("READY_CHECKS", merged))
    messages.extend(_check_check_list("STARTUP_CHECKS", merged))
    messages.extend(_check_custom_check_list("CUSTOM_CHECKS", merged))
    messages.extend(_check_custom_check_list("READY_CUSTOM_CHECKS", merged))
    messages.extend(_check_custom_check_list("STARTUP_CUSTOM_CHECKS", merged))
    messages.extend(_check_boolean_settings(merged))
    messages.extend(_check_metadata_settings(merged))
    messages.extend(_check_detail_level(merged))
    messages.extend(_check_internal_networks(merged))
    messages.extend(_check_trusted_proxy_networks(merged))
    messages.extend(_check_client_ip_header(merged))
    messages.extend(_check_header_token(merged))
    messages.extend(_check_database_config(merged))
    messages.extend(_check_migration_config(merged))
    messages.extend(_check_redis_config(merged))
    messages.extend(_check_celery_config(merged))
    messages.extend(_check_storage_config(merged))
    messages.extend(_check_openapi_dependencies(merged))
    messages.extend(_check_require_checks(merged))
    return messages


def _check_unknown_keys(configured):
    return [
        Warning(
            f"Unknown DEPLOY_PROBES setting: {key}.",
            id="django_deploy_probes.W001",
        )
        for key in configured
        if key not in DEFAULT_DEPLOY_PROBES and key not in REMOVED_SETTINGS
    ]


def _check_removed_settings(configured):
    if "TIMEOUT" not in configured:
        return []
    return [
        Error(
            "DEPLOY_PROBES['TIMEOUT'] is not supported. Configure timeout values on each "
            "dependency check or backend instead.",
            id="django_deploy_probes.E019",
        )
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
    seen = set()
    for check_name in value:
        if not isinstance(check_name, str) or not check_name:
            messages.append(
                Error(
                    f"DEPLOY_PROBES['{key}'] entries must be non-empty check names.",
                    id="django_deploy_probes.E003",
                )
            )
            continue
        if check_name not in BUILTIN_CHECKS:
            messages.append(
                Error(
                    f"Unknown DEPLOY_PROBES['{key}'] check: {check_name}.",
                    id="django_deploy_probes.E003",
                )
            )
            continue
        if check_name in seen:
            messages.append(
                Error(
                    f"Duplicate DEPLOY_PROBES['{key}'] check: {check_name}.",
                    id="django_deploy_probes.E026",
                )
            )
        seen.add(check_name)
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
    messages = []
    seen = set()
    for dotted_path in value:
        if not isinstance(dotted_path, str) or not dotted_path:
            messages.append(
                Error(
                    f"DEPLOY_PROBES['{key}'] entries must be non-empty dotted paths.",
                    id="django_deploy_probes.E023",
                )
            )
            continue
        if dotted_path in seen:
            messages.append(
                Error(
                    f"Duplicate DEPLOY_PROBES['{key}'] custom check: {dotted_path}.",
                    id="django_deploy_probes.E025",
                )
            )
            continue
        seen.add(dotted_path)
        try:
            custom_check = import_string(dotted_path)
        except Exception:
            custom_check = None
        if not callable(custom_check):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['{key}'] custom check is not importable and callable: "
                    f"{dotted_path}.",
                    id="django_deploy_probes.E024",
                )
            )
    return messages


def _check_detail_level(probes_settings):
    if probes_settings.get("DETAIL_LEVEL") in VALID_DETAIL_LEVELS:
        return []
    return [
        Error(
            "DEPLOY_PROBES['DETAIL_LEVEL'] must be 'none' or 'safe'.",
            id="django_deploy_probes.E004",
        )
    ]


def _check_boolean_settings(probes_settings):
    return [
        Error(
            f"DEPLOY_PROBES['{key}'] must be a boolean.",
            id="django_deploy_probes.E027",
        )
        for key in sorted(BOOLEAN_SETTINGS)
        if not isinstance(probes_settings.get(key), bool)
    ]


def _check_metadata_settings(probes_settings):
    return [
        Error(
            f"DEPLOY_PROBES['{key}'] must be a string.",
            id="django_deploy_probes.E039",
        )
        for key in sorted(METADATA_SETTINGS)
        if not isinstance(probes_settings.get(key), str)
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
        except (TypeError, ValueError):
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
    messages = []
    if not header_token_validation.get("TOKEN"):
        messages.append(
            Error(
                "DEPLOY_PROBES['HEADER_TOKEN_VALIDATION']['TOKEN'] is required when enabled.",
                id="django_deploy_probes.E007",
            )
        )
    header_name = header_token_validation.get("HEADER_NAME", "X-Probe-Token")
    if not isinstance(header_name, str) or not header_name:
        messages.append(
            Error(
                "DEPLOY_PROBES['HEADER_TOKEN_VALIDATION']['HEADER_NAME'] must be a non-empty string.",
                id="django_deploy_probes.E038",
            )
        )
    protect_healthz = header_token_validation.get("PROTECT_HEALTHZ", False)
    if not isinstance(protect_healthz, bool):
        messages.append(
            Error(
                "DEPLOY_PROBES['HEADER_TOKEN_VALIDATION']['PROTECT_HEALTHZ'] must be a boolean.",
                id="django_deploy_probes.E038",
            )
        )
    return messages


def _check_database_config(probes_settings):
    if not _check_is_enabled("database", probes_settings):
        return []

    aliases = probes_settings.get("DATABASES")
    if not isinstance(aliases, (list, tuple)) or not aliases:
        return [
            Error(
                "DEPLOY_PROBES['DATABASES'] must define at least one database alias when "
                "database is enabled.",
                id="django_deploy_probes.E028",
            )
        ]

    messages = []
    seen = set()
    configured_aliases = settings.DATABASES
    for alias in aliases:
        if not isinstance(alias, str) or not alias:
            messages.append(
                Error(
                    "DEPLOY_PROBES['DATABASES'] entries must be non-empty strings.",
                    id="django_deploy_probes.E028",
                )
            )
            continue
        if alias in seen:
            messages.append(
                Error(
                    f"Duplicate DEPLOY_PROBES['DATABASES'] alias: {alias}.",
                    id="django_deploy_probes.E028",
                )
            )
        elif alias not in configured_aliases:
            messages.append(
                Error(
                    f"Unknown DEPLOY_PROBES['DATABASES'] alias: {alias}.",
                    id="django_deploy_probes.E029",
                )
            )
        seen.add(alias)
    return messages


def _check_migration_config(probes_settings):
    if not _check_is_enabled("migrations", probes_settings):
        return []

    migration_settings = probes_settings.get("MIGRATIONS")
    if not isinstance(migration_settings, dict):
        return [
            Error(
                "DEPLOY_PROBES['MIGRATIONS'] must be a dictionary when migrations is enabled.",
                id="django_deploy_probes.E030",
            )
        ]

    alias = migration_settings.get("DATABASE", "default")
    if not isinstance(alias, str) or not alias:
        return [
            Error(
                "DEPLOY_PROBES['MIGRATIONS']['DATABASE'] must be a non-empty string.",
                id="django_deploy_probes.E031",
            )
        ]
    if alias not in settings.DATABASES:
        return [
            Error(
                f"Unknown DEPLOY_PROBES['MIGRATIONS']['DATABASE'] alias: {alias}.",
                id="django_deploy_probes.E032",
            )
        ]
    return []


def _check_redis_config(probes_settings):
    if not _check_is_enabled("redis", probes_settings):
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
        if not isinstance(alias, str) or not alias:
            messages.append(
                Error(
                    "DEPLOY_PROBES['REDIS'] aliases must be non-empty strings.",
                    id="django_deploy_probes.E037",
                )
            )
            continue
        if not isinstance(config, dict) or not config.get("LOCATION"):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['REDIS']['{alias}']['LOCATION'] is required.",
                    id="django_deploy_probes.E009",
                )
            )
            continue
        if "TIMEOUT" in config and not _is_positive_number(config["TIMEOUT"]):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['REDIS']['{alias}']['TIMEOUT'] must be a positive number.",
                    id="django_deploy_probes.E020",
                )
            )
    return messages


def _check_celery_config(probes_settings):
    if not _check_is_enabled("celery", probes_settings):
        return []

    celery_settings = probes_settings.get("CELERY")
    if not isinstance(celery_settings, dict):
        return [
            Error(
                "DEPLOY_PROBES['CELERY'] must be a dictionary when celery is enabled.",
                id="django_deploy_probes.E021",
            )
        ]

    messages = []
    for key in CELERY_BOOLEAN_SETTINGS:
        if not isinstance(celery_settings.get(key), bool):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['CELERY']['{key}'] must be a boolean.",
                    id="django_deploy_probes.E033",
                )
            )

    if not any(celery_settings.get(key) is True for key in CELERY_BOOLEAN_SETTINGS):
        messages.append(
            Error(
                "DEPLOY_PROBES['CELERY'] must enable BROKER, WORKERS, or RESULT_BACKEND when "
                "celery is enabled.",
                id="django_deploy_probes.E034",
            )
        )

    timeout = celery_settings.get("TIMEOUT", DEFAULT_DEPLOY_PROBES["CELERY"]["TIMEOUT"])
    if not _is_positive_number(timeout):
        messages.append(
            Error(
                "DEPLOY_PROBES['CELERY']['TIMEOUT'] must be a positive number.",
                id="django_deploy_probes.E022",
            )
        )
    return messages


def _check_is_enabled(check_name, probes_settings):
    return check_name in probes_settings.get(
        "READY_CHECKS", []
    ) or check_name in probes_settings.get("STARTUP_CHECKS", [])


def _is_positive_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _check_require_checks(probes_settings):
    messages = []
    has_ready_checks = any(
        probes_settings.get(key) for key in ("READY_CHECKS", "READY_CUSTOM_CHECKS", "CUSTOM_CHECKS")
    )
    has_startup_checks = any(
        probes_settings.get(key) for key in ("STARTUP_CHECKS", "STARTUP_CUSTOM_CHECKS")
    )
    if probes_settings.get("REQUIRE_READY_CHECKS") and not has_ready_checks:
        messages.append(
            Warning(
                "REQUIRE_READY_CHECKS=True but READY_CHECKS is empty.",
                id="django_deploy_probes.W002",
            )
        )
    if probes_settings.get("REQUIRE_STARTUP_CHECKS") and not has_startup_checks:
        messages.append(
            Warning(
                "REQUIRE_STARTUP_CHECKS=True but STARTUP_CHECKS is empty.",
                id="django_deploy_probes.W003",
            )
        )
    return messages


def _check_openapi_dependencies(probes_settings):
    if not probes_settings.get("ENABLE_OPENAPI"):
        return []

    missing = [
        package for package in ("rest_framework", "drf_spectacular") if find_spec(package) is None
    ]
    if not missing:
        return []
    return [
        Error(
            "DEPLOY_PROBES['ENABLE_OPENAPI'] requires the 'openapi' package extra. "
            f"Missing modules: {', '.join(missing)}.",
            id="django_deploy_probes.E035",
        )
    ]


def _check_storage_config(probes_settings):
    if "storage" not in probes_settings.get(
        "READY_CHECKS", []
    ) and "storage" not in probes_settings.get("STARTUP_CHECKS", []):
        return []

    storage_settings = probes_settings.get("STORAGE")
    if not isinstance(storage_settings, dict) or not storage_settings:
        return [
            Error(
                "DEPLOY_PROBES['STORAGE'] must define at least one storage alias when storage is enabled.",
                id="django_deploy_probes.E013",
            )
        ]

    messages = []
    for alias, config in storage_settings.items():
        if not isinstance(alias, str) or not alias:
            messages.append(
                Error(
                    "DEPLOY_PROBES['STORAGE'] aliases must be non-empty strings.",
                    id="django_deploy_probes.E036",
                )
            )
            continue
        if alias not in settings.STORAGES:
            messages.append(
                Error(
                    f"Unknown DEPLOY_PROBES['STORAGE'] alias: {alias}.",
                    id="django_deploy_probes.E036",
                )
            )
        if not isinstance(config, dict):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['STORAGE']['{alias}'] must be a dictionary.",
                    id="django_deploy_probes.E014",
                )
            )
            continue

        check_mode = config.get("CHECK", "exists")
        if check_mode not in VALID_STORAGE_CHECKS:
            messages.append(
                Error(
                    f"DEPLOY_PROBES['STORAGE']['{alias}']['CHECK'] must be one of: "
                    f"{', '.join(sorted(VALID_STORAGE_CHECKS))}.",
                    id="django_deploy_probes.E015",
                )
            )
            continue

        if check_mode == "exists" and not config.get("PATH"):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['STORAGE']['{alias}']['PATH'] is required for exists checks.",
                    id="django_deploy_probes.E016",
                )
            )

        if "ALLOW_MISSING" in config and not isinstance(config["ALLOW_MISSING"], bool):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['STORAGE']['{alias}']['ALLOW_MISSING'] must be a boolean.",
                    id="django_deploy_probes.E017",
                )
            )

        if "PREFIX" in config and not isinstance(config["PREFIX"], str):
            messages.append(
                Error(
                    f"DEPLOY_PROBES['STORAGE']['{alias}']['PREFIX'] must be a string.",
                    id="django_deploy_probes.E018",
                )
            )

    return messages
