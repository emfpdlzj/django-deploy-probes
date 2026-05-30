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


def get_request_ip(request, probes_settings):
    remote_addr = request.META.get("REMOTE_ADDR", "")
    client_ip_header = probes_settings.get("CLIENT_IP_HEADER")
    trusted_proxy_networks = probes_settings.get("TRUSTED_PROXY_NETWORKS", [])

    if not client_ip_header or not trusted_proxy_networks:
        return remote_addr

    if not is_internal_ip(remote_addr, trusted_proxy_networks):
        return remote_addr

    header_value = request.headers.get(client_ip_header, "")
    forwarded_ip = _extract_forwarded_client_ip(
        client_ip_header,
        header_value,
        trusted_proxy_networks,
        remote_addr,
    )
    return forwarded_ip or remote_addr


def security_forbidden_response(request, probes_settings, protect_healthz=False):
    if not protect_healthz or _protect_healthz_enabled(probes_settings):
        if probes_settings["INTERNAL_IP_ONLY"] and not is_internal_ip(
            get_request_ip(request, probes_settings),
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


def _extract_forwarded_client_ip(
    client_ip_header,
    header_value,
    trusted_proxy_networks,
    remote_addr,
):
    if not header_value:
        return None

    if client_ip_header.lower() == "x-forwarded-for":
        return _extract_x_forwarded_for_client_ip(
            header_value,
            trusted_proxy_networks,
            remote_addr,
        )

    return _normalize_ip_value(header_value)


def _extract_x_forwarded_for_client_ip(header_value, trusted_proxy_networks, remote_addr):
    forwarded_ips = [ip.strip() for ip in header_value.split(",") if ip.strip()]
    if not forwarded_ips:
        return None

    normalized_ips = [_normalize_ip_value(ip) for ip in forwarded_ips]
    if any(ip is None for ip in normalized_ips):
        return None

    for candidate_ip in reversed([*normalized_ips, remote_addr]):
        if not is_internal_ip(candidate_ip, trusted_proxy_networks):
            return candidate_ip

    return normalized_ips[0]


def _normalize_ip_value(value):
    try:
        return str(ip_address(value.strip()))
    except ValueError:
        return None
