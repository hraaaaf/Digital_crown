"""Canonical V1.5-01 cabinet topology and LAN transport contract.

Topology roles are descriptive deployment roles only. They never grant
application permissions and must remain separate from workstation UX modes.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import os
import socket
from typing import Mapping

TOPOLOGY_ROLES = ("server", "workstation", "reception", "connected_device")
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True)
class CabinetNetworkContract:
    environment: str
    host: str
    port: int
    https_enabled: bool
    cert_file: str
    key_file: str
    lan_exposed: bool
    tls_ready: bool

    @property
    def scheme(self) -> str:
        return "https" if self.https_enabled else "http"

    @property
    def base_url(self) -> str:
        host = self.host
        if host == "0.0.0.0":
            detected = detect_lan_ip()
            if not detected:
                raise RuntimeError("RESEAU : aucune adresse LAN utilisable détectée pour publier une URL cabinet.")
            host = detected
        elif host == "::":
            raise RuntimeError("RESEAU : adresse IPv6 wildcard non publiable comme URL cabinet.")
        return f"{self.scheme}://{host}:{self.port}"

    def diagnostics(self) -> dict:
        return {
            "topologyRole": "server",
            "knownTopologyRoles": list(TOPOLOGY_ROLES),
            "environment": self.environment,
            "bindHost": self.host,
            "port": self.port,
            "scheme": self.scheme,
            "lanExposed": self.lan_exposed,
            "tlsEnabled": self.https_enabled,
            "tlsReady": self.tls_ready,
            "remediation": _remediation_code(self),
        }


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_loopback(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized in LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _usable_lan_ipv4(candidate: str) -> str | None:
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if address.version != 4 or address.is_loopback or address.is_unspecified or address.is_link_local:
        return None
    return candidate


def detect_lan_ip() -> str | None:
    """Best-effort LAN discovery without requiring Internet reachability.

    UDP ``connect`` does not send application data; it asks the local routing
    table which source address would be used. Private documentation/test-net
    destinations keep discovery independent from public DNS or Internet hosts.
    Hostname resolution is retained only as a local fallback. Failure remains
    fail-closed: callers never publish an invented or loopback LAN address.
    """
    for destination in (("192.0.2.1", 9), ("198.51.100.1", 9), ("203.0.113.1", 9)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(destination)
                candidate = _usable_lan_ipv4(sock.getsockname()[0])
            if candidate:
                return candidate
        except OSError:
            continue

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM):
            candidate = _usable_lan_ipv4(info[4][0])
            if candidate:
                return candidate
    except (OSError, ValueError):
        pass
    return None


def resolve_cabinet_network(
    environ: Mapping[str, str] | None = None,
    *,
    validate_tls_files: bool = True,
) -> CabinetNetworkContract:
    env = environ if environ is not None else os.environ
    environment = env.get("ENVIRONMENT", "development").strip().lower()
    host = env.get("CABINET_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(env.get("CABINET_PORT", "8005"))
    except ValueError as exc:
        raise RuntimeError("RESEAU : CABINET_PORT doit être un entier valide.") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("RESEAU : CABINET_PORT doit être compris entre 1 et 65535.")

    https_enabled = _truthy(env.get("DIGITALCROWN_ENABLE_HTTPS"))
    cert_file = env.get("DIGITALCROWN_TLS_CERT_FILE", "").strip()
    key_file = env.get("DIGITALCROWN_TLS_KEY_FILE", "").strip()
    loopback = _is_loopback(host)

    if https_enabled:
        if port != 8005:
            raise RuntimeError("SECURITE : HTTPS mobile/WebAuthn exige CABINET_PORT=8005.")
        if not cert_file or not key_file:
            raise RuntimeError("SECURITE : HTTPS cabinet exige DIGITALCROWN_TLS_CERT_FILE et DIGITALCROWN_TLS_KEY_FILE.")
        if validate_tls_files and (not os.path.isfile(cert_file) or not os.path.isfile(key_file)):
            raise RuntimeError("SECURITE : certificat/clé TLS cabinet introuvable.")
    elif environment in {"cabinet", "production"} and not loopback:
        raise RuntimeError(
            "SECURITE : exposition réseau cabinet/production refusée sans HTTPS explicite ; "
            "utilisez 127.0.0.1 ou configurez TLS."
        )

    return CabinetNetworkContract(
        environment=environment,
        host=host,
        port=port,
        https_enabled=https_enabled,
        cert_file=cert_file,
        key_file=key_file,
        lan_exposed=not loopback,
        tls_ready=https_enabled and bool(cert_file and key_file),
    )


def get_cabinet_base_url(
    environ: Mapping[str, str] | None = None,
    *,
    validate_tls_files: bool = True,
) -> str:
    """Return the canonical reachable backend URL or fail closed.

    ``environ`` is an explicit integration seam for installers/tests; runtime
    callers use the real process environment. TLS file validation remains on by
    default and can be disabled only by an explicit caller.
    """
    return resolve_cabinet_network(
        environ,
        validate_tls_files=validate_tls_files,
    ).base_url


def _remediation_code(contract: CabinetNetworkContract) -> str | None:
    if not contract.lan_exposed:
        return "LAN_DISABLED_LOOPBACK_ONLY"
    if contract.https_enabled and contract.tls_ready:
        return None
    return "TLS_REQUIRED_FOR_LAN"
