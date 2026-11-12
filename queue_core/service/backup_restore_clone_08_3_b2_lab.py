"""LOT08.3-B2-B: sealed synthetic Queue snapshot and fail-closed restore CLONE.

This experiment is deliberately unreachable from the application, HTTP, CLI,
scheduler and installer. It can only read explicitly marked temp LAB Queue SQLite,
and it can only create a NEW clone in the temp directory. No live restore,
backup retention scheduler, real encryption key store or RPO/RTO certification.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import os
import sqlite3
import struct
import tempfile
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from queue_core.service.retention_lab_08_3_b import (
    RetentionLabError, _verify_integrity, _verify_lab_file,
)
from queue_core.service.retention_qr_08_3_b2_lab import _require_g2_qr_schema

_MAGIC = b"LOT08_3_B2B_SEALED_QUEUE_V1\x00"
_MAX_SQLITE_BYTES = 4 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
_QR_TTL = 7 * 86400
_ALLOWED_TABLES = frozenset({
    "queue_tenants", "queue_lines", "queue_resources", "queue_visits",
    "queue_visit_resources", "queue_external_references", "queue_event_log",
    "queue_presence_qr_lab", "queue_retention_receipts_lab",
    "queue_qr_retention_receipts_lab",
    "queue_qr_expired_unconsumed_receipts_lab",
})


class RestoreCloneLabError(RetentionLabError):
    """Non-sensitive refusal for a synthetic-only restore operation."""


def _now_epoch(now: datetime) -> int:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise RestoreCloneLabError("AWARE_UTC_CLOCK_REQUIRED")
    try:
        value = int(now.astimezone(timezone.utc).timestamp())
    except (OverflowError, OSError, ValueError):
        raise RestoreCloneLabError("AWARE_UTC_CLOCK_REQUIRED") from None
    if not 0 <= value < 10**15:
        raise RestoreCloneLabError("AWARE_UTC_CLOCK_REQUIRED")
    return value


def _fernet(key: bytes) -> Fernet:
    if not isinstance(key, bytes):
        raise RestoreCloneLabError("SEPARATE_LAB_KEY_REQUIRED")
    try:
        return Fernet(key)
    except (ValueError, TypeError):
        raise RestoreCloneLabError("SEPARATE_LAB_KEY_REQUIRED") from None


def _lab_destination(value: str | Path, *, kind: str, exists: bool) -> Path:
    """Only purpose-named files below system temp, no symlinks or overwrite."""
    try:
        original = Path(value)
        root = Path(tempfile.gettempdir()).resolve()
        target = original.resolve(strict=exists)
    except (OSError, ValueError, TypeError):
        raise RestoreCloneLabError("LAB_DESTINATION_REQUIRED") from None
    prefix, suffix = (
        ("lot08_3_b_lab_backup_", ".fernet") if kind == "archive"
        else ("lot08_3_b_lab_restored_", ".sqlite")
    )
    if (original.is_symlink() or not target.is_relative_to(root)
        or not target.name.startswith(prefix) or target.suffix != suffix
        or target.parent == root or not target.parent.is_dir()
        or target.is_file() != exists):
        raise RestoreCloneLabError("LAB_DESTINATION_REQUIRED")
    if exists and not target.is_file():
        raise RestoreCloneLabError("LAB_DESTINATION_REQUIRED")
    return target


def _verify_queue_scope(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        _verify_integrity(conn)
    except RetentionLabError as exc:
        raise RestoreCloneLabError(str(exc)) from None
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }
    if (not {"queue_tenants", "queue_visits", "queue_event_log"} <= tables
        or not tables <= _ALLOWED_TABLES):
        raise RestoreCloneLabError("QUEUE_LAB_SCHEMA_REQUIRED")
    if "queue_presence_qr_lab" in tables:
        try:
            _require_g2_qr_schema(conn)
        except RetentionLabError as exc:
            raise RestoreCloneLabError(str(exc)) from None
    if conn.execute("SELECT count(*) FROM queue_tenants").fetchone()[0] < 1:
        raise RestoreCloneLabError("QUEUE_LAB_TENANT_REQUIRED")


def _disallow_overdue_personal_data(conn: sqlite3.Connection, now_epoch: int) -> None:
    """No clone publication while any tenant contains purge-eligible G3 records.

    The guard intentionally REJECTS stale archives; it does not silently
    perform purge/migration or rewrite append-only audit. No scope/tenant bypass.
    """
    utc_now = datetime.fromtimestamp(now_epoch, timezone.utc)
    cutoff = (utc_now - timedelta(days=30)).replace(tzinfo=None)
    cutoff_sql = cutoff.strftime("%Y-%m-%d %H:%M:%S.%f")
    if conn.execute(
        "SELECT 1 FROM queue_visits WHERE status IN ('DONE','CANCELLED','NO_SHOW') "
        "AND closed_at_utc IS NOT NULL AND closed_at_utc <= ? LIMIT 1",
        (cutoff_sql,),
    ).fetchone():
        raise RestoreCloneLabError("RESTORE_OVERDUE_VISIT_DENIED")
    has_qr = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='queue_presence_qr_lab'"
    ).fetchone()
    if has_qr and conn.execute(
        "SELECT 1 FROM queue_presence_qr_lab WHERE consumed_epoch IS NOT NULL "
        "AND consumed_epoch < ? AND expires_epoch <= ? LIMIT 1",
        (now_epoch - _QR_TTL, now_epoch),
    ).fetchone():
        raise RestoreCloneLabError("RESTORE_OVERDUE_QR_DENIED")
    # B3: even a never-consumed QR is not restorable once expired. Reject the
    # WHOLE stale clone rather than silently deleting it during recovery.
    # Kiosk redemption already denies at now >= expires_epoch.
    if has_qr and conn.execute(
        "SELECT 1 FROM queue_presence_qr_lab WHERE consumed_epoch IS NULL "
        "AND (typeof(expires_epoch)!='integer' OR expires_epoch < 0 "
        "OR expires_epoch <= ?) LIMIT 1",
        (now_epoch,),
    ).fetchone():
        raise RestoreCloneLabError("RESTORE_EXPIRED_UNCONSUMED_QR_DENIED")


def _before_clone_publish() -> None:
    """Synthetic fault-injection oracle."""


def seal_queue_snapshot_lab(
    source: str | Path, archive: str | Path, *, key: bytes, now: datetime,
) -> str:
    """Encrypted SQLite online snapshot, ciphertext-only archive, no overwrite.

    Returns authenticated plaintext image SHA-256 for test comparison only;
    this checksum is not a real external trust anchor or key-management scheme.
    """
    try:
        source_path = _verify_lab_file(source)
    except RetentionLabError as exc:
        raise RestoreCloneLabError(str(exc)) from None
    target = _lab_destination(archive, kind="archive", exists=False)
    cipher = _fernet(key)
    stamp = _now_epoch(now)
    if source_path == target:
        raise RestoreCloneLabError("LAB_DESTINATION_REQUIRED")

    original = sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True)
    memory = sqlite3.connect(":memory:")
    try:
        _verify_queue_scope(original)
        original.backup(memory)
        # A committed-WAL source can leave page bytes 18/19 in WAL mode even
        # after a correct SQLite backup into memory. VACUUM on the disposable
        # in-memory copy yields a self-contained rollback-mode image without
        # editing SQLite headers by hand or touching the source database.
        memory.execute("VACUUM")
        _verify_queue_scope(memory)
        image = memory.serialize()
        if not image.startswith(b"SQLite format 3\x00") or not 0 < len(image) <= _MAX_SQLITE_BYTES:
            raise RestoreCloneLabError("QUEUE_SNAPSHOT_SIZE_OR_HEADER_INVALID")
        payload = (_MAGIC + struct.pack(">QI", stamp, len(image))
                   + sha256(image).digest() + image)
        token = cipher.encrypt(payload)
        if len(token) > _MAX_ARCHIVE_BYTES:
            raise RestoreCloneLabError("QUEUE_SNAPSHOT_SIZE_OR_HEADER_INVALID")
        try:
            with target.open("xb") as handle:
                handle.write(token)
        except FileExistsError:
            raise RestoreCloneLabError("LAB_DESTINATION_EXISTS") from None
        return sha256(image).hexdigest()
    finally:
        memory.close()
        original.close()


def restore_queue_clone_lab(
    archive: str | Path, destination: str | Path, *, key: bytes, now: datetime,
) -> str:
    """Authenticate, reject expired G3 material, then publish a NEW test clone.

    Never changes a current Queue database. Failure leaves no destination clone.
    """
    source = _lab_destination(archive, kind="archive", exists=True)
    target = _lab_destination(destination, kind="clone", exists=False)
    cipher = _fernet(key)
    stamp = _now_epoch(now)
    if source.stat().st_size > _MAX_ARCHIVE_BYTES:
        raise RestoreCloneLabError("LAB_ARCHIVE_TOO_LARGE")
    try:
        data = cipher.decrypt(source.read_bytes())
    except InvalidToken:
        raise RestoreCloneLabError("LAB_ARCHIVE_AUTHENTICATION_FAILED") from None
    if not data.startswith(_MAGIC):
        raise RestoreCloneLabError("LAB_ARCHIVE_FORMAT_INVALID")
    metadata = data[len(_MAGIC):]
    if len(metadata) < 44:
        raise RestoreCloneLabError("LAB_ARCHIVE_FORMAT_INVALID")
    created, expected_size = struct.unpack(">QI", metadata[:12])
    expected_digest = metadata[12:44]
    image = metadata[44:]
    if (created > stamp or expected_size != len(image)
        or not 0 < len(image) <= _MAX_SQLITE_BYTES
        or not image.startswith(b"SQLite format 3\x00")
        or sha256(image).digest() != expected_digest):
        raise RestoreCloneLabError("LAB_ARCHIVE_FORMAT_OR_CLOCK_INVALID")

    recovered = sqlite3.connect(":memory:")
    stage = None
    try:
        recovered.deserialize(image)
        _verify_queue_scope(recovered)
        _disallow_overdue_personal_data(recovered, stamp)
        # Do not expose a plaintext clone at the final location before all gates.
        fd, stage_str = tempfile.mkstemp(
            dir=target.parent, prefix="lot08_3_b_lab_stage_", suffix=".sqlite",
        )
        stage = Path(stage_str)
        os.close(fd)
        disk = sqlite3.connect(str(stage))
        try:
            recovered.backup(disk)
            disk.execute("PRAGMA foreign_keys=ON")
            _verify_queue_scope(disk)
            _disallow_overdue_personal_data(disk, stamp)
        finally:
            disk.close()
        _before_clone_publish()
        try:
            # Hard-link is a create-only publication (refuses existing target).
            # Target and stage share the temp filesystem; unlike os.replace,
            # this never clobbers existing data.
            os.link(stage, target)
        except FileExistsError:
            raise RestoreCloneLabError("LAB_DESTINATION_EXISTS") from None
        return sha256(image).hexdigest()
    except (sqlite3.Error, OSError) as exc:
        raise RestoreCloneLabError("LAB_CLONE_VALIDATION_OR_IO_FAILED") from exc
    finally:
        recovered.close()
        if stage is not None:
            stage.unlink(missing_ok=True)
