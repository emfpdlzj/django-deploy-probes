from time import perf_counter


def check_is_ok(result):
    if isinstance(result, dict):
        return result.get("status") == "ok"
    return result == "ok"


def normalize_check_result(result):
    if isinstance(result, dict):
        normalized = dict(result)
        normalized.setdefault("status", "fail")
        return normalized
    if result == "ok":
        return {"status": "ok"}
    return {"status": "fail"}


def with_duration(check_func, *args, include_duration=False, **kwargs):
    start = perf_counter()
    results = check_func(*args, **kwargs)
    if not include_duration:
        return results

    duration_ms = round((perf_counter() - start) * 1000, 3)
    return {
        name: {
            **normalize_check_result(result),
            "duration_ms": duration_ms,
        }
        for name, result in results.items()
    }
