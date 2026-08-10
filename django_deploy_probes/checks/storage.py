from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import storages

from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    run_check,
)


VALID_STORAGE_CHECKS = {"exists", "write"}
DEFAULT_WRITE_PREFIX = "django-deploy-probes"


def _build_probe_path(prefix):
    normalized_prefix = prefix.strip("/")
    filename = f"probe-{uuid4().hex}.txt"
    if not normalized_prefix:
        return filename
    return f"{normalized_prefix}/{filename}"


def _check_storage_alias(alias, config, detail_level):
    check_mode = config.get("CHECK", "exists")

    try:
        storage = storages[alias]
    except Exception as exc:
        return failure_result_for_exception(exc, "storage_alias_unavailable", detail_level)

    if check_mode == "exists":
        path = config.get("PATH")
        allow_missing = config.get("ALLOW_MISSING", False)
        try:
            exists = storage.exists(path)
        except Exception as exc:
            return failure_result_for_exception(exc, "exists_failed", detail_level)
        if exists or allow_missing:
            return "ok"
        return failure_result("path_missing", detail_level)

    if check_mode == "write":
        probe_path = _build_probe_path(config.get("PREFIX", DEFAULT_WRITE_PREFIX))
        try:
            saved_name = storage.save(probe_path, ContentFile(b"ok\n"))
            storage.delete(saved_name)
        except Exception as exc:
            return failure_result_for_exception(exc, "write_failed", detail_level)
        return "ok"

    return failure_result("invalid_storage_check", detail_level)


def check_storage(storage_settings, detail_level="none", include_duration=False):
    return {
        f"storage.{alias}": run_check(
            _check_storage_alias,
            alias,
            config,
            detail_level,
            include_duration=include_duration,
        )
        for alias, config in storage_settings.items()
    }
