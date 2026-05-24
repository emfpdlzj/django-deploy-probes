def _get_redis_client(location, timeout):
    import redis

    return redis.Redis.from_url(
        location,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
    )


def _fail_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def check_redis(redis_settings, detail_level="none"):
    results = {}
    for alias, config in redis_settings.items():
        check_name = f"redis.{alias}"
        try:
            client = _get_redis_client(
                config["LOCATION"],
                config.get("TIMEOUT", 1.0),
            )
            client.ping()
        except ImportError:
            results[check_name] = _fail_result("redis_package_missing", detail_level)
        except KeyError:
            results[check_name] = _fail_result("location_missing", detail_level)
        except Exception:
            results[check_name] = _fail_result("ping_failed", detail_level)
        else:
            results[check_name] = "ok"
    return results
