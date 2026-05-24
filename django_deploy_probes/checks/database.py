from django.db import connections


def _fail_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def check_databases(aliases, detail_level="none"):
    results = {}
    for alias in aliases:
        check_name = f"database.{alias}"
        try:
            with connections[alias].cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            results[check_name] = _fail_result("query_failed", detail_level)
        else:
            results[check_name] = "ok"
    return results
