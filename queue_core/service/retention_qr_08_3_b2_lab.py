"""LOT08.3-B2-A G3 seven-day consumed QR receipt retention: synthetic LAB only.

Only confirmed, expired, consumed QR receipts strictly older than seven elapsed UTC days
may be deleted. This is NOT a cleanup of pending/unconsumed QR, webhooks, technical
logs, or 12-month audit records. Neither a real clinic DB nor a production task
is permitted. The queue_event_log remains append-only and untouched.
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

_SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60
# Reflect the exact 08.2-D QR schema; don't silently operate on an alien table.
_QR_COLUMNS = (
    "qr_digest", "tenant_id", "queue_id", "visit_id", "expires_epoch",
    "consumed_epoch", "consumed_device", "request_digest", "result_version",
    "result_sequence",
)


@dataclass(frozen=True, slots=True)
class QrLedgerRetentionLabResult:
    eligible_receipts: int
    event_facts_preserved: int
    executed: bool


def _after_first_delete_fault_oracle() -> None:
    """Injection point for lab-only transactional rollback tests."""


def _require_g2_qr_schema(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='queue_presence_qr_lab'"
    ).fetchone()
    if exists is None:
        raise RetentionLabError("QR_LAB_SCHEMA_REQUIRED")
    cols = tuple(
        row[1] for row in conn.execute("PRAGMA table_info(queue_presence_qr_lab)")
    )
    if cols != _QR_COLUMNS:
        raise RetentionLabError("QR_LAB_SCHEMA_MISMATCH")


def _install_immutable_qr_retention_receipt(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS queue_qr_retention_receipts_lab ("
        "id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, "
        "executed_epoch INTEGER NOT NULL, removed_count INTEGER NOT NULL "
        "CHECK(removed_count >= 0))"
    )
    for method in ("UPDATE", "DELETE"):
        conn.execute(
            "CREATE TRIGGER IF NOT EXISTS "
            f"queue_qr_retention_receipts_lab_no_{method.lower()} "
            f"BEFORE {method} ON queue_qr_retention_receipts_lab "
            "BEGIN SELECT RAISE(ABORT, 'QR_RETENTION_RECEIPT_IMMUTABLE'); END"
        )


def retain_consumed_qr_ledger_lab(
    path: str | Path,
    tenant_id: str,
    *,
    now: datetime,
    execute: bool = False,
    limit: int = 100,
) -> QrLedgerRetentionLabResult:
    """Preview or atomically purge a tenant's expired 7-day QR retry receipts.

    Keep all unconsumed codes, receipts within 7 full days, receipts claiming
    expiry in the future, and every queue event audit row. A removed receipt
    cannot be used to retry an arrival: lookup by QR digest then returns none.
    Only 08.3-B1 synthetic-marked temporary files may be opened.
    """
    target = _verify_lab_file(path)
    if not isinstance(tenant_id, str) or re.fullmatch(
        r"[A-Za-z0-9:_-]{1,64}", tenant_id,
    ) is None:
        raise RetentionLabError("TENANT_SCOPE_REQUIRED")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED")
    if type(execute) is not bool or type(limit) is not int or not 1 <= limit <= 100:
        raise RetentionLabError("MAINTENANCE_ARGUMENT_INVALID")
    now_epoch = int(now.astimezone(timezone.utc).timestamp())
    if not 0 <= now_epoch < 10**15:
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED")
    # KioskQrArrivalLab.redeem still permits an exact-boundary retry.\n    # Keep the receipt through second 604800; purge only afterwards.\n    cutoff = now_epoch - _SEVEN_DAYS_SECONDS - 1\n
    conn = sqlite3.connect(str(target), timeout=5.0, isolation_level=None)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("BEGIN IMMEDIATE" if execute else "BEGIN")
        _verify_integrity(conn)
        _require_g2_qr_schema(conn)
        if conn.execute(
            "SELECT 1 FROM queue_tenants WHERE id=?", (tenant_id,)
        ).fetchone() is None:
            raise RetentionLabError("TENANT_SCOPE_REQUIRED")
        rows = conn.execute(
            "SELECT qr_digest FROM queue_presence_qr_lab "
            "WHERE tenant_id=? AND consumed_epoch IS NOT NULL "
            "AND consumed_epoch <= ? AND expires_epoch <= ? "
            "AND request_digest IS NOT NULL "
            "AND result_version IS NOT NULL AND result_sequence IS NOT NULL "
            "ORDER BY consumed_epoch,qr_digest LIMIT ?",
            (tenant_id, cutoff, now_epoch, limit),
        ).fetchall()
        event_count = conn.execute(
            "SELECT count(*) FROM queue_event_log WHERE tenant_id=?", (tenant_id,)
        ).fetchone()[0]

        if execute and rows:
            _install_immutable_qr_retention_receipt(conn)
            for index, (qr_digest,) in enumerate(rows):
                changed = conn.execute(
                    "DELETE FROM queue_presence_qr_lab WHERE tenant_id=? "
                    "AND qr_digest=? AND consumed_epoch IS NOT NULL "
                    "AND consumed_epoch <= ? AND expires_epoch <= ?",
                    (tenant_id, qr_digest, cutoff, now_epoch),
                ).rowcount
                if changed != 1:
                    raise RetentionLabError("QR_RETENTION_RACE_DENIED")
                if index == 0:
                    _after_first_delete_fault_oracle()
            if conn.execute(
                "SELECT count(*) FROM queue_event_log WHERE tenant_id=?",
                (tenant_id,),
            ).fetchone()[0] != event_count:
                raise RetentionLabError("AUDIT_FACTS_CHANGED")
            conn.execute(
                "INSERT INTO queue_qr_retention_receipts_lab "
                "(id,tenant_id,executed_epoch,removed_count) VALUES(?,?,?,?)",
                (uuid4().hex, tenant_id, now_epoch, len(rows)),
            )
            conn.commit()
        else:
            conn.rollback()
        return QrLedgerRetentionLabResult(
            eligible_receipts=len(rows),
            event_facts_preserved=event_count,
            executed=execute,
        )
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
