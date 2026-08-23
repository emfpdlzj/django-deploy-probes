from django_deploy_probes.checks.results import (
    failure_result,
    failure_result_for_exception,
    is_timeout_exception,
    run_check,
)

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


def _check_result_backend(app):
    app.backend.get(RESULT_BACKEND_PROBE_KEY)


def _check_celery_operation(
    app,
    app_failure_reason,
    operation,
    timeout,
    fallback_reason,
    detail_level,
):
    if app_failure_reason is not None:
        return failure_result(app_failure_reason, detail_level)

    try:
        operation(app, timeout)
    except Exception as exc:
        return failure_result_for_exception(exc, fallback_reason, detail_level)
    return "ok"


def _check_result_backend_with_timeout(app, timeout):
    del timeout
    _check_result_backend(app)


def check_celery(celery_settings, detail_level="none", include_duration=False):
    results = {}
    timeout = celery_settings.get("TIMEOUT", 1.0)
    try:
        app = _get_celery_app()
    except ImportError:
        app = None
        app_failure_reason = "celery_package_missing"
    except Exception as exc:
        app = None
        app_failure_reason = "timeout" if is_timeout_exception(exc) else "celery_app_unavailable"
    else:
        app_failure_reason = None

    if celery_settings.get("BROKER"):
        results["celery.broker"] = run_check(
            _check_celery_operation,
            app,
            app_failure_reason,
            _check_broker,
            timeout,
            "broker_unavailable",
            detail_level,
            include_duration=include_duration,
        )

    if celery_settings.get("WORKERS"):
        results["celery.workers"] = run_check(
            _check_celery_operation,
            app,
            app_failure_reason,
            _check_workers,
            timeout,
            "workers_unavailable",
            detail_level,
            include_duration=include_duration,
        )

    if celery_settings.get("RESULT_BACKEND"):
        results["celery.result_backend"] = run_check(
            _check_celery_operation,
            app,
            app_failure_reason,
            _check_result_backend_with_timeout,
            timeout,
            "result_backend_unavailable",
            detail_level,
            include_duration=include_duration,
        )

    return results
