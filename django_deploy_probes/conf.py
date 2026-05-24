from copy import deepcopy

from django.conf import settings


DEFAULT_DEPLOY_PROBES = {
    "SERVICE_NAME": "django-app",
    "ENVIRONMENT": "local",
    "VERSION": "unknown",
    "COMMIT": "unknown",
    "BRANCH": "unknown",
    "BUILD_TIME": "unknown",
    "SLOT": "unknown",
    "READY_CHECKS": [],
    "STARTUP_CHECKS": [],
    "DATABASES": ["default"],
    "REDIS": {},
    "CELERY": {
        "BROKER": False,
        "WORKERS": False,
        "RESULT_BACKEND": False,
        "TIMEOUT": 1.0,
    },
    "MIGRATIONS": {
        "DATABASE": "default",
    },
    "CUSTOM_CHECKS": [],
    "READY_CUSTOM_CHECKS": [],
    "STARTUP_CUSTOM_CHECKS": [],
    "DETAIL_LEVEL": "none",
    "INCLUDE_CHECK_DURATIONS": False,
    "REQUIRE_READY_CHECKS": False,
    "REQUIRE_STARTUP_CHECKS": False,
    "EXPOSE_CHECK_MESSAGES": False,
    "EXPOSE_VERSION": True,
    "EXPOSE_BUILD_INFO": False,
    "INTERNAL_IP_ONLY": False,
    "INTERNAL_IP_NETWORKS": [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ],
    "HEADER_TOKEN_VALIDATION": False,
    "ENABLE_OPENAPI": False,
    "OPENAPI_TAG": "Deployment Probes",
    "TIMEOUT": 1.0,
}


def _merge_settings(defaults, configured):
    merged = deepcopy(defaults)
    for key, value in configured.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_deploy_probes_settings():
    configured = getattr(settings, "DEPLOY_PROBES", {})
    return _merge_settings(DEFAULT_DEPLOY_PROBES, configured)
