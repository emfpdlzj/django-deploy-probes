from dataclasses import dataclass

from django_deploy_probes.checks.registry import run_configured_checks
from django_deploy_probes.checks.results import check_is_ok
from django_deploy_probes.conf import get_deploy_probes_settings

PROBE_NAMES = ("healthz", "readyz", "startupz", "version")


@dataclass(frozen=True)
class ProbeResult:
    name: str
    ok: bool
    status_code: int
    payload: dict


def run_probe(probe_name, probes_settings=None):
    probes_settings = probes_settings or get_deploy_probes_settings()

    if probe_name == "healthz":
        return ProbeResult(
            name="healthz",
            ok=True,
            status_code=200,
            payload={"status": "ok"},
        )

    if probe_name == "readyz":
        checks = run_configured_checks(
            probes_settings,
            probes_settings["READY_CHECKS"],
            custom_check_paths=[
                *probes_settings["READY_CUSTOM_CHECKS"],
                *probes_settings["CUSTOM_CHECKS"],
            ],
        )
        is_ready = _probe_is_ok(checks, require_checks=probes_settings["REQUIRE_READY_CHECKS"])
        return ProbeResult(
            name="readyz",
            ok=is_ready,
            status_code=200 if is_ready else 503,
            payload={
                "status": "ready" if is_ready else "not_ready",
                "checks": checks,
            },
        )

    if probe_name == "startupz":
        checks = run_configured_checks(
            probes_settings,
            probes_settings["STARTUP_CHECKS"],
            custom_check_paths=probes_settings["STARTUP_CUSTOM_CHECKS"],
        )
        is_started = _probe_is_ok(
            checks,
            require_checks=probes_settings["REQUIRE_STARTUP_CHECKS"],
        )
        return ProbeResult(
            name="startupz",
            ok=is_started,
            status_code=200 if is_started else 503,
            payload={
                "status": "started" if is_started else "not_started",
                "checks": checks,
            },
        )

    if probe_name == "version":
        return ProbeResult(
            name="version",
            ok=True,
            status_code=200,
            payload=get_version_payload(probes_settings),
        )

    raise ValueError(f"Unknown probe: {probe_name}")


def get_version_payload(probes_settings=None):
    probes_settings = probes_settings or get_deploy_probes_settings()
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

    return payload


def _probe_is_ok(checks, require_checks=False):
    if require_checks and not checks:
        return False
    return all(check_is_ok(result) for result in checks.values())
