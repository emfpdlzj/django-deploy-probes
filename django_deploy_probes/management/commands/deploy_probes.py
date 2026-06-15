import json

from django.core.management.base import BaseCommand
from django.core.management.base import SystemCheckError

from django_deploy_probes.probes import PROBE_NAMES, run_probe


class Command(BaseCommand):
    help = "Run deploy probes from the command line."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "probe",
            choices=PROBE_NAMES,
            help="Probe to run.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Render the probe payload as JSON.",
        )

    def handle(self, *args, **options):
        try:
            self.check()
        except SystemCheckError as exc:
            self.stderr.write(str(exc))
            raise SystemExit(2) from exc

        probe_name = options["probe"]
        try:
            result = run_probe(probe_name)
        except Exception as exc:
            self.stderr.write(str(exc))
            raise SystemExit(3) from exc

        self.stdout.write(self._render_output(result.payload, as_json=options["json"]))
        if not result.ok:
            raise SystemExit(1)

    def _render_output(self, payload, as_json=False):
        if as_json:
            return json.dumps(payload)

        if "checks" in payload:
            lines = [payload["status"]]
            for check_name, check_result in payload["checks"].items():
                lines.append(f"{check_name}: {self._format_check_result(check_result)}")
            return "\n".join(lines)

        return "\n".join(f"{key}={value}" for key, value in payload.items())

    def _format_check_result(self, check_result):
        if isinstance(check_result, dict):
            return json.dumps(check_result)
        return str(check_result)
