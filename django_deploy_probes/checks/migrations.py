from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    run_check,
)


def _check_migrations(migration_settings, detail_level):
    database_alias = migration_settings.get("DATABASE", "default")
    try:
        executor = MigrationExecutor(connections[database_alias])
        targets = executor.loader.graph.leaf_nodes()
        migration_plan = executor.migration_plan(targets)
    except Exception as exc:
        return failure_result_for_exception(exc, "migration_check_failed", detail_level)

    if migration_plan:
        return failure_result("unapplied_migrations", detail_level)
    return "ok"


def check_migrations(migration_settings, detail_level="none", include_duration=False):
    return {
        "migrations": run_check(
            _check_migrations,
            migration_settings,
            detail_level,
            include_duration=include_duration,
        )
    }
