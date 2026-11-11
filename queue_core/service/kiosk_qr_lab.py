"""LOT08.2-D synthetic-only QR arrival junction: no HTTP, patient data or production schema.

Coordinates existing auth -> device -> Queue locks (one acquisition each).
All MUTATIONS for an arrival happen in the existing, isolated Queue SQLite
transaction: QR spent + idempotency receipt + visit CAS + two event facts.
This module MUST NOT be imported into a clinical production route before
separate migration, Windows ACL/restore and FUE approval.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
import secrets
import time
from typing import Callable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from queue_core.domain import (
    ActorKind, CheckInMethod, QueueDomainError, VisitKind, VisitStatus,
    as_utc, check_in,
)
from queue_core.persistence.models import QueueVisitRecord
from queue_core.security.device_pairing_lab import (
    DeviceCapability, DeviceKind,
)
from queue_core.security.device_store_lab import DurableDeviceStoreLab
from queue_core.security.rbac import Permission
from queue_core.service.atomic_transition import validate_atomic_transition
from queue_core.service.authorized_queue import (
    AuthorizedLocalQueue, QueueVisitView,
)


_SCHEMA = """
CREATE TABLE queue_presence_qr_lab (
    qr_digest TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    queue_id TEXT NOT NULL,
    visit_id TEXT NOT NULL,
    expires_epoch INTEGER NOT NULL,
    consumed_epoch INTEGER,
    consumed_device TEXT,
    request_digest TEXT,
    result_version INTEGER,
    result_sequence INTEGER,
    CHECK(
        (consumed_epoch IS NULL AND consumed_device IS NULL
         AND request_digest IS NULL AND result_version IS NULL
         AND result_sequence IS NULL)
        OR
        (consumed_epoch IS NOT NULL AND consumed_device IS NOT NULL
         AND request_digest IS NOT NULL AND result_version IS NOT NULL
         AND result_sequence IS NOT NULL)
    )
)
"""


def _secret_digest(value: str, purpose: str) -> str:
    if not isinstance(value, str) or not 20 <= len(value) <= 256:
        raise QueueDomainError("QR_REJECTED")
    return sha256((purpose + "\x00" + value).encode("utf-8")).hexdigest()


def _request_digest(request_key: str, actor_ref: str) -> str:
    if not isinstance(request_key, str) or not re.fullmatch(
        r"[A-Za-z0-9:_-]{16,128}", request_key,
    ):
        raise QueueDomainError("QR_REQUEST_INVALID")
    return sha256(("idempotency-v1\x00" + actor_ref + "\x00" + request_key).encode()).hexdigest()


class KioskQrArrivalLab:
    """Bounded experimental bridge. No Queue production migration or API."""

    def __init__(
        self, queue: AuthorizedLocalQueue, devices: DurableDeviceStoreLab, *,
        epoch_clock: Callable[[], float] = time.time,
        utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not isinstance(queue, AuthorizedLocalQueue) or not isinstance(
            devices, DurableDeviceStoreLab
        ):
            raise TypeError("LAB_QUEUE_AND_DEVICE_STORES_REQUIRED")
        if devices.operators is not queue._operators:
            raise ValueError("AUTHORITY_INSTANCE_MISMATCH")
        auth_path = devices.operators.auth.path.resolve()
        device_path = devices.path.resolve()
        queue_path = Path(queue._engine.url.database).resolve()
        # Deliberately refuse normal clinical filenames even if imported.
        if (
            not all(p.name.endswith("-synthetic.sqlite") for p in (
                auth_path, device_path, queue_path,
            ))
            or len({auth_path, device_path, queue_path}) != 3
        ):
            raise ValueError("LAB_SYNTHETIC_FILES_ONLY")
        self.queue, self.devices = queue, devices
        self._epoch_clock, self._utc_clock = epoch_clock, utc_clock

    def _epoch(self) -> int:
        now = self._epoch_clock()
        if type(now) not in (int, float) or not 0 <= now < 10**15:
            raise QueueDomainError("QR_CLOCK_INVALID")
        return int(now)

    def initialize_lab(self) -> None:
        """Explicit temporary Queue-only schema in a synthetic SQLite file."""
        self.queue._operators.auth._guard()
        with self.queue._engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                current = connection.exec_driver_sql(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='queue_presence_qr_lab'"
                ).first()
                queue_exists = connection.exec_driver_sql(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='queue_visits'"
                ).first()
                if current or not queue_exists:
                    raise QueueDomainError("QR_LAB_SCHEMA_PRECONDITION")
                connection.exec_driver_sql(_SCHEMA)
                connection.exec_driver_sql(
                    "CREATE INDEX queue_presence_scope_idx "
                    "ON queue_presence_qr_lab(tenant_id,queue_id,visit_id)"
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def issue(
        self, human_session: str, visit_id: str, *, ttl_seconds: int = 900,
    ) -> str:
        """One-time QR for preexisting appointment; live human QR_ISSUE rights."""
        if type(ttl_seconds) is not int or not 300 <= ttl_seconds <= 1800:
            raise QueueDomainError("QR_TTL_INVALID")
        qr = secrets.token_urlsafe(32)
        with self.queue._transaction(human_session) as (db, principal, authorizer):
            visit = self.queue._visit(db, principal, visit_id)
            authorizer.require(
                human_session, Permission.QR_ISSUE,
                self.queue._target(visit, None),
            )
            if (
                visit.visit_kind != VisitKind.APPOINTMENT.value
                or visit.status not in (VisitStatus.PLANNED.value, VisitStatus.EN_ROUTE.value)
            ):
                raise QueueDomainError("QR_REJECTED")
            # Re-issue atomically invalidates only the same visit's older code.
            db.execute(text(
                "DELETE FROM queue_presence_qr_lab "
                "WHERE tenant_id=:tenant AND visit_id=:visit"
            ), {"tenant":visit.tenant_id, "visit":visit.id})
            db.execute(text(
                "INSERT INTO queue_presence_qr_lab "
                "(qr_digest,tenant_id,queue_id,visit_id,expires_epoch) "
                "VALUES(:digest,:tenant,:queue,:visit,:expiry)"
            ), {
                "digest":_secret_digest(qr, "presence-qr-v1"),
                "tenant":visit.tenant_id,
                "queue":visit.queue_id,
                "visit":visit.id,
                "expiry":self._epoch()+ttl_seconds,
            })
        return qr

    def redeem(
        self, device_bearer: str, qr: str, *, tenant_id: str, request_key: str,
    ) -> QueueVisitView:
        """Redeem only after auth→device→Queue lock, without lock re-entry."""
        qr_digest = _secret_digest(qr, "presence-qr-v1")
        # Device store scopes the tenant against the persisted bearer.
        with self.devices._guarded_device_session(
            device_bearer, tenant_id=tenant_id,
            capability=DeviceCapability.QR_REDEEM,
        ) as device:
            if device.kind is not DeviceKind.KIOSK:
                raise QueueDomainError("QR_REJECTED")
            # Short opaque audit actor, not a patient or physical identifier.
            actor = "dev_" + sha256(
                (device.tenant_id + "\x00" + device.device_id).encode()
            ).hexdigest()[:32]
            retry_digest = _request_digest(request_key, actor)
            with self.queue._engine.connect() as connection:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.exec_driver_sql("PRAGMA busy_timeout=5000")
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                try:
                    with Session(bind=connection, expire_on_commit=False) as db:
                        record = db.execute(text(
                            "SELECT * FROM queue_presence_qr_lab "
                            "WHERE qr_digest=:digest AND tenant_id=:tenant"
                        ), {"digest":qr_digest, "tenant":device.tenant_id}).mappings().first()
                        if record is None:
                            raise QueueDomainError("QR_REJECTED")
                        if record["consumed_epoch"] is not None:
                            if (
                                record["consumed_device"] != actor
                                or record["request_digest"] != retry_digest
                                or self._epoch() > record["consumed_epoch"] + 7 * 86400
                            ):
                                raise QueueDomainError("QR_REJECTED")
                            view = QueueVisitView(
                                record["visit_id"], record["queue_id"],
                                VisitStatus.WAITING.value, record["result_version"],
                                record["result_sequence"],
                            )
                        else:
                            if self._epoch() >= record["expires_epoch"]:
                                raise QueueDomainError("QR_REJECTED")
                            row = db.scalar(select(QueueVisitRecord).where(
                                QueueVisitRecord.id == record["visit_id"],
                                QueueVisitRecord.tenant_id == device.tenant_id,
                                QueueVisitRecord.queue_id == record["queue_id"],
                            ))
                            if (
                                row is None
                                or row.visit_kind != VisitKind.APPOINTMENT.value
                                or row.status not in (
                                    VisitStatus.PLANNED.value, VisitStatus.EN_ROUTE.value
                                )
                            ):
                                raise QueueDomainError("QR_REJECTED")
                            self.queue._queue(db, device.tenant_id, row.queue_id)
                            before = self.queue._as_domain(db, row)
                            seq = db.scalar(select(func.max(
                                QueueVisitRecord.queue_sequence
                            )).where(
                                QueueVisitRecord.tenant_id == device.tenant_id,
                                QueueVisitRecord.queue_id == row.queue_id,
                            )) or 0
                            now = as_utc(self._utc_clock())
                            plan = check_in(
                                before, at=now, actor_ref=actor,
                                method=CheckInMethod.KIOSK_QR,
                                actor_kind=ActorKind.DEVICE,
                                queue_sequence=max(seq, before.queue_sequence or 0) + 1,
                                authorized=True,
                            )
                            validate_atomic_transition(before, plan)
                            self.queue._commit_plan(db, row, plan, now)
                            changed = db.execute(text(
                                "UPDATE queue_presence_qr_lab SET "
                                "consumed_epoch=:epoch,consumed_device=:device,"
                                "request_digest=:req,result_version=:version,"
                                "result_sequence=:sequence WHERE qr_digest=:digest "
                                "AND tenant_id=:tenant AND consumed_epoch IS NULL"
                            ), {
                                "epoch":self._epoch(), "device":actor, "req":retry_digest,
                                "version":plan.visit.version,
                                "sequence":plan.visit.queue_sequence,
                                "digest":qr_digest, "tenant":device.tenant_id,
                            })
                            if changed.rowcount != 1:
                                raise QueueDomainError("QR_REJECTED")
                            view = QueueVisitView(
                                row.id, row.queue_id, plan.visit.status.value,
                                plan.visit.version, plan.visit.queue_sequence,
                            )
                        db.flush()
                    connection.commit()
                    return view
                except BaseException:
                    connection.rollback()
                    raise
