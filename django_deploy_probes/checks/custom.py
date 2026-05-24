from django.utils.module_loading import import_string


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


def check_custom_checks(custom_check_paths, expose_messages=False):
    results = {}

    for dotted_path in custom_check_paths:
        try:
            custom_check = import_string(dotted_path)
            if not callable(custom_check):
                raise TypeError("custom check is not callable")
            results.update(
                _normalize_custom_result(
                    dotted_path,
                    custom_check(),
                    expose_messages,
                )
            )
        except Exception:
            results[_default_check_name(dotted_path)] = "fail"

    return results
