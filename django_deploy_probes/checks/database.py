from django.db import connections

from django_deploy_probes.checks.results import failure_result_for_exception


def check_databases(aliases, detail_level="none"):
    results = {}
    for alias in aliases:
        check_name = f"database.{alias}"
        try:
            with connections[alias].cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            results[check_name] = failure_result_for_exception(
                exc,
                "query_failed",
                detail_level,
            )
        else:
            results[check_name] = "ok"
    return results
