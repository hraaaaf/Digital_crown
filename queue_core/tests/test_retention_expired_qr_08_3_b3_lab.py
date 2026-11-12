"""LOT08.3-B3 FUE: never-consumed expired QR purge + fail-closed restore.

All fixtures are synthetic Queue SQLite inside pytest tmp_path; no clinical
database, production scheduler, real physical devices or patient identifiers.
"""
from datetime import datetime, timedelta, timezone
import os
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import (
    QueueTenant, QueueLine, QueueVisitRecord, QueueEventRecord,
)
from queue_core.service.kiosk_qr_lab import _SCHEMA as QR_SCHEMA
from queue_core.service.retention_lab_08_3_b import (
    SYNTHETIC_LAB_APPLICATION_ID, RetentionLabError, retain_closed_visits_lab,
)
from queue_core.service import retention_expired_qr_08_3_b3_lab as b3
from queue_core.service.retention_qr_08_3_b2_lab import retain_consumed_qr_ledger_lab
from queue_core.service import backup_restore_clone_08_3_b2_lab as backup
from queue_core.service import backup_rotation_08_3_b2c_lab as rotation

NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)
EPOCH = int(NOW.timestamp())
DAY = 86400


def rows(path, sql, args=()):
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        return conn.execute(sql, args).fetchall()


def insert_qr(path, token, tenant, visit, expiry, consumed=None):
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO queue_presence_qr_lab "
            "(qr_digest,tenant_id,queue_id,visit_id,expires_epoch,"
            "consumed_epoch,consumed_device,request_digest,"
            "result_version,result_sequence) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                token, tenant, "Q1" if tenant == "T1" else "Q2", visit,
                expiry, consumed,
                "dev_synth" if consumed is not None else None,
                "retry_synth" if consumed is not None else None,
                2 if consumed is not None else None,
                1 if consumed is not None else None,
            ),
        )


@pytest.fixture
def lab(tmp_path):
    path = tmp_path / "lot08_3_b_lab_unconsumed_expired.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{path}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            QueueTenant(id=t, timezone_name="Africa/Casablanca", created_at_utc=NOW)
            for t in ("T1", "T2")
        ])
        session.flush()
        session.add_all([
            QueueLine(id="Q1", tenant_id="T1", queue_key="WAIT", is_active=True),
            QueueLine(id="Q2", tenant_id="T2", queue_key="WAIT", is_active=True),
        ])
        session.flush()
        session.add_all([
            QueueVisitRecord(
                id="WAIT_T1", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="PLANNED", version=0,
                scheduled_at_utc=NOW+timedelta(hours=1),
            ),
            QueueVisitRecord(
                id="WAIT_T2", tenant_id="T2", queue_id="Q2",
                visit_kind="APPOINTMENT", status="PLANNED", version=0,
                scheduled_at_utc=NOW+timedelta(hours=1),
            ),
            QueueVisitRecord(
                id="DONE_T1", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="DONE", version=2,
                scheduled_at_utc=NOW-timedelta(days=2),
                arrival_confirmed_at_utc=NOW-timedelta(days=2),
                waiting_since_utc=NOW-timedelta(days=2),
                closed_at_utc=NOW-timedelta(days=1), queue_sequence=1,
            ),
        ])
        session.flush()
        session.add(QueueEventRecord(
            id="AUDIT_B3_SYNTH", tenant_id="T1", visit_ref="DONE_T1",
            aggregate_version=2, event_type="DONE", state_before="CHAIR",
            state_after="DONE", occurred_at_utc=NOW-timedelta(days=1),
            actor_kind="HUMAN", actor_ref="SYNTH_OP",
        ))
        session.commit()
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
        db.executescript(QR_SCHEMA)
    insert_qr(path, "expired_past", "T1", "WAIT_T1", EPOCH-1)
    insert_qr(path, "expired_boundary", "T1", "WAIT_T1", EPOCH)
    insert_qr(path, "future_pending", "T1", "WAIT_T1", EPOCH+1)
    insert_qr(path, "consumed_recent", "T1", "DONE_T1", EPOCH-100, EPOCH-50)
    insert_qr(path, "other_future", "T2", "WAIT_T2", EPOCH+DAY)
    return path


def test_b3_preview_and_exact_expiration_second_and_other_tenant_untouched(lab):
    initial = rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest")
    pre = b3.retain_expired_unconsumed_qr_lab(
        lab, "T1", now=NOW-timedelta(seconds=1),
    )
    assert pre.eligible_codes == 1 and not pre.executed
    preview = b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW)
    assert preview.eligible_codes == 2
    assert preview.event_facts_preserved == 1
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest") == initial
    assert rows(lab, "SELECT 1 FROM sqlite_master WHERE name='queue_qr_expired_unconsumed_receipts_lab'") == []
    actual = b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert actual.eligible_codes == 2 and actual.executed
    assert {r[0] for r in rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab")} == {
        "future_pending", "consumed_recent", "other_future",
    }
    assert rows(lab, "SELECT id,event_type FROM queue_event_log") == [
        ("AUDIT_B3_SYNTH", "DONE")
    ]
    assert rows(lab, "SELECT tenant_id,removed_count FROM queue_qr_expired_unconsumed_receipts_lab") == [
        ("T1", 2)
    ]
    assert b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True).eligible_codes == 0
    assert rows(lab, "SELECT count(*) FROM queue_qr_expired_unconsumed_receipts_lab") == [(1,)]


def test_b3_batch_100_bound_idempotency_and_tenant_scope(lab):
    insert_qr(lab, "other_expired", "T2", "WAIT_T2", EPOCH-100)
    first = b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, limit=1, execute=True)
    assert first.eligible_codes == 1
    assert b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW).eligible_codes == 1
    assert b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True).eligible_codes == 1
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab WHERE tenant_id='T2' ORDER BY qr_digest") == [
        ("other_expired",), ("other_future",)
    ]
    assert b3.retain_expired_unconsumed_qr_lab(lab, "T2", now=NOW, execute=True).eligible_codes == 1
    assert rows(lab, "SELECT removed_count FROM queue_qr_expired_unconsumed_receipts_lab ORDER BY rowid") == [
        (1,), (1,), (1,)
    ]


def test_b3_fault_after_first_delete_rolls_back_whole_transaction(lab, monkeypatch):
    def interrupt():
        raise RuntimeError("LAB_B3_CRASH")
    monkeypatch.setattr(b3, "_after_first_unconsumed_delete_lab", interrupt)
    before = rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest")
    with pytest.raises(RuntimeError, match="LAB_B3_CRASH"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest") == before
    assert rows(lab, "SELECT 1 FROM sqlite_master WHERE name='queue_qr_expired_unconsumed_receipts_lab'") == []
    assert rows(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_b3_receipt_is_append_only_and_audit_untouched(lab):
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    for sql in (
        "UPDATE queue_qr_expired_unconsumed_receipts_lab SET removed_count=9",
        "DELETE FROM queue_qr_expired_unconsumed_receipts_lab",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="QR_UNUSED_RECEIPT_IMMUTABLE"):
            with sqlite3.connect(lab) as conn:
                conn.execute(sql)
    with pytest.raises(sqlite3.IntegrityError, match="QUEUE_EVENT_IMMUTABLE"):
        with sqlite3.connect(lab) as conn:
            conn.execute("DELETE FROM queue_event_log")
    assert rows(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_b3_refuses_mutable_or_incompatible_existing_receipt_table(lab):
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "CREATE TABLE queue_qr_expired_unconsumed_receipts_lab "
            "(id TEXT PRIMARY KEY, tenant_id TEXT, executed_epoch INTEGER, removed_count INTEGER)"
        )
    with pytest.raises(RetentionLabError, match="QR_UNUSED_RECEIPT_GUARD_REQUIRED"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT count(*) FROM queue_presence_qr_lab") == [(5,)]
    with sqlite3.connect(lab) as conn:
        conn.execute("DROP TABLE queue_qr_expired_unconsumed_receipts_lab")
        conn.execute(
            "CREATE TABLE queue_qr_expired_unconsumed_receipts_lab "
            "(id TEXT PRIMARY KEY, unexpected TEXT)"
        )
    with pytest.raises(RetentionLabError, match="QR_UNUSED_RECEIPT_SCHEMA_MISMATCH"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT count(*) FROM queue_presence_qr_lab") == [(5,)]


def test_b3_missing_audit_trigger_or_alien_qr_schema_denied(lab):
    with sqlite3.connect(lab) as conn:
        conn.execute("DROP TRIGGER queue_event_log_no_update")
    with pytest.raises(RetentionLabError, match="QUEUE_EVENT_IMMUTABILITY_REQUIRED"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "CREATE TRIGGER queue_event_log_no_update BEFORE UPDATE ON queue_event_log "
            "BEGIN SELECT RAISE(ABORT,'QUEUE_EVENT_IMMUTABLE'); END"
        )
        conn.execute("ALTER TABLE queue_presence_qr_lab ADD COLUMN unknown TEXT")
    with pytest.raises(RetentionLabError, match="QR_LAB_SCHEMA_MISMATCH"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT count(*) FROM queue_presence_qr_lab") == [(5,)]


def test_b3_wrong_tenant_unsafe_file_bad_clock_batch_type_and_symlink_denied(lab, tmp_path):
    for tenant in ("T3", "x "):
        with pytest.raises(RetentionLabError, match="TENANT_SCOPE_REQUIRED"):
            b3.retain_expired_unconsumed_qr_lab(lab, tenant, now=NOW, execute=True)
    for value in (NOW.replace(tzinfo=None),):
        with pytest.raises(RetentionLabError, match="AWARE_UTC_CLOCK_REQUIRED"):
            b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=value, execute=True)
    for limit in (0, 101, True):
        with pytest.raises(RetentionLabError, match="MAINTENANCE_ARGUMENT_INVALID"):
            b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True, limit=limit)
    wrong = tmp_path / "cabinet.sqlite"
    wrong.write_bytes(lab.read_bytes())
    with pytest.raises(RetentionLabError, match="SYNTHETIC_LAB_FILE_REQUIRED"):
        b3.retain_expired_unconsumed_qr_lab(wrong, "T1", now=NOW, execute=True)
    link = tmp_path / "lot08_3_b_lab_symlink.sqlite"
    try:
        link.symlink_to(lab)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable; other negative cases checked")
    with pytest.raises(RetentionLabError, match="SYNTHETIC_LAB_FILE_REQUIRED"):
        b3.retain_expired_unconsumed_qr_lab(link, "T1", now=NOW, execute=True)


def test_b3_malformed_unconsumed_expiry_fail_closed(lab):
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "UPDATE queue_presence_qr_lab SET expires_epoch='oops' "
            "WHERE qr_digest='expired_past'"
        )
    with pytest.raises(RetentionLabError, match="QR_UNUSED_EXPIRY_INVALID"):
        b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT count(*) FROM queue_presence_qr_lab") == [(5,)]


def test_b3_no_overdelete_consumed_retry_and_b2a_retention_still_independent(lab):
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "UPDATE queue_presence_qr_lab SET consumed_epoch=? "
            "WHERE qr_digest='consumed_recent'", (EPOCH-8*DAY,),
        )
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab WHERE qr_digest='consumed_recent'") == [
        ("consumed_recent",)
    ]
    assert retain_consumed_qr_ledger_lab(lab, "T1", now=NOW, execute=True).eligible_receipts == 1
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab WHERE qr_digest='consumed_recent'") == []
    assert rows(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_b3_unconsumed_reference_blocks_then_unblocks_30d_closed_visit_purge(lab):
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "UPDATE queue_visits SET closed_at_utc=?,scheduled_at_utc=? "
            "WHERE id='DONE_T1'",
            ("2029-12-01 00:00:00.000000", "2029-11-30 00:00:00.000000"),
        )
    insert_qr(lab, "old_done_expired", "T1", "DONE_T1", EPOCH-DAY)
    # The same DONE visit also has a consumed receipt: retire it ONLY under
    # B2-A's independent >7-day policy before attempting B1 visit removal.
    with sqlite3.connect(lab) as conn:
        conn.execute(
            "UPDATE queue_presence_qr_lab SET consumed_epoch=? "
            "WHERE qr_digest='consumed_recent'", (EPOCH-8*DAY,),
        )
    with pytest.raises(RetentionLabError, match="QR_REFERENCES_REMAIN"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    assert retain_consumed_qr_ledger_lab(lab, "T1", now=NOW, execute=True).eligible_receipts == 1
    assert rows(lab, "SELECT qr_digest FROM queue_presence_qr_lab WHERE qr_digest='old_done_expired'") == []
    assert retain_closed_visits_lab(lab, "T1", now=NOW, execute=True).eligible_visits == 1
    assert rows(lab, "SELECT id FROM queue_visits WHERE id='DONE_T1'") == []
    assert rows(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_b3_stale_encrypted_archive_cannot_resurrect_expired_qr_after_purge(lab, tmp_path):
    archive = tmp_path / "lot08_3_b_lab_backup_b3_old.fernet"
    old_clone = tmp_path / "lot08_3_b_lab_restored_old_b3.sqlite"
    new_archive = tmp_path / "lot08_3_b_lab_backup_b3_new.fernet"
    new_clone = tmp_path / "lot08_3_b_lab_restored_new_b3.sqlite"
    key = Fernet.generate_key()
    backup.seal_queue_snapshot_lab(lab, archive, key=key, now=NOW)
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    with pytest.raises(backup.RestoreCloneLabError, match="RESTORE_EXPIRED_UNCONSUMED_QR_DENIED"):
        backup.restore_queue_clone_lab(archive, old_clone, key=key, now=NOW)
    assert not old_clone.exists()
    backup.seal_queue_snapshot_lab(lab, new_archive, key=key, now=NOW)
    backup.restore_queue_clone_lab(new_archive, new_clone, key=key, now=NOW)
    assert rows(new_clone, "SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest") == [
        ("consumed_recent",), ("future_pending",), ("other_future",)
    ]
    assert rows(new_clone, "SELECT tenant_id,removed_count FROM queue_qr_expired_unconsumed_receipts_lab") == [
        ("T1", 2)
    ]
    assert rows(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_b3_cloned_snapshot_exact_expiry_boundary_now_minus_one_allowed(lab, tmp_path):
    with sqlite3.connect(lab) as conn:
        conn.execute("DELETE FROM queue_presence_qr_lab WHERE qr_digest='expired_past'")
    archive = tmp_path / "lot08_3_b_lab_backup_b3_boundary.fernet"
    before = tmp_path / "lot08_3_b_lab_restored_b3_before.sqlite"
    at = tmp_path / "lot08_3_b_lab_restored_b3_at.sqlite"
    key = Fernet.generate_key()
    backup.seal_queue_snapshot_lab(lab, archive, key=key, now=NOW-timedelta(seconds=1))
    backup.restore_queue_clone_lab(
        archive, before, key=key, now=NOW-timedelta(seconds=1),
    )
    assert rows(before, "SELECT qr_digest FROM queue_presence_qr_lab WHERE qr_digest='expired_boundary'") == [
        ("expired_boundary",)
    ]
    with pytest.raises(backup.RestoreCloneLabError, match="RESTORE_EXPIRED_UNCONSUMED_QR_DENIED"):
        backup.restore_queue_clone_lab(archive, at, key=key, now=NOW)
    assert not at.exists()


def test_b3_seal_rejects_missing_receipt_guard_before_archive_creation(lab, tmp_path):
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    with sqlite3.connect(lab) as conn:
        conn.execute("DROP TRIGGER queue_qr_expired_unconsumed_no_delete")
    archive = tmp_path / "lot08_3_b_lab_backup_b3_altered_receipt.fernet"
    clone = tmp_path / "lot08_3_b_lab_restored_b3_altered_receipt.sqlite"
    key = Fernet.generate_key()
    # Stronger early failure: the source cannot even be sealed while its
    # append-only evidence is mutable; no archive and no clone may be created.
    with pytest.raises(backup.RestoreCloneLabError, match="QR_UNUSED_RECEIPT_GUARD_REQUIRED"):
        backup.seal_queue_snapshot_lab(lab, archive, key=key, now=NOW)
    assert not archive.exists() and not clone.exists()


def test_b3_vault_rotation_uses_same_fail_closed_restore_gate(lab, tmp_path):
    vault = tmp_path / "lot08_3_b_lab_vault_b3"
    vault.mkdir()
    backup_key, manifest_key = Fernet.generate_key(), os.urandom(32)
    # Produce a genuinely restorable archived generation two seconds BEFORE
    # the earliest pending token expires (B2-C verifies its clone pre-publish).
    prior = NOW - timedelta(seconds=2)
    first = rotation.rotate_queue_vault_lab(
        lab, vault, backup_key=backup_key, manifest_key=manifest_key,
        trusted_anchor=None, now=prior,
    )
    b3.retain_expired_unconsumed_qr_lab(lab, "T1", now=NOW, execute=True)
    target = tmp_path / "lot08_3_b_lab_restored_vault_b3.sqlite"
    with pytest.raises(backup.RestoreCloneLabError, match="RESTORE_EXPIRED_UNCONSUMED_QR_DENIED"):
        rotation.restore_queue_vault_clone_lab(
            vault, target, backup_key=backup_key, manifest_key=manifest_key,
            trusted_anchor=first.anchor, slot="daily",
            bucket=NOW.strftime("%Y-%m-%d"), now=NOW,
        )
    assert not target.exists()
