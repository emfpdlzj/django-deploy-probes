from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import storages


VALID_STORAGE_CHECKS = {"exists", "write"}
DEFAULT_WRITE_PREFIX = "django-deploy-probes"


def _fail_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def _build_probe_path(prefix):
    normalized_prefix = prefix.strip("/")
    filename = f"probe-{uuid4().hex}.txt"
    if not normalized_prefix:
        return filename
    return f"{normalized_prefix}/{filename}"


def check_storage(storage_settings, detail_level="none"):
    results = {}

    for alias, config in storage_settings.items():
        check_name = f"storage.{alias}"
        check_mode = config.get("CHECK", "exists")

        try:
            storage = storages[alias]
        except Exception:
            results[check_name] = _fail_result("storage_alias_unavailable", detail_level)
            continue

        if check_mode == "exists":
            path = config.get("PATH")
            allow_missing = config.get("ALLOW_MISSING", False)
            try:
                exists = storage.exists(path)
            except Exception:
                results[check_name] = _fail_result("exists_failed", detail_level)
            else:
                if exists or allow_missing:
                    results[check_name] = "ok"
                else:
                    results[check_name] = _fail_result("path_missing", detail_level)
            continue

        if check_mode == "write":
            probe_path = _build_probe_path(config.get("PREFIX", DEFAULT_WRITE_PREFIX))
            try:
                saved_name = storage.save(probe_path, ContentFile(b"ok\n"))
                storage.delete(saved_name)
            except Exception:
                results[check_name] = _fail_result("write_failed", detail_level)
            else:
                results[check_name] = "ok"
            continue

        results[check_name] = _fail_result("invalid_storage_check", detail_level)

    return results
