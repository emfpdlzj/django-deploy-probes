from django.db import connections
from django.db.migrations.executor import MigrationExecutor


def _fail_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def check_migrations(migration_settings, detail_level="none"):
    database_alias = migration_settings.get("DATABASE", "default")
    try:
        executor = MigrationExecutor(connections[database_alias])
        targets = executor.loader.graph.leaf_nodes()
        migration_plan = executor.migration_plan(targets)
    except Exception:
        return {"migrations": _fail_result("migration_check_failed", detail_level)}

    if migration_plan:
        return {"migrations": _fail_result("unapplied_migrations", detail_level)}
    return {"migrations": "ok"}
