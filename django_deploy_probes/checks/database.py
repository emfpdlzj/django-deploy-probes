from django.db import connections

from django_deploy_probes.checks.results import failure_result_for_exception, run_check


def _check_database(alias, detail_level):
    try:
        with connections[alias].cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        return failure_result_for_exception(exc, "query_failed", detail_level)
    return "ok"


def check_databases(aliases, detail_level="none", include_duration=False):
    return {
        f"database.{alias}": run_check(
            _check_database,
            alias,
            detail_level,
            include_duration=include_duration,
        )
        for alias in aliases
    }
