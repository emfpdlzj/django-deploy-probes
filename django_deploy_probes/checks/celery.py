RESULT_BACKEND_PROBE_KEY = "django-deploy-probes-readyz"


def _get_celery_app():
    from celery import current_app

    return current_app


def _check_broker(app, timeout):
    with app.connection_for_read() as connection:
        connection.ensure_connection(max_retries=1, timeout=timeout)


def _check_workers(app, timeout):
    responses = app.control.ping(timeout=timeout)
    if not responses:
        raise RuntimeError("no celery workers responded")
    return responses


def _check_result_backend(app, timeout):
    app.backend.get(RESULT_BACKEND_PROBE_KEY)


def _fail_result(reason, detail_level):
    if detail_level == "safe":
        return {"status": "fail", "reason": reason}
    return "fail"


def check_celery(celery_settings, detail_level="none"):
    results = {}
    try:
        app = _get_celery_app()
    except ImportError:
        app = None
        app_failure_reason = "celery_package_missing"
    except Exception:
        app = None
        app_failure_reason = "celery_app_unavailable"
    else:
        app_failure_reason = None

    if celery_settings.get("BROKER"):
        check_name = "celery.broker"
        try:
            if app is None:
                raise RuntimeError("celery app is unavailable")
            _check_broker(app, celery_settings.get("TIMEOUT", 1.0))
        except Exception:
            results[check_name] = _fail_result(
                app_failure_reason or "broker_unavailable", detail_level
            )
        else:
            results[check_name] = "ok"

    if celery_settings.get("WORKERS"):
        check_name = "celery.workers"
        try:
            if app is None:
                raise RuntimeError("celery app is unavailable")
            _check_workers(app, celery_settings.get("TIMEOUT", 1.0))
        except Exception:
            results[check_name] = _fail_result(
                app_failure_reason or "workers_unavailable", detail_level
            )
        else:
            results[check_name] = "ok"

    if celery_settings.get("RESULT_BACKEND"):
        check_name = "celery.result_backend"
        try:
            if app is None:
                raise RuntimeError("celery app is unavailable")
            _check_result_backend(app, celery_settings.get("TIMEOUT", 1.0))
        except Exception:
            results[check_name] = _fail_result(
                app_failure_reason or "result_backend_unavailable",
                detail_level,
            )
        else:
            results[check_name] = "ok"

    return results
