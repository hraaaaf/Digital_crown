"""08.2-C: persistent synthetic device authority, separate from clinical data.

This is a LOCAL LAB component, not an activated device service. The operator
identity store and device file are distinct. Provisioning requires the local
console guard and is explicit; importing or constructing never creates tables.
Credential digests only. No HTTP, patient data, migration, or platform pairing.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import hmac
import secrets
import sqlite3
import time
from typing import Callable, Iterator

from queue_core.security.device_pairing_lab import (
    DeviceCapability, DeviceIdentityError, DeviceKind, VerifiedDevice, _identifier,
)
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import (
    Permission, QueueAuthorizer, TargetScope,
)

_CREATE = (
    """CREATE TABLE devices (
        tenant_id TEXT NOT NULL, device_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('KIOSK','WALL')),
        generation INTEGER NOT NULL CHECK(generation > 0),
        revoked INTEGER NOT NULL CHECK(revoked IN (0,1)),
        pairing_digest TEXT, pairing_expires INTEGER,
        PRIMARY KEY(tenant_id,device_id),
        CHECK((pairing_digest IS NULL) = (pairing_expires IS NULL))
    )""",
    """CREATE TABLE device_sessions (
        digest TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL, device_id TEXT NOT NULL,
        generation INTEGER NOT NULL,
        expires_epoch INTEGER NOT NULL,
        FOREIGN KEY(tenant_id,device_id) REFERENCES devices(tenant_id,device_id)
            ON DELETE CASCADE
    )""",
    "CREATE INDEX device_sessions_device_idx ON device_sessions(tenant_id,device_id)",
)


def _fingerprint(token: str, purpose: str) -> str:
    if not isinstance(token, str) or not 20 <= len(token) <= 256:
        raise DeviceIdentityError("DEVICE_AUTH_REQUIRED")
    return sha256((purpose + "\x00" + token).encode("utf-8")).hexdigest()


class DurableDeviceStoreLab:
    """Explicitly initialized, crash-persistent SQLite FUE-I candidate.

    Admin operations lock identity DB BEFORE device DB and use live
    DEVICE_MANAGE permissions; account revocation cannot interleave an
    already-authorized mutation. Redemption/reads are scoped to the persisted
    tenant/device/session and fail closed on DB access errors.
    """

    def __init__(
        self, operators: LocalOperatorStore, db_path: str | Path, *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not isinstance(operators, LocalOperatorStore):
            raise TypeError("OPERATOR_STORE_REQUIRED")
        self.operators = operators
        self.path = Path(db_path).resolve()
        if self.path == operators.auth.path.resolve():
            raise DeviceIdentityError("DEVICE_DB_MUST_BE_SEPARATE")
        self.clock = clock

    def _now(self) -> int:
        value = self.clock()
        if type(value) not in (int, float) or not 0 <= value < 10**15:
            raise DeviceIdentityError("DEVICE_CLOCK_INVALID")
        return int(value)

    @contextmanager
    def _connect(self, *, creating: bool = False) -> Iterator[sqlite3.Connection]:
        if not creating and not self.path.is_file():
            raise DeviceIdentityError("DEVICE_STORE_NOT_INITIALIZED")
        try:
            connection = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("PRAGMA secure_delete=ON")
            connection.execute("PRAGMA synchronous=FULL")
            yield connection
        except BaseException:
            if "connection" in locals():
                connection.rollback()
            raise
        finally:
            if "connection" in locals():
                connection.close()

    def initialize_lab(self) -> None:
        """Only explicit LAB provisioning with existing local-console guard.

        Never a production migration; refuses an existing file, including a
        previously provisioned store. Caller must protect the directory via
        tested filesystem ACLs before any non-synthetic use.
        """
        self.operators.auth._guard()
        if not self.operators.auth.path.is_file() or not self.path.parent.is_dir():
            raise DeviceIdentityError("DEVICE_STORE_PRECONDITION_FAILED")
        if self.path.exists():
            raise DeviceIdentityError("DEVICE_STORE_ALREADY_EXISTS")
        with self._connect(creating=True) as c:
            c.execute("BEGIN IMMEDIATE")
            for ddl in _CREATE:
                c.execute(ddl)
            c.commit()

    @contextmanager
    def _admin(self, admin_token: str, tenant_id: str) -> Iterator[sqlite3.Connection]:
        if not isinstance(admin_token, str) or not 20 <= len(admin_token) <= 256:
            raise DeviceIdentityError("DEVICE_MANAGE_FORBIDDEN")
        tenant = _identifier(tenant_id)
        # The lock order is authoritative and shared with AuthorizedLocalQueue.
        with self.operators.auth._connect() as identity:
            identity.execute("BEGIN IMMEDIATE")
            try:
                principal = LocalOperatorStore._principal(
                    identity, admin_token, self.operators._now(),
                )
                QueueAuthorizer(lambda _: principal).require(
                    admin_token, Permission.DEVICE_MANAGE, TargetScope(tenant_id=tenant),
                )
                with self._connect() as device:
                    device.execute("BEGIN IMMEDIATE")
                    try:
                        yield device
                        device.commit()
                    except BaseException:
                        device.rollback()
                        raise
                identity.commit()
            except BaseException:
                identity.rollback()
                raise

    def issue(
        self, admin_token: str, *, tenant_id: str,
        device_id: str, kind: DeviceKind, ttl_seconds: int = 900,
    ) -> str:
        tenant, device_id = _identifier(tenant_id), _identifier(device_id)
        if not isinstance(kind, DeviceKind):
            raise DeviceIdentityError("DEVICE_KIND_INVALID")
        if type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 1800:
            raise DeviceIdentityError("DEVICE_TTL_INVALID")
        code = secrets.token_urlsafe(32)
        fingerprint = _fingerprint(code, "pair-v1")
        with self._admin(admin_token, tenant) as c:
            current = c.execute(
                "SELECT generation FROM devices WHERE tenant_id=? AND device_id=?",
                (tenant, device_id),
            ).fetchone()
            if current:
                generation = current["generation"] + 1
                c.execute(
                    """UPDATE devices SET kind=?, generation=?, revoked=0,
                       pairing_digest=?,pairing_expires=?
                       WHERE tenant_id=? AND device_id=?""",
                    (kind.value, generation, fingerprint, self._now() + ttl_seconds,
                     tenant, device_id),
                )
                c.execute(
                    "DELETE FROM device_sessions WHERE tenant_id=? AND device_id=?",
                    (tenant, device_id),
                )
            else:
                c.execute(
                    """INSERT INTO devices
                       (tenant_id,device_id,kind,generation,revoked,
                        pairing_digest,pairing_expires) VALUES(?,?,?,1,0,?,?)""",
                    (tenant, device_id, kind.value, fingerprint,
                     self._now() + ttl_seconds),
                )
        return code

    def redeem(self, *, tenant_id: str, device_id: str, ticket: str) -> str:
        tenant, device_id = _identifier(tenant_id), _identifier(device_id)
        digest = _fingerprint(ticket, "pair-v1")
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute(
                "SELECT * FROM devices WHERE tenant_id=? AND device_id=?",
                (tenant, device_id),
            ).fetchone()
            if (not row or row["revoked"] or row["pairing_digest"] is None
                or not hmac.compare_digest(row["pairing_digest"], digest)
                or self._now() >= row["pairing_expires"]):
                raise DeviceIdentityError("PAIRING_REJECTED")
            bearer = secrets.token_urlsafe(32)
            c.execute(
                """UPDATE devices SET pairing_digest=NULL,pairing_expires=NULL
                   WHERE tenant_id=? AND device_id=?""",
                (tenant, device_id),
            )
            c.execute(
                """INSERT INTO device_sessions
                   (digest,tenant_id,device_id,generation,expires_epoch)
                   VALUES(?,?,?,?,?)""",
                (_fingerprint(bearer, "session-v1"), tenant, device_id,
                 row["generation"], self._now() + 3600),
            )
            c.commit()
        return bearer

    def require(
        self, bearer: str, *, tenant_id: str, capability: DeviceCapability,
    ) -> VerifiedDevice:
        tenant = _identifier(tenant_id)
        digest = _fingerprint(bearer, "session-v1")
        if not isinstance(capability, DeviceCapability):
            raise DeviceIdentityError("DEVICE_CAPABILITY_DENIED")
        with self._connect() as c:
            row = c.execute(
                """SELECT d.tenant_id,d.device_id,d.kind,d.revoked,
                          d.generation,s.generation AS session_generation,
                          s.expires_epoch
                   FROM device_sessions s JOIN devices d
                     ON d.tenant_id=s.tenant_id AND d.device_id=s.device_id
                   WHERE s.digest=? AND s.tenant_id=?""",
                (digest, tenant),
            ).fetchone()
        if (not row or row["revoked"]
            or row["generation"] != row["session_generation"]
            or self._now() >= row["expires_epoch"]):
            raise DeviceIdentityError("DEVICE_CAPABILITY_DENIED")
        kind = DeviceKind(row["kind"])
        capabilities = (
            frozenset({DeviceCapability.QR_REDEEM}) if kind is DeviceKind.KIOSK
            else frozenset({DeviceCapability.PUBLIC_QUEUE_READ})
        )
        if capability not in capabilities:
            raise DeviceIdentityError("DEVICE_CAPABILITY_DENIED")
        return VerifiedDevice(tenant, row["device_id"], kind, capabilities)

    def revoke(self, admin_token: str, *, tenant_id: str, device_id: str) -> None:
        tenant, device_id = _identifier(tenant_id), _identifier(device_id)
        with self._admin(admin_token, tenant) as c:
            found = c.execute(
                """UPDATE devices SET revoked=1, generation=generation+1,
                   pairing_digest=NULL,pairing_expires=NULL
                   WHERE tenant_id=? AND device_id=?""",
                (tenant, device_id),
            )
            if found.rowcount != 1:
                raise DeviceIdentityError("DEVICE_SCOPE_INVALID")
            c.execute(
                "DELETE FROM device_sessions WHERE tenant_id=? AND device_id=?",
                (tenant, device_id),
            )
