"""LOT08.2-C FUE-0: bounded, in-memory synthetic device pairing policy.

NOT a durable device authority, HTTP endpoint, real kiosk enrollment, or clinical
product. The caller must resolve a DEVICE_MANAGE admin from its trusted local
store; never accept the admin_allowed argument from a client request. A
persistent, crash-safe identity store and physical device proof remain open.
No patient IDs, records, browser storage, secrets logging, or network calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import hmac
import secrets
from threading import RLock
import time
from typing import Callable


class DeviceIdentityError(ValueError):
    """A stable denial with no device ID, tenant, credential or secret."""


class DeviceKind(str, Enum):
    KIOSK = "KIOSK"
    WALL = "WALL"


class DeviceCapability(str, Enum):
    QR_REDEEM = "qr.redeem"
    PUBLIC_QUEUE_READ = "queue.public.read"


_CAPABILITIES = {
    DeviceKind.KIOSK: frozenset({DeviceCapability.QR_REDEEM}),
    DeviceKind.WALL: frozenset({DeviceCapability.PUBLIC_QUEUE_READ}),
}


@dataclass(frozen=True, slots=True)
class VerifiedDevice:
    """Server-side result; not a claim accepted from a remote device."""

    tenant_id: str
    device_id: str
    kind: DeviceKind
    capabilities: frozenset[DeviceCapability]


@dataclass(frozen=True, slots=True)
class _Pending:
    tenant_id: str
    device_id: str
    kind: DeviceKind
    digest: bytes
    expires_at: float


@dataclass(frozen=True, slots=True)
class _Session:
    device: VerifiedDevice
    expires_at: float


def _digest(secret: str) -> bytes:
    if not isinstance(secret, str) or not 20 <= len(secret) <= 256:
        raise DeviceIdentityError("DEVICE_AUTH_REQUIRED")
    return sha256(secret.encode("utf-8")).digest()


def _identifier(value: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or value != value.strip()
        or not value.isascii()
        or any(not (char.isalnum() or char in "_-.") for char in value)
    ):
        raise DeviceIdentityError("DEVICE_SCOPE_INVALID")
    return value


class DevicePairingLab:
    """Atomic synthetic issuer/redeemer with one-use tickets and revocation.

    FUE-0 only. Every credential is held as a digest; bearer secrets are
    returned one time and deliberately never included in exception text.
    No permanence or cross-process coordination is implied.
    """

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._lock = RLock()
        self._pending: dict[tuple[str, str], _Pending] = {}
        self._sessions: dict[bytes, _Session] = {}

    def _now(self) -> float:
        value = self._clock()
        if not isinstance(value, (int, float)) or not 0 <= value < 10**15:
            raise DeviceIdentityError("DEVICE_CLOCK_INVALID")
        return float(value)

    def _invalidate(self, tenant: str, device: str) -> None:
        self._pending.pop((tenant, device), None)
        for digest, session in tuple(self._sessions.items()):
            if session.device.tenant_id == tenant and session.device.device_id == device:
                del self._sessions[digest]

    def issue(
        self, *, tenant_id: str, device_id: str, kind: DeviceKind,
        admin_allowed: bool, ttl_seconds: int = 900,
    ) -> str:
        if admin_allowed is not True:
            raise DeviceIdentityError("DEVICE_MANAGE_FORBIDDEN")
        tenant, device = _identifier(tenant_id), _identifier(device_id)
        if not isinstance(kind, DeviceKind):
            raise DeviceIdentityError("DEVICE_KIND_INVALID")
        if type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 1800:
            raise DeviceIdentityError("DEVICE_TTL_INVALID")
        with self._lock:
            expiry = self._now() + ttl_seconds
            secret = secrets.token_urlsafe(32)
            self._invalidate(tenant, device)  # Re-pair revokes old sessions.
            self._pending[(tenant, device)] = _Pending(
                tenant, device, kind, _digest(secret), expiry,
            )
            return secret

    def redeem(self, *, tenant_id: str, device_id: str, ticket: str) -> str:
        tenant, device = _identifier(tenant_id), _identifier(device_id)
        fingerprint = _digest(ticket)
        with self._lock:
            pending = self._pending.get((tenant, device))
            if pending is None or not hmac.compare_digest(fingerprint, pending.digest):
                raise DeviceIdentityError("PAIRING_REJECTED")
            if self._now() >= pending.expires_at:
                self._pending.pop((tenant, device), None)
                raise DeviceIdentityError("PAIRING_REJECTED")
            del self._pending[(tenant, device)]  # One-time redemption.
            bearer = secrets.token_urlsafe(32)
            principal = VerifiedDevice(
                tenant, device, pending.kind, _CAPABILITIES[pending.kind],
            )
            self._sessions[_digest(bearer)] = _Session(
                principal, self._now() + 3600,
            )
            return bearer

    def require(
        self, bearer: str, *, tenant_id: str, capability: DeviceCapability,
    ) -> VerifiedDevice:
        tenant = _identifier(tenant_id)
        fingerprint = _digest(bearer)
        if not isinstance(capability, DeviceCapability):
            raise DeviceIdentityError("DEVICE_CAPABILITY_DENIED")
        with self._lock:
            session = self._sessions.get(fingerprint)
            if (
                session is None
                or self._now() >= session.expires_at
                or session.device.tenant_id != tenant
                or capability not in session.device.capabilities
            ):
                raise DeviceIdentityError("DEVICE_CAPABILITY_DENIED")
            return session.device

    def revoke(self, *, tenant_id: str, device_id: str, admin_allowed: bool) -> None:
        if admin_allowed is not True:
            raise DeviceIdentityError("DEVICE_MANAGE_FORBIDDEN")
        tenant, device = _identifier(tenant_id), _identifier(device_id)
        with self._lock:
            self._invalidate(tenant, device)
