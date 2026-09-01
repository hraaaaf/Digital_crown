"""Advertise the stable Digital Crown WebAuthn hostname on the cabinet LAN via mDNS."""
from __future__ import annotations

import logging
import os
import socket
import threading

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_zeroconf = None
_service_info = None
_starting = False

STABLE_LAN_HOSTNAME = "digitalcrown.local"
STABLE_HTTPS_PORT = 8005
STABLE_HTTPS_ORIGIN = f"https://{STABLE_LAN_HOSTNAME}:{STABLE_HTTPS_PORT}"


def _secure_lan_enabled() -> bool:
    return os.getenv("DIGITALCROWN_ENABLE_HTTPS", "false").strip().lower() in {"1", "true", "yes", "on"}


def _detect_lan_ip() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        value = sock.getsockname()[0]
        return value if value and not value.startswith("127.") else None
    except OSError:
        return None
    finally:
        sock.close()


def install_stable_lan_url_overrides() -> None:
    """Route pairing/frontend URLs through the same trusted HTTPS origin as WebAuthn."""
    if not _secure_lan_enabled():
        return
    # Delayed import avoids a module cycle: mobile_passkey imports this service after
    # mobile_legacy itself has already been imported.
    from backend.routers import mobile_legacy as legacy

    legacy.get_lan_base_url = lambda: STABLE_HTTPS_ORIGIN
    legacy.get_lan_frontend_url = lambda: STABLE_HTTPS_ORIGIN


def _close_mdns_sync(zc, info) -> None:
    """Perform zeroconf blocking shutdown outside the application event loop."""
    try:
        if info is not None:
            zc.unregister_service(info)
    except Exception:
        pass
    try:
        zc.close()
    except Exception:
        pass


def stop_mdns() -> None:
    global _zeroconf, _service_info, _starting
    with _lock:
        zc, info = _zeroconf, _service_info
        _zeroconf = None
        _service_info = None
        _starting = False
    if zc is not None:
        threading.Thread(
            target=_close_mdns_sync,
            args=(zc, info),
            name="digitalcrown-mdns-stop",
            daemon=True,
        ).start()


def _start_mdns_sync(lan_ip: str) -> None:
    """Perform zeroconf blocking registration outside the application event loop."""
    global _zeroconf, _service_info, _starting
    zc = None
    try:
        from zeroconf import ServiceInfo, Zeroconf

        zc = Zeroconf()
        info = ServiceInfo(
            type_="_https._tcp.local.",
            name="Digital Crown._https._tcp.local.",
            addresses=[socket.inet_aton(lan_ip)],
            port=STABLE_HTTPS_PORT,
            properties={b"app": b"digital-crown", b"scope": b"cabinet-lan"},
            server=f"{STABLE_LAN_HOSTNAME}.",
        )
        zc.register_service(info, allow_name_change=False)
        with _lock:
            _zeroconf = zc
            _service_info = info
            _starting = False
        logger.info("M6-I mDNS: %s -> %s", STABLE_HTTPS_ORIGIN, lan_ip)
    except Exception as exc:
        logger.warning("M6-I mDNS indisponible: %s", type(exc).__name__)
        with _lock:
            _starting = False
        if zc is not None:
            _close_mdns_sync(zc, None)


def start_mdns_if_secure() -> None:
    """Best-effort publish digitalcrown.local; WebAuthn still fails closed if unresolved."""
    global _starting
    if not _secure_lan_enabled():
        return

    # The stable URL must be installed even if mDNS publication itself later fails.
    # That avoids HTTPS pages receiving an HTTP/IP API base URL (mixed content).
    install_stable_lan_url_overrides()

    with _lock:
        if _zeroconf is not None or _starting:
            return
        lan_ip = _detect_lan_ip()
        if not lan_ip:
            logger.warning("M6-I mDNS non démarré: IP LAN introuvable.")
            return
        _starting = True

    threading.Thread(
        target=_start_mdns_sync,
        args=(lan_ip,),
        name="digitalcrown-mdns-start",
        daemon=True,
    ).start()
