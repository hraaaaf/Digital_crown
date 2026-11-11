"""LOT08.3-B FUE-0: real isolated SQLite retention (synthetic only).

Prove 30-day boundary, tenant isolation, reference cascade, 12-month audit
preservation, QR orphan refusal, append-only receipt, dry-run and SQL rollback.
Never exercise clinical databases or a real cabinet installable.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import (
    QueueEventRecord, QueueExternalReference, QueueLine, QueueResource,
    QueueTenant, QueueVisitRecord, QueueVisitResource,
)
from queue_core.service import retention_lab_08_3_b as retention
from queue_core.service.retention_lab_08_3_b import (
    RetentionLabError, retain_closed_visits_lab,
)


NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def lab(tmp_path):
    dbfile = tmp_path / "lot08_3_b_lab_queue.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{dbfile}")
    QueueBase.metadata.create_all(engine)

    def visit(vid, tenant, queue, status, age=None, seq=None):
        return QueueVisitRecord(
            id=vid, tenant_id=tenant, queue_id=queue, visit_kind="APPOINTMENT",
            status=status, scheduled_at_utc=NOW-timedelta(days=50),
            arrival_confirmed_at_utc=(
                NOW-timedelta(days=40) if status in {"DONE", "WAITING"} else None
            ),
            waiting_since_utc=(
                NOW-timedelta(days=40) if status in {"DONE", "WAITING"} else None
            ),
            queue_sequence=seq, version=2,
            closed_at_utc=NOW-timedelta(days=age) if age is not None else None,
        )
    with Session(engine) as s:
        for tenant in ("T1", "T2"):
            s.add(QueueTenant(id=tenant, timezone_name="Africa/Casablanca", created_at_utc=NOW))
        s.flush()
        s.add_all([
            QueueLine(id="Q1", tenant_id="T1", queue_key="WAITING", is_active=True),
            QueueLine(id="Q2", tenant_id="T2", queue_key="WAITING", is_active=True),
            QueueResource(id="R1", tenant_id="T1", resource_key="CHAIR", resource_kind="CHAIR", is_active=True),
        ])
        s.flush()
        s.add_all([
            visit("OLD_DONE", "T1", "Q1", "DONE", 31, 1),
            visit("BOUNDARY_NO_SHOW", "T1", "Q1", "NO_SHOW", 30),
            visit("NEW_DONE", "T1", "Q1", "DONE", 29, 2),
            visit("ACTIVE_WAITING", "T1", "Q1", "WAITING", None, 3),
            visit("UNSET_CANCELLED", "T1", "Q1", "CANCELLED"),
            visit("OTHER_TENANT", "T2", "Q2", "NO_SHOW", 99),
        ])
        s.flush()
        s.add(QueueExternalReference(
            id="EXT1", tenant_id="T1", visit_id="OLD_DONE",
            source_system="SYNTH", entity_kind="APPOINTMENT",
            external_id="fake-appointment-1",
        ))
        s.add(QueueVisitResource(tenant_id="T1", visit_id="OLD_DONE", resource_id="R1"))
        s.add(QueueEventRecord(
            id="AUDIT1", tenant_id="T1", visit_ref="OLD_DONE",
            aggregate_version=7, event_type="DONE",
            state_before="CHAIR", state_after="DONE",
            occurred_at_utc=NOW-timedelta(days=31),
            actor_kind="HUMAN", actor_ref="OPERATOR_SYNTH",
        ))
        s.commit()
    engine.dispose()
    # Dedicated header proof: a renamed/copy-pasted clinical SQLite file does
    # not become eligible merely because its path is under a temporary folder.
    with sqlite3.connect(dbfile) as db:
        db.execute(f"PRAGMA application_id={retention.SYNTHETIC_LAB_APPLICATION_ID}")
    return dbfile


def _read(path: Path, query: str, args=()):
    with sqlite3.connect(path) as c:
        c.execute("PRAGMA foreign_keys=ON")
        return c.execute(query, args).fetchall()


def test_30_day_boundary_dryrun_and_atomic_purge_preserve_12_month_audit(lab):
    before = _read(lab, "SELECT id FROM queue_visits ORDER BY id")
    preview = retain_closed_visits_lab(lab, "T1", now=NOW)
    assert preview.eligible_visits == 2
    assert preview.external_references == 1
    assert preview.resource_bindings == 1
    assert preview.event_facts_preserved == 1
    assert preview.executed is False
    assert _read(lab, "SELECT id FROM queue_visits ORDER BY id") == before
    assert not _read(lab, "SELECT name FROM sqlite_master WHERE name='queue_retention_receipts_lab'")

    result = retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert result.eligible_visits == 2 and result.executed
    assert result.external_references == 1 and result.resource_bindings == 1
    assert {x[0] for x in _read(lab, "SELECT id FROM queue_visits")} == {
        "NEW_DONE", "ACTIVE_WAITING", "UNSET_CANCELLED", "OTHER_TENANT",
    }
    assert _read(lab, "SELECT count(*) FROM queue_external_references") == [(0,)]
    assert _read(lab, "SELECT count(*) FROM queue_visit_resources") == [(0,)]
    assert _read(lab, "SELECT visit_ref, actor_ref, event_type FROM queue_event_log") == [
        ("OLD_DONE", "OPERATOR_SYNTH", "DONE"),
    ]
    receipt = _read(
        lab,
        "SELECT tenant_id,visits_removed,external_refs_removed,resource_links_removed "
        "FROM queue_retention_receipts_lab",
    )
    assert receipt == [("T1", 2, 1, 1)]
    # Repeat maintenance cannot delete anything twice, even if same timestamp.
    next_run = retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert next_run.eligible_visits == 0
    assert _read(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_missing_guard_refuses_purge_without_touching_any_visit(lab):
    with sqlite3.connect(lab) as c:
        c.execute("DROP TRIGGER queue_event_log_no_delete")
    with pytest.raises(RetentionLabError, match="QUEUE_EVENT_IMMUTABILITY_REQUIRED"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]
    assert not _read(lab, "SELECT name FROM sqlite_master WHERE name='queue_retention_receipts_lab'")


def test_mid_transaction_failure_rolls_back_deletes_and_receipts(lab, monkeypatch):
    def failure():
        raise RuntimeError("INJECTED_LAB_FAILURE")
    monkeypatch.setattr(retention, "_fault_after_first_delete", failure)
    with pytest.raises(RuntimeError, match="INJECTED_LAB_FAILURE"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]
    assert _read(lab, "SELECT count(*) FROM queue_external_references") == [(1,)]
    assert _read(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]
    assert not _read(lab, "SELECT name FROM sqlite_master WHERE name='queue_retention_receipts_lab'")


def test_existing_qr_receipt_blocks_orphan_and_no_mutation(lab):
    with sqlite3.connect(lab) as c:
        c.execute(
            "CREATE TABLE queue_presence_qr_lab (tenant_id TEXT, visit_id TEXT)"
        )
        c.execute(
            "INSERT INTO queue_presence_qr_lab VALUES('T1','OLD_DONE')"
        )
    with pytest.raises(RetentionLabError, match="QR_REFERENCES_REMAIN"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]
    with sqlite3.connect(lab) as c:
        c.execute("DELETE FROM queue_presence_qr_lab")
    assert retain_closed_visits_lab(lab, "T1", now=NOW, execute=True).eligible_visits == 2


def test_receipts_and_event_history_stay_immutable_after_purge(lab):
    retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    with pytest.raises(sqlite3.IntegrityError, match="RETENTION_RECEIPT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("UPDATE queue_retention_receipts_lab SET visits_removed=999")
    with pytest.raises(sqlite3.IntegrityError, match="RETENTION_RECEIPT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("DELETE FROM queue_retention_receipts_lab")
    with pytest.raises(sqlite3.IntegrityError, match="QUEUE_EVENT_IMMUTABLE"):
        with sqlite3.connect(lab) as c:
            c.execute("DELETE FROM queue_event_log")
    assert _read(lab, "SELECT count(*) FROM queue_event_log") == [(1,)]


def test_fail_closed_on_nonlab_path_naive_clock_other_tenant_or_bad_limit(lab, tmp_path):
    other = tmp_path / "ordinary_prod_name.sqlite"
    other.write_bytes(lab.read_bytes())
    with pytest.raises(RetentionLabError, match="SYNTHETIC_LAB_FILE_REQUIRED"):
        retain_closed_visits_lab(other, "T1", now=NOW, execute=True)
    with pytest.raises(RetentionLabError, match="AWARE_UTC_CLOCK_REQUIRED"):
        retain_closed_visits_lab(lab, "T1", now=NOW.replace(tzinfo=None))
    with pytest.raises(RetentionLabError, match="TENANT_SCOPE_REQUIRED"):
        retain_closed_visits_lab(lab, "UNKNOWN", now=NOW, execute=True)
    with pytest.raises(RetentionLabError, match="MAINTENANCE_ARGUMENT_INVALID"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True, limit=101)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]


def test_existing_cross_tenant_foreign_key_corruption_refuses_purge(lab):
    """An old damaged SQLite file must be investigated, not silently purged."""
    with sqlite3.connect(lab) as c:
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute(
            "INSERT INTO queue_external_references "
            "(id,tenant_id,visit_id,source_system,entity_kind,external_id) "
            "VALUES ('ORPHAN','T1','MISSING_VISIT','SYNTH','APPOINTMENT','broken')"
        )
    with pytest.raises(RetentionLabError, match="QUEUE_FK_INTEGRITY_FAILED"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]
    assert _read(lab, "SELECT count(*) FROM queue_external_references") == [(2,)]
    assert not _read(lab, "SELECT name FROM sqlite_master WHERE name='queue_retention_receipts_lab'")


def test_misnamed_real_like_sqlite_without_explicit_lab_marker_is_refused(lab):
    with sqlite3.connect(lab) as c:
        c.execute("PRAGMA application_id=0")
    with pytest.raises(RetentionLabError, match="SYNTHETIC_LAB_MARKER_REQUIRED"):
        retain_closed_visits_lab(lab, "T1", now=NOW, execute=True)
    assert _read(lab, "SELECT count(*) FROM queue_visits") == [(6,)]
    assert _read(lab, "SELECT count(*) FROM queue_external_references") == [(1,)]
