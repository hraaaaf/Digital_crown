"""LOT08.3-B2-B synthetic-only FUE: sealed Queue snapshot and restore clone.

Never opens a real cabinet file, imports patient data or publishes to runtime.
"""
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import (
    QueueEventRecord, QueueLine, QueueTenant, QueueVisitRecord,
)
from queue_core.service.kiosk_qr_lab import _SCHEMA as QR_SCHEMA
from queue_core.service.retention_lab_08_3_b import (
    SYNTHETIC_LAB_APPLICATION_ID, retain_closed_visits_lab,
)
from queue_core.service.retention_qr_08_3_b2_lab import retain_consumed_qr_ledger_lab
from queue_core.service import backup_restore_clone_08_3_b2_lab as restore

NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)
EPOCH = int(NOW.timestamp())


def rows(path, query, params=()):
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        return db.execute(query, params).fetchall()


@pytest.fixture
def lab(tmp_path):
    source = tmp_path / "lot08_3_b_lab_queue_restore.sqlite"
    archive = tmp_path / "lot08_3_b_lab_backup_01.fernet"
    clone = tmp_path / "lot08_3_b_lab_restored_01.sqlite"
    key = Fernet.generate_key()
    engine = create_engine(f"sqlite+pysqlite:///{source}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            QueueTenant(id="T1", timezone_name="Africa/Casablanca", created_at_utc=NOW),
            QueueTenant(id="T2", timezone_name="Africa/Casablanca", created_at_utc=NOW),
        ])
        session.flush()
        session.add_all([
            QueueLine(id="Q1", tenant_id="T1", queue_key="Q1", is_active=True),
            QueueLine(id="Q2", tenant_id="T2", queue_key="Q2", is_active=True),
        ])
        session.flush()
        session.add_all([
            QueueVisitRecord(
                id="VISIT_CLOSED", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="DONE", version=2,
                scheduled_at_utc=NOW-timedelta(days=10),
                arrival_confirmed_at_utc=NOW-timedelta(days=4),
                waiting_since_utc=NOW-timedelta(days=4),
                closed_at_utc=NOW-timedelta(days=2), queue_sequence=1,
            ),
            QueueVisitRecord(
                id="VISIT_WAITING", tenant_id="T2", queue_id="Q2",
                visit_kind="WALK_IN", status="WAITING", version=1,
                scheduled_at_utc=None,
                arrival_confirmed_at_utc=NOW-timedelta(hours=2),
                waiting_since_utc=NOW-timedelta(hours=2),
                queue_sequence=1,
            ),
        ])
        session.flush()
        session.add(QueueEventRecord(
            id="AUDIT_FAKE", tenant_id="T1", visit_ref="VISIT_CLOSED",
            aggregate_version=2, event_type="DONE", state_before="CHAIR",
            state_after="DONE", occurred_at_utc=NOW-timedelta(days=2),
            actor_kind="HUMAN", actor_ref="SYNTH_OPERATOR",
        ))
        session.commit()
    engine.dispose()
    with sqlite3.connect(source) as db:
        db.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
        db.executescript(QR_SCHEMA)
        db.execute(
            "INSERT INTO queue_presence_qr_lab "
            "(qr_digest,tenant_id,queue_id,visit_id,expires_epoch,consumed_epoch,"
            "consumed_device,request_digest,result_version,result_sequence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "qr-synthetic", "T1", "Q1", "VISIT_CLOSED",
                EPOCH-3*86400, EPOCH-86400,
                "dev_fake", "request_fake", 2, 1,
            ),
        )
    return source, archive, clone, key


def test_sealed_backup_and_actual_cloned_sqlite_roundtrip_preserve_all_tenants(lab):
    source, archive, clone, key = lab
    before_t1 = rows(source, "SELECT id,status FROM queue_visits WHERE tenant_id='T1'")
    before_t2 = rows(source, "SELECT id,status FROM queue_visits WHERE tenant_id='T2'")
    digest = restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    assert archive.exists() and not clone.exists()
    assert archive.read_bytes().startswith(b"gAAAA")  # Fernet base64 token.
    assert b"SQLite format 3" not in archive.read_bytes()
    restored_digest = restore.restore_queue_clone_lab(
        archive, clone, key=key, now=NOW,
    )
    assert digest == restored_digest
    assert rows(clone, "SELECT id,status FROM queue_visits WHERE tenant_id='T1'") == before_t1
    assert rows(clone, "SELECT id,status FROM queue_visits WHERE tenant_id='T2'") == before_t2
    assert rows(clone, "SELECT event_type,actor_ref FROM queue_event_log") == [
        ("DONE", "SYNTH_OPERATOR")
    ]
    assert rows(clone, "PRAGMA application_id") == [(SYNTHETIC_LAB_APPLICATION_ID,)]
    assert rows(source, "SELECT count(*) FROM queue_visits") == [(2,)]


def test_restoration_rejects_old_snapshot_that_resurrects_30_day_closed_visit(lab):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    with pytest.raises(restore.RestoreCloneLabError, match="RESTORE_OVERDUE_VISIT_DENIED"):
        restore.restore_queue_clone_lab(
            archive, clone, key=key, now=NOW+timedelta(days=40),
        )
    assert not clone.exists()
    assert rows(source, "SELECT id FROM queue_visits WHERE id='VISIT_CLOSED'") == [
        ("VISIT_CLOSED",)
    ]


def test_restoration_rejects_old_consumed_qr_even_before_visit_30_day_cutoff(lab):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    with pytest.raises(restore.RestoreCloneLabError, match="RESTORE_OVERDUE_QR_DENIED"):
        restore.restore_queue_clone_lab(
            archive, clone, key=key, now=NOW+timedelta(days=8),
        )
    assert not clone.exists()


def test_backup_after_verified_purges_restores_without_resurrection(lab):
    source, archive, clone, key = lab
    future = NOW+timedelta(days=40)
    assert retain_consumed_qr_ledger_lab(source, "T1", now=future, execute=True).eligible_receipts == 1
    assert retain_closed_visits_lab(source, "T1", now=future, execute=True).eligible_visits == 1
    assert rows(source, "SELECT count(*) FROM queue_visits") == [(1,)]
    assert rows(source, "SELECT count(*) FROM queue_event_log") == [(1,)]
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=future)
    restore.restore_queue_clone_lab(archive, clone, key=key, now=future)
    assert rows(clone, "SELECT id FROM queue_visits") == [("VISIT_WAITING",)]
    assert rows(clone, "SELECT count(*) FROM queue_presence_qr_lab") == [(0,)]
    assert rows(clone, "SELECT count(*) FROM queue_event_log") == [(1,)]
    assert rows(clone, "SELECT removed_count FROM queue_qr_retention_receipts_lab") == [(1,)]
    assert rows(clone, "SELECT visits_removed FROM queue_retention_receipts_lab") == [(1,)]


def test_wrong_key_and_ciphertext_tampering_fail_without_clone(lab):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    with pytest.raises(restore.RestoreCloneLabError, match="LAB_ARCHIVE_AUTHENTICATION_FAILED"):
        restore.restore_queue_clone_lab(
            archive, clone, key=Fernet.generate_key(), now=NOW,
        )
    content = bytearray(archive.read_bytes())
    content[-11] ^= 1
    archive.write_bytes(content)
    with pytest.raises(restore.RestoreCloneLabError, match="LAB_ARCHIVE_AUTHENTICATION_FAILED"):
        restore.restore_queue_clone_lab(archive, clone, key=key, now=NOW)
    assert not clone.exists()


def test_fail_closed_on_missing_guard_and_unexpected_patient_table(lab):
    source, archive, clone, key = lab
    with sqlite3.connect(source) as db:
        db.execute("DROP TRIGGER queue_event_log_no_update")
    with pytest.raises(restore.RestoreCloneLabError, match="QUEUE_EVENT_IMMUTABILITY_REQUIRED"):
        restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    assert not archive.exists()
    with sqlite3.connect(source) as db:
        db.execute(
            "CREATE TRIGGER queue_event_log_no_update BEFORE UPDATE ON queue_event_log "
            "BEGIN SELECT RAISE(ABORT,'QUEUE_EVENT_IMMUTABLE'); END"
        )
        db.execute("CREATE TABLE patients (id TEXT PRIMARY KEY)")
    with pytest.raises(restore.RestoreCloneLabError, match="QUEUE_LAB_SCHEMA_REQUIRED"):
        restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    assert not archive.exists()


def test_fail_closed_on_source_name_and_header_marker(lab, tmp_path):
    source, archive, _, key = lab
    ordinary = tmp_path/"cabinet.sqlite"
    ordinary.write_bytes(source.read_bytes())
    with pytest.raises(restore.RestoreCloneLabError, match="SYNTHETIC_LAB_FILE_REQUIRED"):
        restore.seal_queue_snapshot_lab(ordinary, archive, key=key, now=NOW)
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA application_id=0")
    with pytest.raises(restore.RestoreCloneLabError, match="SYNTHETIC_LAB_MARKER_REQUIRED"):
        restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    assert not archive.exists()


def test_refuse_to_overwrite_archive_or_existing_destination(lab):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    original_archive = archive.read_bytes()
    with pytest.raises(restore.RestoreCloneLabError, match="LAB_DESTINATION_REQUIRED"):
        restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    assert archive.read_bytes() == original_archive
    clone.write_text("PREEXISTING_CONTENT")
    with pytest.raises(restore.RestoreCloneLabError, match="LAB_DESTINATION_REQUIRED"):
        restore.restore_queue_clone_lab(archive, clone, key=key, now=NOW)
    assert clone.read_text() == "PREEXISTING_CONTENT"


def test_injected_crash_before_clone_publication_has_zero_residue(lab, monkeypatch):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    def injected_crash():
        raise RuntimeError("INJECTED_RESTORE_FAILURE")
    monkeypatch.setattr(restore, "_before_clone_publish", injected_crash)
    with pytest.raises(RuntimeError, match="INJECTED_RESTORE_FAILURE"):
        restore.restore_queue_clone_lab(archive, clone, key=key, now=NOW)
    assert not clone.exists()
    assert not list(clone.parent.glob("lot08_3_b_lab_stage_*.sqlite"))


def test_future_dated_backup_and_invalid_clock_refused(lab):
    source, archive, clone, key = lab
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    with pytest.raises(restore.RestoreCloneLabError, match="LAB_ARCHIVE_FORMAT_OR_CLOCK_INVALID"):
        restore.restore_queue_clone_lab(
            archive, clone, key=key, now=NOW-timedelta(seconds=1),
        )
    with pytest.raises(restore.RestoreCloneLabError, match="AWARE_UTC_CLOCK_REQUIRED"):
        restore.restore_queue_clone_lab(
            archive, clone, key=key, now=NOW.replace(tzinfo=None),
        )
    assert not clone.exists()


def test_uncheckpointed_wal_committed_change_included_in_online_snapshot(lab):
    source, archive, clone, key = lab
    conn = sqlite3.connect(source)
    try:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        conn.execute(
            "INSERT INTO queue_tenants(id,timezone_name,created_at_utc) "
            "VALUES('T3','Africa/Casablanca','2030-04-01 00:00:00')"
        )
        conn.commit()
        restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    finally:
        conn.close()
    restore.restore_queue_clone_lab(archive, clone, key=key, now=NOW)
    assert ("T3",) in rows(clone, "SELECT id FROM queue_tenants")


def test_restore_rejects_overdue_rows_in_other_tenant(lab):
    source, archive, clone, key = lab
    with sqlite3.connect(source) as db:
        db.execute(
            "UPDATE queue_visits SET status='DONE',"
            "closed_at_utc='2030-01-01 00:00:00.000000' "
            "WHERE id='VISIT_WAITING'"
        )
    restore.seal_queue_snapshot_lab(source, archive, key=key, now=NOW)
    with pytest.raises(restore.RestoreCloneLabError,match="RESTORE_OVERDUE_VISIT_DENIED"):
        restore.restore_queue_clone_lab(archive, clone, key=key, now=NOW)
    assert not clone.exists()
