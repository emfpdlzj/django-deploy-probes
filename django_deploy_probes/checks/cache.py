from uuid import uuid4

from django.core.cache import caches

from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    run_check,
)


def _check_cache(alias, detail_level):
    key = f"django-deploy-probes:{uuid4().hex}"
    value = uuid4().hex
    try:
        cache = caches[alias]
        try:
            cache.set(key, value, timeout=30)
            if cache.get(key) != value:
                return failure_result("value_mismatch", detail_level)
        finally:
            cache.delete(key)
        if cache.get(key) is not None:
            return failure_result("delete_failed", detail_level)
    except Exception as exc:
        return failure_result_for_exception(exc, "cache_check_failed", detail_level)
    return "ok"


def check_caches(aliases, detail_level="none", include_duration=False):
    return {
        f"cache.{alias}": run_check(
            _check_cache,
            alias,
            detail_level,
            include_duration=include_duration,
        )
        for alias in aliases
    }
