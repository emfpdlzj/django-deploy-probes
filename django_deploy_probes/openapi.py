from django_deploy_probes.conf import get_deploy_probes_settings


HEALTHZ_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["ok"],
        },
    },
    "required": ["status"],
}

READYZ_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["ready", "not_ready"],
        },
        "checks": {
            "type": "object",
            "additionalProperties": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "additionalProperties": True,
                    },
                ],
            },
        },
    },
    "required": ["status", "checks"],
}

STARTUPZ_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["started", "not_started"],
        },
        "checks": {
            "type": "object",
            "additionalProperties": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "additionalProperties": True,
                    },
                ],
            },
        },
    },
    "required": ["status", "checks"],
}

VERSION_SCHEMA = {
    "type": "object",
    "properties": {
        "service": {"type": "string"},
        "environment": {"type": "string"},
        "version": {"type": "string"},
        "commit": {"type": "string"},
        "branch": {"type": "string"},
        "build_time": {"type": "string"},
        "slot": {"type": "string"},
    },
    "required": [
        "service",
        "environment",
        "version",
    ],
}

PROBE_OPENAPI_SCHEMAS = {
    "healthz": {
        "summary": "Liveness probe",
        "description": (
            "Returns process liveness without checking external dependencies. "
            "Intended for Docker HEALTHCHECK and Kubernetes livenessProbe."
        ),
        "responses": {
            200: {
                "description": "The Django process is alive.",
                "schema": HEALTHZ_SCHEMA,
            },
            403: {
                "description": "The probe is protected by security settings.",
            },
        },
    },
    "readyz": {
        "summary": "Readiness probe",
        "description": (
            "Checks whether the application is ready to receive traffic. "
            "Configured dependency checks are returned by name."
        ),
        "responses": {
            200: {
                "description": "The application is ready to receive traffic.",
                "schema": READYZ_SCHEMA,
            },
            503: {
                "description": "One or more readiness checks failed.",
                "schema": READYZ_SCHEMA,
            },
            403: {
                "description": "The probe is protected by security settings.",
            },
        },
    },
    "startupz": {
        "summary": "Startup probe",
        "description": (
            "Checks whether application startup requirements have completed. "
            "Intended for Kubernetes startupProbe and deploy bootstrap validation."
        ),
        "responses": {
            200: {
                "description": "The application has completed startup requirements.",
                "schema": STARTUPZ_SCHEMA,
            },
            503: {
                "description": "One or more startup checks failed.",
                "schema": STARTUPZ_SCHEMA,
            },
            403: {
                "description": "The probe is protected by security settings.",
            },
        },
    },
    "version": {
        "summary": "Deployment version",
        "description": (
            "Returns deployment metadata such as service name, environment, "
            "and version. Commit, branch, build time, and deployment slot are "
            "included only when EXPOSE_BUILD_INFO=True."
        ),
        "responses": {
            200: {
                "description": "Current deployment metadata.",
                "schema": VERSION_SCHEMA,
            },
            403: {
                "description": (
                    "Version exposure is disabled or the probe is protected by security settings."
                ),
            },
        },
    },
}


def apply_openapi_metadata(view_name, view):
    probes_settings = get_deploy_probes_settings()
    if not probes_settings["ENABLE_OPENAPI"]:
        return view

    try:
        from rest_framework.decorators import api_view
        from drf_spectacular.utils import OpenApiResponse, extend_schema
    except ImportError:
        return view

    schema = PROBE_OPENAPI_SCHEMAS[view_name]
    responses = {}
    for status_code, response in schema["responses"].items():
        responses[status_code] = OpenApiResponse(
            response=response.get("schema"),
            description=response["description"],
        )

    metadata = {
        "summary": schema["summary"],
        "description": schema["description"],
        "tags": [probes_settings["OPENAPI_TAG"]],
        "responses": responses,
    }
    view._deploy_probes_openapi = metadata
    return extend_schema(**metadata)(api_view(["GET"])(view))
