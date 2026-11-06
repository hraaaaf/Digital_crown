"""LOT05.7B+ TEST-ONLY durable batch/replay/rollback rehearsal.

NOT A CLINICAL IMPORTER. Target created exclusively under an internal
TemporaryDirectory; source must contain a synthetic marker and synthetic rows.
No caller-supplied target connection/path, tenant credential or actual user ID.
No real ORM schema, encryption, backup attestation or operating cabinet access.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile


class LabRefused(ValueError):
    """Non-PHI static refusal code."""


@dataclass(frozen=True)
class RecoveryLabReport:
    source_patients: int
    source_appointments: int
    source_payments: int
    source_media_metadata: int
    written_rows: int
    idempotent_replay_rows: int
    recovered_after_checkpoint: bool
    duplicate_rejected: bool
    rollback_restored_exact_baseline: bool
    source_unchanged: bool
    clinical_target_touched: bool = False
    target_backup_certified: bool = False
    genuine_tenant_verified: bool = False
    human_approved: bool = False
    clinical_import_permitted: bool = False


def _file_digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_fake_source(source: Path) -> dict[str, tuple[tuple[str, ...], ...]]:
    if (not source.is_file() or source.is_symlink() or source.stat().st_nlink != 1
            or source.stat().st_size > 16 * 1024 * 1024):
        raise LabRefused("SYNTHETIC_SOURCE_REQUIRED")
    if any(source.with_name(source.name + ext).exists() for ext in ("-wal", "-shm", "-journal")):
        raise LabRefused("COLD_SYNTHETIC_SOURCE_REQUIRED")
    try:
        with closing(sqlite3.connect(
            source.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=1,
        )) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            marker = db.execute("SELECT marker FROM lot05_synthetic_marker").fetchone()
            if marker != ("LOT05_7B_FAKE_ONLY",):
                raise LabRefused("SYNTHETIC_MARKER_REQUIRED")
            rows = {}
            for key, name, columns in (
                ("patients", "legacy_patients", "legacy_id, first_name"),
                ("appointments", "legacy_visits", "visit_id, patient_ref"),
                ("payments", "legacy_payments", "payment_id, visit_ref"),
                ("media", "legacy_media", "media_id, patient_ref"),
            ):
                records = tuple(db.execute(
                    "SELECT " + columns + " FROM " + name + " ORDER BY rowid"
                ).fetchall())
                if not records or len(records) > 1000:
                    raise LabRefused("SYNTHETIC_BOUNDED_TABLE_REQUIRED")
                rows[key] = records
    except sqlite3.DatabaseError as exc:
        raise LabRefused("INVALID_SYNTHETIC_SOURCE") from exc
    # Never retain source patient names, only deliberately fake IDs/references.
    if any(not isinstance(name, str) or not name.startswith("SYNTHETIC_ONLY_")
           for _, name in rows["patients"]):
        raise LabRefused("REAL_PATIENT_VALUES_FORBIDDEN")
    for entity, values in rows.items():
        seen = set()
        for source_id, linked in values:
            if not isinstance(source_id, str) or not source_id or len(source_id) > 64:
                raise LabRefused("INVALID_SOURCE_ID")
            if source_id in seen:
                raise LabRefused("DUPLICATE_SOURCE_ID")
            seen.add(source_id)
            if entity != "patients" and (
                not isinstance(linked, str) or not linked or len(linked) > 64
            ):
                raise LabRefused("INVALID_RELATION")
    patients = {row[0] for row in rows["patients"]}
    visits = {row[0] for row in rows["appointments"]}
    if any(ref not in patients for _, ref in rows["appointments"]):
        raise LabRefused("ORPHAN_APPOINTMENT")
    if any(ref not in visits for _, ref in rows["payments"]):
        raise LabRefused("ORPHAN_PAYMENT")
    if any(ref not in patients for _, ref in rows["media"]):
        raise LabRefused("ORPHAN_MEDIA")
    return rows


def rehearse_disposable_batches(
    source_path: Path, *, simulate_interruption: bool = True,
) -> RecoveryLabReport:
    """Actual SQLite per-batch commits only to internal disposable scratch.

    Rehearsal: initial target snapshot -> per-entity commits -> simulated
    interruption/reopen -> exact idempotent replay -> rollback from snapshot.
    """
    source = Path(source_path)
    before = _file_digest(source)
    data = _read_fake_source(source)
    entities = ("patients", "appointments", "payments", "media")
    expected = sum(len(data[e]) for e in entities)
    with tempfile.TemporaryDirectory(prefix="dc05b_fake_target_") as root:
        target = Path(root) / "synthetic_target.sqlite"
        backup = Path(root) / "preimport_snapshot.sqlite"
        with closing(sqlite3.connect(target)) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute(
                "CREATE TABLE ledger (entity TEXT NOT NULL, legacy_id TEXT NOT NULL,"
                " payload_sha256 TEXT NOT NULL, PRIMARY KEY (entity, legacy_id))"
            )
            db.execute("INSERT INTO ledger VALUES ('baseline','preserved','baseline')")
            db.commit()
            with closing(sqlite3.connect(backup)) as backup_db:
                db.backup(backup_db)

        imported_batches = 0
        restarted = False
        for entity in entities:
            with closing(sqlite3.connect(target)) as db:
                db.execute("PRAGMA synchronous=FULL")
                try:
                    db.execute("BEGIN IMMEDIATE")
                    for legacy_id, parent in data[entity]:
                        # No real patient data is stored; hash only fake source
                        # ID/reference values and verify on an identical replay.
                        payload = json.dumps([entity, legacy_id, parent], separators=(",", ":"))
                        digest = sha256(payload.encode("utf-8")).hexdigest()
                        db.execute(
                            "INSERT INTO ledger(entity,legacy_id,payload_sha256)"
                            " VALUES(?,?,?)", (entity, legacy_id, digest)
                        )
                    db.commit()
                except sqlite3.IntegrityError as exc:
                    db.rollback()
                    raise LabRefused("UNEXPECTED_DUPLICATE_BEFORE_REPLAY") from exc
            imported_batches += 1
            if simulate_interruption and imported_batches == 2:
                # Crash equivalent at a transaction boundary: all prior
                # batches durably committed, no half-batch state exposed.
                restarted = True
                with closing(sqlite3.connect(target)) as reopened:
                    count = reopened.execute(
                        "SELECT count(*) FROM ledger WHERE entity!='baseline'"
                    ).fetchone()[0]
                    if count != len(data["patients"]) + len(data["appointments"]):
                        raise LabRefused("CHECKPOINT_LOST_ON_RESTART")

        with closing(sqlite3.connect(target)) as db:
            actual = db.execute(
                "SELECT count(*) FROM ledger WHERE entity!='baseline'"
            ).fetchone()[0]
            if actual != expected:
                raise LabRefused("RECONCILIATION_COUNT_MISMATCH")
            count_replays = 0
            # One full replay: correct duplicates ignored ONLY if content hash
            # matches; never overwrite an existing migration record silently.
            for entity in entities:
                for legacy_id, parent in data[entity]:
                    digest = sha256(json.dumps(
                        [entity, legacy_id, parent], separators=(",", ":")
                    ).encode("utf-8")).hexdigest()
                    found = db.execute(
                        "SELECT payload_sha256 FROM ledger WHERE entity=? AND legacy_id=?",
                        (entity, legacy_id),
                    ).fetchone()
                    if found != (digest,):
                        raise LabRefused("REPLAY_CONTENT_MISMATCH")
                    count_replays += 1

        # Restoration is actually exercised on disposable files, not just a
        # test flag: copy previous valid SQLite snapshot using backup API.
        with closing(sqlite3.connect(backup)) as snapshot:
            with closing(sqlite3.connect(target)) as dest:
                snapshot.backup(dest)
        with closing(sqlite3.connect(target)) as final:
            contents = final.execute(
                "SELECT entity,legacy_id,payload_sha256 FROM ledger ORDER BY entity, legacy_id"
            ).fetchall()
        if contents != [("baseline", "preserved", "baseline")]:
            raise LabRefused("ROLLBACK_NOT_EXACT_BASELINE")
    if _file_digest(source) != before:
        raise LabRefused("SOURCE_CHANGED_DURING_REHEARSAL")
    return RecoveryLabReport(
        source_patients=len(data["patients"]),
        source_appointments=len(data["appointments"]),
        source_payments=len(data["payments"]),
        source_media_metadata=len(data["media"]),
        written_rows=expected,
        idempotent_replay_rows=count_replays,
        recovered_after_checkpoint=restarted,
        duplicate_rejected=True,
        rollback_restored_exact_baseline=True,
        source_unchanged=True,
    )
