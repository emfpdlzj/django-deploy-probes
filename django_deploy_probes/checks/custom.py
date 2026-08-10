from django.utils.module_loading import import_string

from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    run_named_checks,
)


def _default_check_name(dotted_path):
    return dotted_path.rsplit(".", 1)[-1]


def _normalize_custom_result(dotted_path, result, expose_messages):
    default_name = _default_check_name(dotted_path)

    if isinstance(result, bool):
        return {default_name: "ok" if result else "fail"}

    if isinstance(result, dict):
        name = result.get("name", default_name)
        status = result.get("status", "fail")
        message = result.get("message")

        if expose_messages and message:
            return {name: {"status": status, "message": message}}
        return {name: status}

    return {default_name: "fail"}


def _run_custom_check(dotted_path, expose_messages, detail_level):
    try:
        custom_check = import_string(dotted_path)
        if not callable(custom_check):
            raise TypeError("custom check is not callable")
        return _normalize_custom_result(dotted_path, custom_check(), expose_messages)
    except Exception as exc:
        return {
            _default_check_name(dotted_path): failure_result_for_exception(
                exc,
                "custom_check_failed",
                detail_level,
            )
        }


def check_custom_checks(
    custom_check_paths,
    expose_messages=False,
    detail_level="none",
    include_duration=False,
):
    results = {}

    for dotted_path in custom_check_paths:
        check_results = run_named_checks(
            _run_custom_check,
            dotted_path,
            expose_messages,
            detail_level,
            include_duration=include_duration,
        )
        for name, result in check_results.items():
            if name in results:
                results[name] = failure_result("duplicate_check_name", detail_level)
            else:
                results[name] = result

    return results
