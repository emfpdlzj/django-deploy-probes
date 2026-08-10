from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    run_check,
)


def _get_redis_client(location, timeout):
    import redis

    return redis.Redis.from_url(
        location,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
    )


def _check_redis_alias(config, detail_level):
    try:
        client = _get_redis_client(
            config["LOCATION"],
            config.get("TIMEOUT", 1.0),
        )
        client.ping()
    except ImportError:
        return failure_result("redis_package_missing", detail_level)
    except KeyError:
        return failure_result("location_missing", detail_level)
    except Exception as exc:
        return failure_result_for_exception(exc, "ping_failed", detail_level)
    return "ok"


def check_redis(redis_settings, detail_level="none", include_duration=False):
    return {
        f"redis.{alias}": run_check(
            _check_redis_alias,
            config,
            detail_level,
            include_duration=include_duration,
        )
        for alias, config in redis_settings.items()
    }
