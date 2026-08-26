import base64
import ipaddress
import json
import logging
import os
import socket
import threading
from pathlib import Path
from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from backend import models
from backend.core.paths import AppPaths
from backend.models_mobile_push import MobilePushSubscription
from backend.services.mobile_notification_policy import user_can_receive_mobile_notification

logger = logging.getLogger(__name__)
_VAPID_LOCK = threading.Lock()

GENERIC_OS_PUSH_PAYLOAD = {"kind": "alerts"}


def _vapid_key_path() -> Path:
    return AppPaths.get_config_dir() / "web_push_vapid.json"


def _public_key_b64(private_key: ec.EllipticCurvePrivateKey) -> str:
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _serialize_private_key(private_key: ec.EllipticCurvePrivateKey) -> str:
    der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.urlsafe_b64encode(der).rstrip(b"=").decode("ascii")


def _deserialize_private_key(encoded: str) -> ec.EllipticCurvePrivateKey:
    try:
        padding = "=" * ((4 - len(encoded) % 4) % 4)
        der = base64.urlsafe_b64decode(encoded + padding)
        key = serialization.load_der_private_key(der, password=None)
    except Exception as exc:
        raise RuntimeError("Web Push VAPID key store invalide.") from exc
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise RuntimeError("Web Push VAPID key store invalide.")
    return key


def get_or_create_vapid_keypair() -> tuple[str, str]:
    """Return (private PKCS8 DER b64url, public uncompressed P-256 key b64url)."""
    path = _vapid_key_path()
    with _VAPID_LOCK:
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                private_key = _deserialize_private_key(payload["private_key_b64"])
                public_key = _public_key_b64(private_key)
                if payload.get("public_key") != public_key:
                    raise RuntimeError("Web Push VAPID key store incohérent.")
            except RuntimeError:
                raise
            except Exception as exc:
                raise RuntimeError("Web Push VAPID key store invalide.") from exc
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            private_key = ec.generate_private_key(ec.SECP256R1())
            public_key = _public_key_b64(private_key)
            payload = {
                "version": 1,
                "private_key_b64": _serialize_private_key(private_key),
                "public_key": public_key,
            }
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, path)
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass

        # pywebpush/py-vapid accepts a DER representation encoded as a string.
        # Passing raw PEM *content* is not supported (a PEM *file path* would be).
        return _serialize_private_key(private_key), public_key


def _is_public_push_endpoint(endpoint: str) -> bool:
    """Prevent a forged subscription from turning the cabinet backend into an SSRF primitive."""
    try:
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False
        if parsed.fragment:
            return False
        infos = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not infos:
            return False
        for info in infos:
            address = ipaddress.ip_address(info[4][0])
            if (
                address.is_private
                or address.is_loopback
                or address.is_link_local
                or address.is_multicast
                or address.is_reserved
                or address.is_unspecified
            ):
                return False
        return True
    except Exception:
        return False


def _approval_value(user) -> str:
    value = getattr(user, "approval_status", None)
    return getattr(value, "value", value) or "approved"


def send_push_for_alert_types(db: Session, employer_id: int, alert_types: list[str]) -> int:
    """Send one generic OS signal only to active paired users authorized for at least one alert type."""
    normalized_types = [str(value) for value in dict.fromkeys(alert_types) if value]
    if not normalized_types:
        return 0

    rows = (
        db.query(MobilePushSubscription, models.User, models.MobilePairedDevice)
        .join(models.User, models.User.id == MobilePushSubscription.user_id)
        .join(models.MobilePairedDevice, models.MobilePairedDevice.device_id == MobilePushSubscription.device_id)
        .filter(
            MobilePushSubscription.employer_id == int(employer_id),
            models.MobilePairedDevice.employer_id == MobilePushSubscription.employer_id,
            models.MobilePairedDevice.user_id == MobilePushSubscription.user_id,
            models.MobilePairedDevice.revoked_at.is_(None),
            models.User.is_active == True,  # noqa: E712
            models.User.is_suspended == False,  # noqa: E712
            models.User.is_archived == False,  # noqa: E712
        )
        .all()
    )
    eligible = []
    for subscription, user, _device in rows:
        if user.get_employer_id() != int(employer_id):
            continue
        if user.employer_id is not None and _approval_value(user) != "approved":
            continue
        if any(user_can_receive_mobile_notification(user, alert_type) for alert_type in normalized_types):
            eligible.append(subscription)
    if not eligible:
        return 0

    try:
        private_key, public_key = get_or_create_vapid_keypair()
    except Exception as exc:
        logger.error("Web Push VAPID unavailable: %s", type(exc).__name__)
        return 0

    stale_ids: list[int] = [
        subscription.id for subscription in eligible
        if subscription.vapid_public_key != public_key
    ]
    eligible = [
        subscription for subscription in eligible
        if subscription.vapid_public_key == public_key
    ]
    sent = 0
    payload = json.dumps(GENERIC_OS_PUSH_PAYLOAD, separators=(",", ":"), ensure_ascii=False)
    subject = os.getenv("WEB_PUSH_VAPID_SUBJECT", "https://digital-crown.local")

    for subscription in eligible:
        if not _is_public_push_endpoint(subscription.endpoint):
            logger.warning("Web Push endpoint not currently resolvable as public for subscription id=%s", subscription.id)
            continue
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
                ttl=300,
            )
            sent += 1
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in (404, 410):
                stale_ids.append(subscription.id)
            else:
                logger.warning("Web Push delivery failed status=%s", status_code or "unknown")
        except Exception as exc:
            logger.warning("Web Push delivery failed: %s", type(exc).__name__)

    if stale_ids:
        db.query(MobilePushSubscription).filter(MobilePushSubscription.id.in_(stale_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    return sent
