"""LOT08.3-B3: expire NEVER-CONSUMED synthetic kiosk QR records, G3 LAB ONLY.

The kiosk already denies redemption at now >= expires_epoch. This bounded,
tenant-scoped maintenance removes only unconsumed records at that exact
boundary; consumed receipts keep their independent 7-day retry policy.
No automatic scheduler, real patient DB, clinic installable or physical proof.
An encrypted backup predating deletion MUST fail closed at restore, never
re-introduce the retired QR under the current trusted clock.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from queue_core.service.retention_lab_08_3_b import (
    RetentionLabError, _verify_integrity, _verify_lab_file,
)
from queue_core.service.retention_qr_08_3_b2_lab import _require_g2_qr_schema

_RECEIPT_TABLE = "queue_qr_expired_unconsumed_receipts_lab"
_RECEIPT_COLUMNS = ("id", "tenant_id", "executed_epoch", "removed_count")


@dataclass(frozen=True, slots=True)
class ExpiredUnconsumedQrLabResult:
    eligible_codes: int
    event_facts_preserved: int
    executed: bool


def _after_first_unconsumed_delete_lab() -> None:
    """Fault injection. Roll back every deletion and its aggregate receipt."""


def _ensure_retention_receipt_lab(conn: sqlite3.Connection) -> None:
    existing = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_RECEIPT_TABLE,),
    ).fetchone()
    if existing:
        cols = tuple(row[1] for row in conn.execute(
            f"PRAGMA table_info({_RECEIPT_TABLE})"
        ))
        if cols != _RECEIPT_COLUMNS:
            raise RetentionLabError("QR_UNUSED_RECEIPT_SCHEMA_MISMATCH")
        guards = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
            (_RECEIPT_TABLE,),
        )}
        if not {
            "queue_qr_expired_unconsumed_no_update",
            "queue_qr_expired_unconsumed_no_delete",
        } <= guards:
            raise RetentionLabError("QR_UNUSED_RECEIPT_GUARD_REQUIRED")
        return
    conn.execute(
        f"CREATE TABLE {_RECEIPT_TABLE} ("
        "id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, "
        "executed_epoch INTEGER NOT NULL, removed_count INTEGER NOT NULL "
        "CHECK(removed_count > 0))"
    )
    for action in ("UPDATE", "DELETE"):
        conn.execute(
            f"CREATE TRIGGER queue_qr_expired_unconsumed_no_{action.lower()} "
            f"BEFORE {action} ON {_RECEIPT_TABLE} "
            "BEGIN SELECT RAISE(ABORT, 'QR_UNUSED_RECEIPT_IMMUTABLE'); END"
        )


def retain_expired_unconsumed_qr_lab(
    path: str | Path, tenant_id: str, *, now: datetime,
    execute: bool = False, limit: int = 100,
) -> ExpiredUnconsumedQrLabResult:
    """Preview/purge up to 100 expired, unconsumed QR codes in one SQLite tx.

    Exact kiosk threshold: current UTC second >= expires_epoch. No consumed
    receipt is touched (even when its expiry has passed); its 7-day retry
    retention belongs exclusively to B2-A. No audit event or visit is deleted.
    If a fault happens after deleting the first row, all changes roll back.
    """
    target = _verify_lab_file(path)
    if (type(tenant_id) is not str
        or re.fullmatch(r"[A-Za-z0-9:_-]{1,64}", tenant_id) is None):
        raise RetentionLabError("TENANT_SCOPE_REQUIRED")
    if (not isinstance(now, datetime) or now.tzinfo is None
        or now.utcoffset() is None):
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED")
    try:
        epoch = int(now.astimezone(timezone.utc).timestamp())
    except (ValueError, OverflowError, OSError):
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED") from None
    if not 0 <= epoch < 10**15:
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED")
    if type(execute) is not bool or type(limit) is not int or not 1 <= limit <= 100:
        raise RetentionLabError("MAINTENANCE_ARGUMENT_INVALID")

    conn = sqlite3.connect(str(target), timeout=5.0, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("BEGIN IMMEDIATE" if execute else "BEGIN")
        _verify_integrity(conn)
        _require_g2_qr_schema(conn)
        if conn.execute(
            "SELECT 1 FROM queue_tenants WHERE id=?", (tenant_id,),
        ).fetchone() is None:
            raise RetentionLabError("TENANT_SCOPE_REQUIRED")
        if conn.execute(
            "SELECT 1 FROM queue_presence_qr_lab "
            "WHERE tenant_id=? AND consumed_epoch IS NULL "
            "AND (typeof(expires_epoch)!='integer' OR expires_epoch < 0) LIMIT 1",
            (tenant_id,),
        ).fetchone():
            raise RetentionLabError("QR_UNUSED_EXPIRY_INVALID")
        eligible = conn.execute(
            "SELECT qr_digest FROM queue_presence_qr_lab "
            "WHERE tenant_id=? AND consumed_epoch IS NULL "
            "AND expires_epoch <= ? "
            "ORDER BY expires_epoch,qr_digest LIMIT ?",
            (tenant_id, epoch, limit),
        ).fetchall()
        audit_before = conn.execute(
            "SELECT count(*) FROM queue_event_log"
        ).fetchone()[0]
        if execute and eligible:
            _ensure_retention_receipt_lab(conn)
            for idx, (digest,) in enumerate(eligible):
                deleted = conn.execute(
                    "DELETE FROM queue_presence_qr_lab "
                    "WHERE qr_digest=? AND tenant_id=? "
                    "AND consumed_epoch IS NULL AND expires_epoch <= ?",
                    (digest, tenant_id, epoch),
                ).rowcount
                if deleted != 1:
                    raise RetentionLabError("QR_UNUSED_RACE_DENIED")
                if idx == 0:
                    _after_first_unconsumed_delete_lab()
            if conn.execute(
                "SELECT count(*) FROM queue_event_log"
            ).fetchone()[0] != audit_before:
                raise RetentionLabError("AUDIT_FACTS_CHANGED")
            conn.execute(
                f"INSERT INTO {_RECEIPT_TABLE} "
                "(id,tenant_id,executed_epoch,removed_count) VALUES(?,?,?,?)",
                (uuid4().hex, tenant_id, epoch, len(eligible)),
            )
            conn.commit()
        else:
            conn.rollback()
        return ExpiredUnconsumedQrLabResult(
            eligible_codes=len(eligible),
            event_facts_preserved=audit_before,
            executed=execute,
        )
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
