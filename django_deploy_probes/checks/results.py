from time import perf_counter


TIMEOUT_EXCEPTION_NAMES = {
    "ConnectTimeout",
    "ConnectTimeoutError",
    "ConnectionTimeout",
    "ConnectionTimeoutError",
    "OperationTimedOut",
    "ReadTimeout",
    "ReadTimeoutError",
    "SocketTimeout",
    "TimeoutError",
}


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


def failure_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def failure_result_for_exception(exc, fallback_reason, detail_level):
    reason = "timeout" if is_timeout_exception(exc) else fallback_reason
    return failure_result(reason, detail_level)


def is_timeout_exception(exc):
    pending = [exc]
    seen = set()

    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        if isinstance(current, TimeoutError):
            return True
        if any(
            exception_class.__name__ in TIMEOUT_EXCEPTION_NAMES
            for exception_class in type(current).__mro__
        ):
            return True

        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)

    return False


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
