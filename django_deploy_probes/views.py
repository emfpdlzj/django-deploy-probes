from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_GET

from django_deploy_probes.conf import get_deploy_probes_settings
from django_deploy_probes.openapi import apply_openapi_metadata
from django_deploy_probes.probes import run_probe
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

    result = run_probe("healthz", probes_settings)
    return JsonResponse(result.payload, status=result.status_code)


@require_GET
def readyz(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    result = run_probe("readyz", probes_settings)
    return JsonResponse(result.payload, status=result.status_code)


@require_GET
def startupz(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    result = run_probe("startupz", probes_settings)
    return JsonResponse(result.payload, status=result.status_code)


@require_GET
def version(request):
    probes_settings = get_deploy_probes_settings()
    forbidden_response = security_forbidden_response(request, probes_settings)
    if forbidden_response is not None:
        return forbidden_response

    if not probes_settings["EXPOSE_VERSION"]:
        return HttpResponseForbidden()

    result = run_probe("version", probes_settings)
    return JsonResponse(result.payload, status=result.status_code)


healthz = apply_openapi_metadata("healthz", healthz)
readyz = apply_openapi_metadata("readyz", readyz)
startupz = apply_openapi_metadata("startupz", startupz)
version = apply_openapi_metadata("version", version)
