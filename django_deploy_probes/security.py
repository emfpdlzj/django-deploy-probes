import secrets
from ipaddress import ip_address, ip_network

from django.http import HttpResponseForbidden


def is_internal_ip(remote_addr, networks):
    try:
        request_ip = ip_address(remote_addr)
        parsed_networks = [ip_network(network) for network in networks]
    except ValueError:
        return False

    return any(request_ip in network for network in parsed_networks)


def security_forbidden_response(request, probes_settings, protect_healthz=False):
    if not protect_healthz or _protect_healthz_enabled(probes_settings):
        if probes_settings["INTERNAL_IP_ONLY"] and not is_internal_ip(
            request.META.get("REMOTE_ADDR", ""),
            probes_settings["INTERNAL_IP_NETWORKS"],
        ):
            return HttpResponseForbidden()

        header_token_validation = probes_settings["HEADER_TOKEN_VALIDATION"]
        if header_token_validation:
            if not isinstance(header_token_validation, dict):
                return HttpResponseForbidden()

            header_name = header_token_validation.get("HEADER_NAME", "X-Probe-Token")
            token = header_token_validation.get("TOKEN")
            request_token = request.headers.get(header_name, "")
            if not token or not secrets.compare_digest(request_token, str(token)):
                return HttpResponseForbidden()

    return None


def _protect_healthz_enabled(probes_settings):
    header_token_validation = probes_settings["HEADER_TOKEN_VALIDATION"]
    if isinstance(header_token_validation, dict):
        return header_token_validation.get("PROTECT_HEALTHZ", False)
    return False
