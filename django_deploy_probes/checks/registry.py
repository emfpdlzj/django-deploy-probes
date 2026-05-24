from django_deploy_probes.checks.celery import check_celery
from django_deploy_probes.checks.custom import check_custom_checks
from django_deploy_probes.checks.database import check_databases
from django_deploy_probes.checks.migrations import check_migrations
from django_deploy_probes.checks.redis import check_redis
from django_deploy_probes.checks.results import with_duration


BUILTIN_CHECKS = {
    "database": lambda probes_settings: (
        check_databases,
        (probes_settings["DATABASES"],),
        {"detail_level": probes_settings["DETAIL_LEVEL"]},
    ),
    "redis": lambda probes_settings: (
        check_redis,
        (probes_settings["REDIS"],),
        {"detail_level": probes_settings["DETAIL_LEVEL"]},
    ),
    "celery": lambda probes_settings: (
        check_celery,
        (probes_settings["CELERY"],),
        {"detail_level": probes_settings["DETAIL_LEVEL"]},
    ),
    "migrations": lambda probes_settings: (
        check_migrations,
        (probes_settings["MIGRATIONS"],),
        {"detail_level": probes_settings["DETAIL_LEVEL"]},
    ),
}


def run_configured_checks(probes_settings, check_names, custom_check_paths=None):
    checks = {}
    include_duration = probes_settings["INCLUDE_CHECK_DURATIONS"]

    for check_name in check_names:
        check_factory = BUILTIN_CHECKS.get(check_name)
        if check_factory is None:
            checks[check_name] = _unknown_check_result(probes_settings["DETAIL_LEVEL"])
            continue

        check_func, args, kwargs = check_factory(probes_settings)
        checks.update(
            with_duration(
                check_func,
                *args,
                include_duration=include_duration,
                **kwargs,
            )
        )

    custom_check_paths = custom_check_paths or []
    if custom_check_paths:
        checks.update(
            with_duration(
                check_custom_checks,
                custom_check_paths,
                expose_messages=probes_settings["EXPOSE_CHECK_MESSAGES"],
                include_duration=include_duration,
            )
        )

    return checks


def _unknown_check_result(detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": "unknown_check"}
    return "fail"
