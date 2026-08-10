from django_deploy_probes.checks.celery import check_celery
from django_deploy_probes.checks.custom import check_custom_checks
from django_deploy_probes.checks.database import check_databases
from django_deploy_probes.checks.migrations import check_migrations
from django_deploy_probes.checks.redis import check_redis
from django_deploy_probes.checks.results import failure_result, run_check
from django_deploy_probes.checks.storage import check_storage


BUILTIN_CHECKS = {
    "database": lambda probes_settings: (
        check_databases,
        (probes_settings["DATABASES"],),
        {
            "detail_level": probes_settings["DETAIL_LEVEL"],
            "include_duration": probes_settings["INCLUDE_CHECK_DURATIONS"],
        },
    ),
    "redis": lambda probes_settings: (
        check_redis,
        (probes_settings["REDIS"],),
        {
            "detail_level": probes_settings["DETAIL_LEVEL"],
            "include_duration": probes_settings["INCLUDE_CHECK_DURATIONS"],
        },
    ),
    "storage": lambda probes_settings: (
        check_storage,
        (probes_settings["STORAGE"],),
        {
            "detail_level": probes_settings["DETAIL_LEVEL"],
            "include_duration": probes_settings["INCLUDE_CHECK_DURATIONS"],
        },
    ),
    "celery": lambda probes_settings: (
        check_celery,
        (probes_settings["CELERY"],),
        {
            "detail_level": probes_settings["DETAIL_LEVEL"],
            "include_duration": probes_settings["INCLUDE_CHECK_DURATIONS"],
        },
    ),
    "migrations": lambda probes_settings: (
        check_migrations,
        (probes_settings["MIGRATIONS"],),
        {
            "detail_level": probes_settings["DETAIL_LEVEL"],
            "include_duration": probes_settings["INCLUDE_CHECK_DURATIONS"],
        },
    ),
}


def run_configured_checks(probes_settings, check_names, custom_check_paths=None):
    checks = {}
    detail_level = probes_settings["DETAIL_LEVEL"]
    include_duration = probes_settings["INCLUDE_CHECK_DURATIONS"]

    for check_name in check_names:
        check_factory = BUILTIN_CHECKS.get(check_name)
        if check_factory is None:
            _merge_check_results(
                checks,
                {
                    check_name: run_check(
                        _unknown_check_result,
                        detail_level,
                        include_duration=include_duration,
                    )
                },
                detail_level,
            )
            continue

        check_func, args, kwargs = check_factory(probes_settings)
        _merge_check_results(checks, check_func(*args, **kwargs), detail_level)

    custom_check_paths = custom_check_paths or []
    if custom_check_paths:
        _merge_check_results(
            checks,
            check_custom_checks(
                custom_check_paths,
                expose_messages=probes_settings["EXPOSE_CHECK_MESSAGES"],
                detail_level=detail_level,
                include_duration=include_duration,
            ),
            detail_level,
        )

    return checks


def _unknown_check_result(detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": "unknown_check"}
    return "fail"


def _merge_check_results(target, additions, detail_level):
    for name, result in additions.items():
        if name in target:
            target[name] = failure_result("duplicate_check_name", detail_level)
        else:
            target[name] = result
