"""LOT08.3-B synthetic LAB only: bounded, tenant-scoped closed-visit retention.

The approved G3 contract sets visit/external-reference retention at 30 days
after closure and minimized event audit retention at 12 months. This helper
deletes only closed synthetic LAB visit rows (FK-cascaded references), leaving
the append-only event ledger intact. It must NEVER be wired into a real
cabinet, scheduled task, API, or installer. Real maintenance requires separate
legal, migration, backup, restore, audit and installation gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sqlite3
import tempfile
from uuid import uuid4


# Distinct SQLite header marker written ONLY by explicit LAB fixture setup.
# A temp filename alone is insufficient to prove the file isn't a real DB copy.
SYNTHETIC_LAB_APPLICATION_ID = 0x4C4F5438  # "LOT8"


class RetentionLabError(ValueError):
    """A fail-closed, non-sensitive synthetic maintenance refusal."""


@dataclass(frozen=True, slots=True)
class RetentionLabResult:
    eligible_visits: int
    external_references: int
    resource_bindings: int
    event_facts_preserved: int
    executed: bool


def _fault_after_first_delete() -> None:
    """Test-only crash/exception oracle; overridden in synthetic tests."""


def _verify_lab_file(path: str | Path) -> Path:
    try:
        target = Path(path).resolve(strict=True)
    except (OSError, ValueError, TypeError):
        raise RetentionLabError("SYNTHETIC_LAB_FILE_REQUIRED") from None
    root = Path(tempfile.gettempdir()).resolve()
    if (
        target.is_symlink()
        or not target.is_file()
        or not target.is_relative_to(root)
        or not target.name.startswith("lot08_3_b_lab_")
        or target.suffix != ".sqlite"
    ):
        raise RetentionLabError("SYNTHETIC_LAB_FILE_REQUIRED")
    return target


def _verify_integrity(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA application_id").fetchone()[0] != SYNTHETIC_LAB_APPLICATION_ID:
        raise RetentionLabError("SYNTHETIC_LAB_MARKER_REQUIRED")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RetentionLabError("QUEUE_FK_REQUIRED")
    objects = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' "
            "AND tbl_name='queue_event_log'"
        )
    }
    if not {"queue_event_log_no_update", "queue_event_log_no_delete"} <= objects:
        raise RetentionLabError("QUEUE_EVENT_IMMUTABILITY_REQUIRED")
    # Existing on-disk corruption cannot be masked by a successful DELETE.
    if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RetentionLabError("QUEUE_SQLITE_INTEGRITY_FAILED")
    if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise RetentionLabError("QUEUE_FK_INTEGRITY_FAILED")


def _install_lab_receipt(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS queue_retention_receipts_lab ("
        "id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, executed_utc TEXT NOT NULL,"
        "visits_removed INTEGER NOT NULL, external_refs_removed INTEGER NOT NULL,"
        "resource_links_removed INTEGER NOT NULL, "
        "CHECK(visits_removed >= 0), CHECK(external_refs_removed >= 0),"
        "CHECK(resource_links_removed >= 0))"
    )
    for action in ("UPDATE", "DELETE"):
        conn.execute(
            f"CREATE TRIGGER IF NOT EXISTS queue_retention_receipts_lab_no_{action.lower()} "
            f"BEFORE {action} ON queue_retention_receipts_lab "
            "BEGIN SELECT RAISE(ABORT, 'RETENTION_RECEIPT_IMMUTABLE'); END"
        )


def retain_closed_visits_lab(
    path: str | Path, tenant_id: str, *, now: datetime,
    execute: bool = False, limit: int = 100,
) -> RetentionLabResult:
    """Preview or atomically purge up to 100 eligible synthetic visits.

    Requires an already-created isolated SQLite file. Exactly 30 days of UTC
    elapsed time since persisted closure, with DONE/NO_SHOW/CANCELLED only.
    Existing QR references block a purge rather than orphaning a QR receipt.
    Event audit rows remain unchanged and are not subject to this purge.

    This is not a general-purpose or production database maintenance routine.
    """
    target = _verify_lab_file(path)
    if not isinstance(tenant_id, str) or re.fullmatch(r"[A-Za-z0-9:_-]{1,64}", tenant_id) is None:
        raise RetentionLabError("TENANT_SCOPE_REQUIRED")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise RetentionLabError("AWARE_UTC_CLOCK_REQUIRED")
    if type(execute) is not bool or type(limit) is not int or not 1 <= limit <= 100:
        raise RetentionLabError("MAINTENANCE_ARGUMENT_INVALID")
    now_utc = now.astimezone(timezone.utc)
    cutoff = (now_utc - timedelta(days=30)).replace(tzinfo=None)
    cutoff_text = cutoff.strftime("%Y-%m-%d %H:%M:%S.%f")

    conn = sqlite3.connect(str(target), isolation_level=None, timeout=5.0)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("BEGIN IMMEDIATE" if execute else "BEGIN")
        _verify_integrity(conn)
        if conn.execute(
            "SELECT 1 FROM queue_tenants WHERE id=?", (tenant_id,)
        ).fetchone() is None:
            raise RetentionLabError("TENANT_SCOPE_REQUIRED")

        rows = conn.execute(
            "SELECT id, held_resource_id FROM queue_visits "
            "WHERE tenant_id=? AND status IN ('DONE','NO_SHOW','CANCELLED') "
            "AND closed_at_utc IS NOT NULL AND closed_at_utc <= ? "
            "ORDER BY closed_at_utc, id LIMIT ?",
            (tenant_id, cutoff_text, limit),
        ).fetchall()
        ids = [row[0] for row in rows]
        if any(row[1] is not None for row in rows):
            raise RetentionLabError("VISIT_RESOURCE_CONFLICT")

        existing_qr = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='queue_presence_qr_lab'"
        ).fetchone()
        if existing_qr and ids:
            placeholders = ",".join("?" for _ in ids)
            count = conn.execute(
                f"SELECT count(*) FROM queue_presence_qr_lab "
                f"WHERE tenant_id=? AND visit_id IN ({placeholders})",
                (tenant_id, *ids),
            ).fetchone()[0]
            if count:
                raise RetentionLabError("QR_REFERENCES_REMAIN")

        external_refs = resource_links = 0
        for visit_id in ids:
            external_refs += conn.execute(
                "SELECT count(*) FROM queue_external_references "
                "WHERE tenant_id=? AND visit_id=?",
                (tenant_id, visit_id),
            ).fetchone()[0]
            resource_links += conn.execute(
                "SELECT count(*) FROM queue_visit_resources "
                "WHERE tenant_id=? AND visit_id=?",
                (tenant_id, visit_id),
            ).fetchone()[0]
        event_count = conn.execute(
            "SELECT count(*) FROM queue_event_log WHERE tenant_id=?",
            (tenant_id,),
        ).fetchone()[0]

        if execute:
            _install_lab_receipt(conn)
            for i, visit_id in enumerate(ids):
                removed = conn.execute(
                    "DELETE FROM queue_visits WHERE tenant_id=? AND id=? "
                    "AND status IN ('DONE','NO_SHOW','CANCELLED') "
                    "AND closed_at_utc IS NOT NULL AND closed_at_utc <= ? "
                    "AND held_resource_id IS NULL",
                    (tenant_id, visit_id, cutoff_text),
                ).rowcount
                if removed != 1:
                    raise RetentionLabError("PURGE_RACE_DENIED")
                if i == 0:
                    _fault_after_first_delete()
            if conn.execute(
                "SELECT count(*) FROM queue_event_log WHERE tenant_id=?",
                (tenant_id,),
            ).fetchone()[0] != event_count:
                raise RetentionLabError("AUDIT_FACTS_CHANGED")
            conn.execute(
                "INSERT INTO queue_retention_receipts_lab "
                "(id,tenant_id,executed_utc,visits_removed,external_refs_removed,resource_links_removed) "
                "VALUES (?,?,?,?,?,?)",
                (uuid4().hex, tenant_id, now_utc.isoformat(), len(ids),
                 external_refs, resource_links),
            )
            conn.commit()
        else:
            conn.rollback()
        return RetentionLabResult(
            eligible_visits=len(ids), external_references=external_refs,
            resource_bindings=resource_links,
            event_facts_preserved=event_count, executed=execute,
        )
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
