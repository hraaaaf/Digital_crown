"""Advertise the stable Digital Crown WebAuthn hostname on the cabinet LAN via mDNS."""
from __future__ import annotations

import atexit
import logging
import os
import socket
import threading

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_zeroconf = None
_service_info = None


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


def stop_mdns() -> None:
    global _zeroconf, _service_info
    with _lock:
        zc, info = _zeroconf, _service_info
        _zeroconf = None
        _service_info = None
    if zc is not None:
        try:
            if info is not None:
                zc.unregister_service(info)
        except Exception:
            pass
        try:
            zc.close()
        except Exception:
            pass


def start_mdns_if_secure() -> None:
    """Best-effort publish digitalcrown.local; WebAuthn still fails closed if unresolved."""
    global _zeroconf, _service_info
    if not _secure_lan_enabled():
        return
    with _lock:
        if _zeroconf is not None:
            return
        lan_ip = _detect_lan_ip()
        if not lan_ip:
            logger.warning("M6-I mDNS non démarré: IP LAN introuvable.")
            return
        zc = None
        try:
            from zeroconf import ServiceInfo, Zeroconf
            zc = Zeroconf()
            info = ServiceInfo(
                type_="_https._tcp.local.",
                name="Digital Crown._https._tcp.local.",
                addresses=[socket.inet_aton(lan_ip)],
                port=5173,
                properties={b"app": b"digital-crown", b"scope": b"cabinet-lan"},
                server="digitalcrown.local.",
            )
            zc.register_service(info, allow_name_change=False)
            _zeroconf = zc
            _service_info = info
            logger.info("M6-I mDNS: https://digitalcrown.local:5173 -> %s", lan_ip)
        except Exception as exc:
            logger.warning("M6-I mDNS indisponible: %s", type(exc).__name__)
            if zc is not None:
                try:
                    zc.close()
                except Exception:
                    pass


# The secure LAN responder is process-scoped. Normal launcher/EXE shutdown must
# release multicast resources even though publication itself is best-effort.
atexit.register(stop_mdns)
