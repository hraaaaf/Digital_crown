"""04.8-C virtual outbox: real SQL transaction and one-shot crash fencing.

No real docs, devices or production DB. Exactly one synthetic identity can
enter this lab. PostgreSQL multiprocess proof is tested in a separate job.
"""
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, event, insert, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool
import pytest

from backend.services.station_print_held_claims_lab import SCHEMA, claims, claim_events
from backend.services.station_print_virtual_outbox_lab_v15 import (
    SYNTHETIC_TENANT, SYNTHETIC_DELIVERY_KEY,
    SYNTHETIC_PRINTER, virtual_outbox,
    VirtualLabDuplicate, VirtualLabRejected,
    reserve_synthetic_outbox, fence_virtual_attempt, read_synthetic_outbox,
)


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB", "1")
    db = create_engine(
        "sqlite+pysqlite:///" + str(tmp_path / "virtual-outbox.sqlite"),
        poolclass=QueuePool, connect_args={"check_same_thread": False, "timeout": 15},
    )
    @event.listens_for(db, "connect")
    def fk(c, _):
        c.execute("PRAGMA foreign_keys=ON")
    SCHEMA.create_all(db)
    with db.begin() as c:
        c.execute(insert(SCHEMA.tables["users"]).values(id=10))
    yield db
    db.dispose()


def snapshot(db):
    with db.connect() as conn:
        jobs = conn.execute(select(claims)).mappings().all()
        events = conn.execute(
            select(claim_events.c.revision, claim_events.c.transition)
            .order_by(claim_events.c.revision)
        ).all()
        out = conn.execute(select(virtual_outbox)).mappings().all()
    return jobs, events, out


def test_transactional_reservation_is_held_and_single_destination(engine):
    reserved = reserve_synthetic_outbox(engine)
    assert (reserved.tenant_id, reserved.delivery_key, reserved.printer_id) == (
        SYNTHETIC_TENANT, SYNTHETIC_DELIVERY_KEY, SYNTHETIC_PRINTER,
    )
    assert (reserved.state, reserved.attempts) == ("reserved", 0)
    jobs, events, out = snapshot(engine)
    assert len(jobs) == len(out) == 1
    assert (jobs[0]["state"], jobs[0]["revision"]) == ("held", 1)
    assert events == [(1, "held_reserved")]
    with pytest.raises(VirtualLabDuplicate):
        reserve_synthetic_outbox(engine)
    assert snapshot(engine)[1] == events


def test_worker_fences_attempt_before_external_spool_and_never_retries(engine):
    reserve_synthetic_outbox(engine)
    ticket = fence_virtual_attempt(engine)
    assert (ticket.state, ticket.attempts) == ("attempted", 1)
    jobs, events, out = snapshot(engine)
    assert (jobs[0]["state"], jobs[0]["revision"]) == ("uncertain", 2)
    assert events == [(1, "held_reserved"), (2, "marked_uncertain")]
    assert (out[0]["state"], out[0]["attempts"]) == ("attempted", 1)
    with pytest.raises(VirtualLabRejected, match="ALREADY_ATTEMPTED"):
        fence_virtual_attempt(engine)
    with pytest.raises(VirtualLabDuplicate):
        reserve_synthetic_outbox(engine)


def test_simulated_crash_before_dispatch_leaves_irreversible_uncertain(engine):
    reserve_synthetic_outbox(engine)
    ticket = fence_virtual_attempt(engine)
    engine.dispose()  # worker exited without spooling or committing "printed"
    assert read_synthetic_outbox(engine) == ticket
    with pytest.raises(VirtualLabRejected):
        fence_virtual_attempt(engine)
    assert snapshot(engine)[1] == [(1, "held_reserved"), (2, "marked_uncertain")]


def test_two_worker_threads_only_one_can_claim_the_outbox(engine):
    reserve_synthetic_outbox(engine)
    def worker(_):
        try:
            return fence_virtual_attempt(engine)
        except VirtualLabRejected:
            return "denied"
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(worker, (1, 2)))
    assert sum(x != "denied" for x in results) == 1, results
    assert results.count("denied") == 1
    assert len(snapshot(engine)[1]) == 2


def test_audit_write_failure_rolls_back_before_any_ticket(engine):
    reserve_synthetic_outbox(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE station_print_claim_events")
    with pytest.raises(OperationalError):
        fence_virtual_attempt(engine)
    with engine.connect() as conn:
        assert conn.execute(select(claims.c.state)).scalar_one() == "held"
        assert conn.execute(select(virtual_outbox.c.state)).scalar_one() == "reserved"


def test_reservation_failure_rolls_back_all_three_tables(engine):
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE station_print_virtual_outbox_lab")
    with pytest.raises(OperationalError):
        reserve_synthetic_outbox(engine)
    with engine.connect() as conn:
        assert conn.execute(select(claims)).all() == []
        assert conn.execute(select(claim_events)).all() == []


@pytest.mark.parametrize("key,value", [
    ("GITHUB_ACTIONS", "false"), ("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB", "0"),
])
def test_no_lab_flag_means_no_reservation(engine, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(VirtualLabRejected, match="LAB_ONLY"):
        reserve_synthetic_outbox(engine)
    with pytest.raises(VirtualLabRejected, match="LAB_ONLY"):
        fence_virtual_attempt(engine)
    assert len(snapshot(engine)[0]) == 0


def test_no_PHI_and_no_fake_success_column_in_virtual_outbox():
    names = {c.name for c in virtual_outbox.columns}
    assert names == {
        "tenant_id", "delivery_key", "printer_id", "state", "attempts",
        "created_at", "updated_at",
    }
    assert not names.intersection({
        "patient_id", "patient_name", "document_bytes", "session_id",
        "pdf", "raw_path", "delivery_confirmed", "spool_completed",
    })
    assert virtual_outbox.name.endswith("_lab")
