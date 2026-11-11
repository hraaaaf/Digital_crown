"""LOT08.3-B2-A FUE: seven-day QR consumed-receipt purge, synthetic files only.

Every test uses a disposable QueueBase SQLite file, never patient data.
"""
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import QueueTenant, QueueLine, QueueVisitRecord, QueueEventRecord
from queue_core.service.retention_lab_08_3_b import (
    SYNTHETIC_LAB_APPLICATION_ID, RetentionLabError, retain_closed_visits_lab,
)
from queue_core.service import retention_qr_08_3_b2_lab as retention
from queue_core.service.retention_qr_08_3_b2_lab import retain_consumed_qr_ledger_lab


NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)
EPOCH = int(NOW.timestamp())
DAY = 86400
# Mirrors the 08.2-D kiosk schema. The maintenance routine rejects incompatible columns.
QR_SCHEMA = """
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


def _get(path, sql, params=()):
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        return conn.execute(sql, params).fetchall()


def _receipt(path, token, tenant, visit, age, *, expiry_age=1, consumed=True):
    consumed_epoch = EPOCH-age*DAY if consumed else None
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO queue_presence_qr_lab "
            "(qr_digest,tenant_id,queue_id,visit_id,expires_epoch,"
            "consumed_epoch,consumed_device,request_digest,result_version,result_sequence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                token,tenant,"Q1" if tenant=="T1" else "Q2",visit,
                EPOCH-expiry_age*DAY, consumed_epoch,
                "synthetic-device" if consumed else None,
                "synthetic-request-hash" if consumed else None,
                4 if consumed else None, 2 if consumed else None,
            ),
        )


@pytest.fixture
def lab(tmp_path):
    path = tmp_path / "lot08_3_b_lab_qr_receipts.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{path}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        for tenant in ("T1","T2"):
            session.add(QueueTenant(
                id=tenant, timezone_name="Africa/Casablanca",
                created_at_utc=NOW-timedelta(days=50),
            ))
        session.flush()
        session.add_all([
            QueueLine(id="Q1",tenant_id="T1",queue_key="WAITING",is_active=True),
            QueueLine(id="Q2",tenant_id="T2",queue_key="WAITING",is_active=True),
        ])
        session.flush()
        session.add(QueueVisitRecord(
            id="OLD_DONE",tenant_id="T1",queue_id="Q1",visit_kind="APPOINTMENT",
            status="DONE",version=4,scheduled_at_utc=NOW-timedelta(days=50),
            closed_at_utc=NOW-timedelta(days=40),queue_sequence=2,
            waiting_since_utc=NOW-timedelta(days=41),
            arrival_confirmed_at_utc=NOW-timedelta(days=41),
        ))
        session.add(QueueEventRecord(
            id="AUDIT_SYNTH",tenant_id="T1",visit_ref="OLD_DONE",
            aggregate_version=4,event_type="DONE",
            state_before="CHAIR",state_after="DONE",
            occurred_at_utc=NOW-timedelta(days=40),
            actor_kind="HUMAN",actor_ref="SYNTHETIC_OP",
        ))
        session.commit()
    engine.dispose()
    with sqlite3.connect(path) as c:
        c.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
        c.executescript(QR_SCHEMA)

    _receipt(path,"old-8-days","T1","OLD_DONE",8)
    _receipt(path,"boundary-7-days","T1","unrelated-7",7)
    _receipt(path,"recent-6-days","T1","unrelated-6",6)
    _receipt(path,"other-tenant-old","T2","unrelated-t2",90)
    _receipt(path,"pending-expired","T1","unrelated-pending",60,consumed=False)
    _receipt(path,"consumed-not-expired","T1","unrelated-expiry",9,expiry_age=-1)
    return path


def test_7_day_boundary_tenant_scope_dry_run_and_preserved_audit(lab):
    before = _get(lab,"SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest")
    preview = retain_consumed_qr_ledger_lab(lab,"T1",now=NOW)
    assert preview.eligible_receipts == 2
    assert preview.event_facts_preserved == 1 and not preview.executed
    assert _get(lab,"SELECT qr_digest FROM queue_presence_qr_lab ORDER BY qr_digest") == before
    assert _get(lab,"SELECT count(*) FROM sqlite_master WHERE name='queue_qr_retention_receipts_lab'") == [(0,)]

    result = retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert result.eligible_receipts == 2 and result.event_facts_preserved == 1
    assert {x[0] for x in _get(lab,"SELECT qr_digest FROM queue_presence_qr_lab")} == {
        "recent-6-days","other-tenant-old","pending-expired","consumed-not-expired",
    }
    assert _get(lab,"SELECT id, event_type FROM queue_event_log") == [("AUDIT_SYNTH","DONE")]
    assert _get(lab,"SELECT tenant_id,removed_count FROM queue_qr_retention_receipts_lab") == [("T1",2)]
    assert retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True).eligible_receipts == 0
    assert _get(lab,"SELECT count(*) FROM queue_qr_retention_receipts_lab") == [(1,)]


def test_delete_only_limited_batch_then_remaining(lab):
    x = retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True,limit=1)
    assert x.eligible_receipts == 1
    assert retain_consumed_qr_ledger_lab(lab,"T1",now=NOW).eligible_receipts == 1
    assert retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True).eligible_receipts == 1
    assert _get(lab,"SELECT removed_count FROM queue_qr_retention_receipts_lab ORDER BY rowid") == [(1,),(1,)]
    assert _get(lab,"SELECT count(*) FROM queue_event_log") == [(1,)]


def test_injected_crash_rolls_back_delete_and_receipt(lab,monkeypatch):
    def fail():
        raise RuntimeError("LAB_INJECTED_CRASH")
    monkeypatch.setattr(retention,"_after_first_delete_fault_oracle",fail)
    with pytest.raises(RuntimeError,match="LAB_INJECTED_CRASH"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert _get(lab,"SELECT count(*) FROM queue_presence_qr_lab") == [(6,)]
    assert _get(lab,"SELECT count(*) FROM queue_event_log") == [(1,)]
    assert _get(lab,"SELECT count(*) FROM sqlite_master WHERE name='queue_qr_retention_receipts_lab'") == [(0,)]


def test_immutable_receipt_and_event_ledger(lab):
    retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    with pytest.raises(sqlite3.IntegrityError,match="QR_RETENTION_RECEIPT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("UPDATE queue_qr_retention_receipts_lab SET removed_count=999")
    with pytest.raises(sqlite3.IntegrityError,match="QR_RETENTION_RECEIPT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("DELETE FROM queue_qr_retention_receipts_lab")
    with pytest.raises(sqlite3.IntegrityError,match="QUEUE_EVENT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("DELETE FROM queue_event_log")


def test_schema_corruption_missing_table_and_trigger_fail_closed(lab):
    with sqlite3.connect(lab) as c:
        c.execute("DROP TRIGGER queue_event_log_no_delete")
    with pytest.raises(RetentionLabError,match="QUEUE_EVENT_IMMUTABILITY_REQUIRED"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert _get(lab,"SELECT count(*) FROM queue_presence_qr_lab") == [(6,)]
    with sqlite3.connect(lab) as c:
        c.execute(
            "CREATE TRIGGER queue_event_log_no_delete BEFORE DELETE ON queue_event_log "
            "BEGIN SELECT RAISE(ABORT,'QUEUE_EVENT_IMMUTABLE'); END"
        )
        c.execute("ALTER TABLE queue_presence_qr_lab ADD COLUMN surprise TEXT")
    with pytest.raises(RetentionLabError,match="QR_LAB_SCHEMA_MISMATCH"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert _get(lab,"SELECT count(*) FROM queue_presence_qr_lab") == [(6,)]


def test_unmarked_or_wrong_file_bad_clock_scope_and_invalid_batch_fail(lab,tmp_path):
    with pytest.raises(RetentionLabError,match="AWARE_UTC_CLOCK_REQUIRED"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW.replace(tzinfo=None),execute=True)
    with pytest.raises(RetentionLabError,match="TENANT_SCOPE_REQUIRED"):
        retain_consumed_qr_ledger_lab(lab,"BAD_TENANT",now=NOW,execute=True)
    with pytest.raises(RetentionLabError,match="MAINTENANCE_ARGUMENT_INVALID"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True,limit=101)
    renamed = tmp_path/"ordinary.sqlite"
    renamed.write_bytes(lab.read_bytes())
    with pytest.raises(RetentionLabError,match="SYNTHETIC_LAB_FILE_REQUIRED"):
        retain_consumed_qr_ledger_lab(renamed,"T1",now=NOW,execute=True)
    with sqlite3.connect(lab) as c:
        c.execute("PRAGMA application_id=0")
    with pytest.raises(RetentionLabError,match="SYNTHETIC_LAB_MARKER_REQUIRED"):
        retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert _get(lab,"SELECT count(*) FROM queue_presence_qr_lab") == [(6,)]


def test_post_purge_lookup_rejects_old_qr_and_unblocks_closed_visit_retention(lab):
    # B1 refuses orphaning a visit with an outstanding historical QR record.
    with pytest.raises(RetentionLabError,match="QR_REFERENCES_REMAIN"):
        retain_closed_visits_lab(lab,"T1",now=NOW,execute=True)
    retain_consumed_qr_ledger_lab(lab,"T1",now=NOW,execute=True)
    assert _get(lab,
        "SELECT count(*) FROM queue_presence_qr_lab WHERE tenant_id='T1' AND qr_digest='old-8-days'"
    ) == [(0,)]
    # Only the old visit's QR record was associated with OLD_DONE.
    assert retain_closed_visits_lab(lab,"T1",now=NOW,execute=True).eligible_visits == 1
    assert _get(lab,"SELECT count(*) FROM queue_visits WHERE id='OLD_DONE'") == [(0,)]
    assert _get(lab,"SELECT count(*) FROM queue_event_log") == [(1,)]
