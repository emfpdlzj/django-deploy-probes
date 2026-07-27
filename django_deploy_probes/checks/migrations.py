from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
)


def check_migrations(migration_settings, detail_level="none"):
    database_alias = migration_settings.get("DATABASE", "default")
    try:
        executor = MigrationExecutor(connections[database_alias])
        targets = executor.loader.graph.leaf_nodes()
        migration_plan = executor.migration_plan(targets)
    except Exception as exc:
        return {
            "migrations": failure_result_for_exception(
                exc,
                "migration_check_failed",
                detail_level,
            )
        }

    if migration_plan:
        return {"migrations": failure_result("unapplied_migrations", detail_level)}
    return {"migrations": "ok"}
