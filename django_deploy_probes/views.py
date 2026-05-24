from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_GET

from django_deploy_probes.checks.registry import run_configured_checks
from django_deploy_probes.checks.results import check_is_ok
from django_deploy_probes.conf import get_deploy_probes_settings
from django_deploy_probes.openapi import apply_openapi_metadata
from django_deploy_probes.security import security_forbidden_response


@require_GET
def healthz(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(
        request,
        probes_settings,
        protect_healthz=True,
    )
    if forbidden_response is not None:
        return forbidden_response

    return JsonResponse({"status": "ok"})


@require_GET
def readyz(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    checks = run_configured_checks(
        probes_settings,
        probes_settings["READY_CHECKS"],
        custom_check_paths=[
            *probes_settings["READY_CUSTOM_CHECKS"],
            *probes_settings["CUSTOM_CHECKS"],
        ],
    )
    is_ready = _probe_is_ok(checks, require_checks=probes_settings["REQUIRE_READY_CHECKS"])
    status_code = 200 if is_ready else 503
    status = "ready" if is_ready else "not_ready"

    return JsonResponse({"status": status, "checks": checks}, status=status_code)


@require_GET
def startupz(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    checks = run_configured_checks(
        probes_settings,
        probes_settings["STARTUP_CHECKS"],
        custom_check_paths=probes_settings["STARTUP_CUSTOM_CHECKS"],
    )
    is_started = _probe_is_ok(checks, require_checks=probes_settings["REQUIRE_STARTUP_CHECKS"])
    status_code = 200 if is_started else 503
    status = "started" if is_started else "not_started"

    return JsonResponse({"status": status, "checks": checks}, status=status_code)


def _probe_is_ok(checks, require_checks=False):
    if require_checks and not checks:
        return False
    return all(check_is_ok(result) for result in checks.values())


@require_GET
def version(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    if not probes_settings["EXPOSE_VERSION"]:
        return HttpResponseForbidden()

    payload = {
        "service": probes_settings["SERVICE_NAME"],
        "environment": probes_settings["ENVIRONMENT"],
        "version": probes_settings["VERSION"],
    }

    if probes_settings["EXPOSE_BUILD_INFO"]:
        payload.update(
            {
                "commit": probes_settings["COMMIT"],
                "branch": probes_settings["BRANCH"],
                "build_time": probes_settings["BUILD_TIME"],
                "slot": probes_settings["SLOT"],
            }
        )

    return JsonResponse(payload)


healthz = apply_openapi_metadata("healthz", healthz)
readyz = apply_openapi_metadata("readyz", readyz)
startupz = apply_openapi_metadata("startupz", startupz)
version = apply_openapi_metadata("version", version)
