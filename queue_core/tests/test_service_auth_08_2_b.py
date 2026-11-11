"""LOT08.2-B local service FUE-I: real SQLite persistence, authorization, audit.

No patient data, network endpoints, clinical DB, real credentials or devices.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from queue_core.domain import QueueDomainError, VisitStatus
from queue_core.persistence.base import QueueBase
from queue_core.persistence.models import (
    QueueTenant, QueueLine, QueueResource, QueueVisitRecord,
    QueueVisitResource, QueueEventRecord,
)
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import AuthorizationError, Permission as P, Role
from queue_core.service.authorized_queue import AuthorizedLocalQueue, HumanCommand


PASS1 = "SyntheticAdminPassword!!2026"
PASS2 = "SyntheticStaffPassword!!2026"
NOW = datetime(2030, 2, 1, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def local(tmp_path):
    auth = LocalIdentityStore(
        tmp_path / "auth-synthetic.sqlite",
        local_guard=lambda: None, clock=lambda: 1_800_000_000,
    )
    challenge = auth.begin_bootstrap()
    auth.enroll_first_admin(challenge, "testadmin", PASS1)
    admin = auth.login("testadmin", PASS1)
    operators = LocalOperatorStore(auth, clock=lambda: 1_800_000_000)
    operators.bind_first_admin(first_admin_session=admin, tenant_id="T1")
    rec = operators.create_operator(
        admin, "reception1", PASS2, Role.RECEPTION, queue_ids=("Q1",),
    )
    staff = operators.create_operator(
        admin, "chairman1", PASS2, Role.STAFF, queue_ids=("Q1",),
        resource_ids=("R1",), grants=(P.QUEUE_CHAIR, P.QUEUE_DONE),
    )
    reception = operators.login_operator("T1", "reception1", PASS2)
    worker = operators.login_operator("T1", "chairman1", PASS2)
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'queue-synthetic.sqlite'}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([
            QueueTenant(id="T1", timezone_name="Africa/Casablanca", created_at_utc=NOW),
            QueueTenant(id="T2", timezone_name="Africa/Casablanca", created_at_utc=NOW),
            QueueLine(id="Q1", tenant_id="T1", queue_key="LAB1", is_active=True),
            QueueLine(id="Q2", tenant_id="T1", queue_key="LAB2", is_active=True),
            QueueLine(id="Q3", tenant_id="T2", queue_key="LAB3", is_active=True),
            QueueResource(id="R1", tenant_id="T1", resource_key="CHAIR1",
                          resource_kind="CHAIR", is_active=True),
            QueueResource(id="R2", tenant_id="T2", resource_key="CHAIR2",
                          resource_kind="CHAIR", is_active=True),
        ])
        s.flush()
        s.add_all([
            QueueVisitRecord(
                id="V1", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="PLANNED",
                scheduled_at_utc=NOW-timedelta(days=1), version=0,
            ),
            QueueVisitRecord(
                id="V2", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="PLANNED",
                scheduled_at_utc=NOW-timedelta(hours=2), version=0,
            ),
            QueueVisitRecord(
                id="V3", tenant_id="T2", queue_id="Q3",
                visit_kind="APPOINTMENT", status="PLANNED",
                scheduled_at_utc=NOW-timedelta(days=1), version=0,
            ),
            QueueVisitRecord(
                id="V4", tenant_id="T1", queue_id="Q2",
                visit_kind="APPOINTMENT", status="PLANNED",
                scheduled_at_utc=NOW-timedelta(days=1), version=0,
            ),
            QueueVisitResource(tenant_id="T1", visit_id="V1", resource_id="R1"),
            QueueVisitResource(tenant_id="T1", visit_id="V2", resource_id="R1"),
            QueueVisitResource(tenant_id="T2", visit_id="V3", resource_id="R2"),
        ])
        s.commit()
    service = AuthorizedLocalQueue(operators, engine, clock=lambda: NOW)
    return auth, operators, admin, reception, worker, rec, staff, service, engine


def denied(fn, code="AUTHZ_DENIED", status=403):
    with pytest.raises(AuthorizationError) as exc:
        fn()
    assert exc.value.code == code and exc.value.status_code == status


def test_fue_i_real_checkin_call_chair_done_events_and_replay(local):
    _, _, _, reception, worker, _, _, svc, engine = local
    v = svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    assert v.status == "WAITING" and v.version == 2 and v.queue_sequence == 1
    denied(lambda: svc.perform(reception, HumanCommand.CALL, "V1",
                               expected_version=2, resource_id="R1"))
    call = svc.perform(worker, HumanCommand.CALL, "V1",
                       expected_version=2, resource_id="R1")
    assert call.status == "CALLED" and call.version == 3
    chair = svc.perform(worker, HumanCommand.CHAIR, "V1",
                        expected_version=3, resource_id="R1")
    assert chair.status == "CHAIR" and chair.version == 5
    done = svc.perform(worker, HumanCommand.DONE, "V1", expected_version=5)
    assert done.status == "DONE" and done.version == 7
    events = svc.replay_events(worker, "Q1")
    assert len(events) == 7
    assert set(x.aggregate_version for x in events) == set(range(1, 8))
    page = svc.replay_events(worker, "Q1", limit=3)
    assert len(page) == 3
    # Snapshot should be minimized and scoped (no user/patient info).
    snapshot = svc.queue_snapshot(reception, "Q1")
    assert {item.id: item.status for item in snapshot} == {"V1": "DONE", "V2": "PLANNED"}
    with Session(engine) as session:
        record = session.get(QueueVisitRecord, "V1")
        assert record.status == "DONE" and record.held_resource_id is None
        assert record.version == 7
        assert session.scalar(select(QueueEventRecord).where(
            QueueEventRecord.visit_ref == "V1").limit(1)) is not None


def test_service_attacks_tenant_queue_resource_cursor_and_role(local):
    _, _, admin, rec, worker, _, _, svc, engine = local
    denied(lambda: svc.perform(rec, HumanCommand.CHECK_IN, "V3", expected_version=0))
    denied(lambda: svc.perform(rec, HumanCommand.CHECK_IN, "V4", expected_version=0))
    denied(lambda: svc.perform(worker, HumanCommand.CALL, "V3",
                               expected_version=0, resource_id="R2"))
    denied(lambda: svc.perform(worker, HumanCommand.CALL, "V1",
                               expected_version=0, resource_id="R2"))
    denied(lambda: svc.queue_snapshot(admin, "Q1"))
    denied(lambda: svc.queue_snapshot(rec, "Q3"))
    denied(lambda: svc.replay_events(rec, "Q3"))
    denied(lambda: svc.perform("INVALID", HumanCommand.CHECK_IN, "V1",
                               expected_version=0), "AUTH_REQUIRED", 401)
    # Invalid command cannot be used to bypass role permissions.
    denied(lambda: svc.perform(rec, "queue.override", "V1", expected_version=0))
    with Session(engine) as s:
        assert s.get(QueueVisitRecord, "V1").version == 0
        assert not s.scalars(select(QueueEventRecord)).all()


def test_revoke_before_command_stream_snapshot_and_replay(local):
    _, operators, admin, rec, worker, rec_id, staff_id, svc, engine = local
    svc.perform(rec, HumanCommand.CHECK_IN, "V1", expected_version=0)
    events = svc.replay_events(worker, "Q1")
    assert len(events) == 2
    cursor = events[0].id
    assert svc.replay_events(worker, "Q1", after_event_id=cursor)
    operators.replace_rights(admin, staff_id, queue_ids=("Q2",))
    denied(lambda: svc.replay_events(worker, "Q1"), "AUTH_REQUIRED", 401)
    denied(lambda: svc.queue_snapshot(worker, "Q1"), "AUTH_REQUIRED", 401)
    denied(lambda: svc.perform(worker, HumanCommand.CALL, "V1",
                               expected_version=2, resource_id="R1"),
           "AUTH_REQUIRED", 401)
    fresh = operators.login_operator("T1", "chairman1", PASS2)
    denied(lambda: svc.replay_events(fresh, "Q1"))
    denied(lambda: svc.perform(fresh, HumanCommand.CALL, "V1",
                               expected_version=2, resource_id="R1"))
    operators.disable_operator(admin, rec_id)
    denied(lambda: svc.queue_snapshot(rec, "Q1"), "AUTH_REQUIRED", 401)
    with Session(engine) as s:
        assert s.get(QueueVisitRecord, "V1").version == 2


def test_stale_version_wrong_actor_no_show_requires_grant_and_reason(local):
    _, operators, admin, rec, worker, rec_id, _, svc, engine = local
    with pytest.raises(QueueDomainError, match="VERSION_CONFLICT"):
        svc.perform(rec, HumanCommand.CHECK_IN, "V1", expected_version=3)
    denied(lambda: svc.perform(worker, HumanCommand.NO_SHOW, "V2",
                               expected_version=0, reason_code="MISSED"))
    denied(lambda: svc.perform(rec, HumanCommand.NO_SHOW, "V2",
                               expected_version=0, reason_code="MISSED"))
    operators.replace_rights(admin, rec_id, grants=(P.QUEUE_NO_SHOW,))
    new_rec = operators.login_operator("T1", "reception1", PASS2)
    with pytest.raises(QueueDomainError, match="AUDIT_REASON_CODE_INVALID"):
        svc.perform(new_rec, HumanCommand.NO_SHOW, "V2",
                    expected_version=0, reason_code="patient was late")
    v = svc.perform(new_rec, HumanCommand.NO_SHOW, "V2",
                    expected_version=0, reason_code="MISSED")
    assert v.status == "NO_SHOW" and v.version == 1
    with Session(engine) as s:
        assert s.get(QueueVisitRecord, "V2").status == "NO_SHOW"


def test_queue_db_and_identity_db_must_be_distinct_and_existing(local):
    _, operators, _, _, _, _, _, _, engine = local
    with pytest.raises(ValueError, match="AUTH_QUEUE_DATABASES_MUST_BE_SEPARATE"):
        bad = create_engine(f"sqlite+pysqlite:///{operators.auth.path}")
        try:
            AuthorizedLocalQueue(operators, bad)
        finally:
            bad.dispose()
    with pytest.raises(ValueError, match="PERSISTENT_QUEUE_SQLITE_REQUIRED"):
        AuthorizedLocalQueue(operators, create_engine("sqlite+pysqlite:///:memory:"))


def test_resource_is_stored_server_side_not_supplied_by_identity(local):
    _, _, _, reception, worker, _, _, svc, engine = local
    svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    # Client cannot inject unbound room, even if present under same tenant.
    with Session(engine) as db:
        db.add(QueueResource(id="RX", tenant_id="T1", resource_key="UNBOUND",
                             resource_kind="CHAIR", is_active=True))
        db.commit()
    denied(lambda: svc.perform(worker, HumanCommand.CALL, "V1",
                               expected_version=2, resource_id="RX"))
    good = svc.perform(worker, HumanCommand.CALL, "V1",
                       expected_version=2, resource_id="R1")
    assert good.status == "CALLED"


def test_queue_event_cursor_from_another_queue_is_403(local):
    _, _, _, reception, _, _, _, svc, engine = local
    svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    with Session(engine) as s:
        foreign = QueueEventRecord(
            id="otherevent", tenant_id="T2", visit_ref="V3", aggregate_version=1,
            event_type="NO_SHOW", state_before="PLANNED", state_after="NO_SHOW",
            occurred_at_utc=NOW, actor_kind="HUMAN", actor_ref="fictional",
            reason_code="MISSED",
        )
        s.add(foreign)
        s.commit()
    denied(lambda: svc.replay_events(reception, "Q1", after_event_id="otherevent"))
    assert len(svc.replay_events(reception, "Q1")) == 2


def test_failure_rolls_back_domain_events_and_status(local):
    _, _, _, reception, worker, _, _, svc, engine = local
    svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    with pytest.raises(QueueDomainError, match="RECALL_STATE_CONFLICT"):
        svc.perform(worker, HumanCommand.RECALL, "V1",
                    expected_version=2, resource_id="R1")
    with Session(engine) as s:
        row = s.get(QueueVisitRecord, "V1")
        assert row.version == 2 and row.status == "WAITING"
        assert len(s.scalars(select(QueueEventRecord)).all()) == 2


def test_real_cursor_pagination_monotonic_versions_even_same_timestamp(local):
    _, _, _, reception, worker, _, _, svc, _ = local
    svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    svc.perform(worker, HumanCommand.CALL, "V1", expected_version=2, resource_id="R1")
    svc.perform(worker, HumanCommand.CHAIR, "V1", expected_version=3, resource_id="R1")
    svc.perform(worker, HumanCommand.DONE, "V1", expected_version=5)
    all_events = []
    cursor = None
    while True:
        page = svc.replay_events(worker, "Q1", after_event_id=cursor, limit=2)
        if not page:
            break
        all_events.extend(page)
        cursor = page[-1].id
    assert [e.aggregate_version for e in all_events] == list(range(1, 8))
    assert len({e.id for e in all_events}) == 7


def test_override_requires_grant_and_stores_reason_event(local):
    _, operators, admin, rec, worker, _, staff_id, svc, engine = local
    svc.perform(rec, HumanCommand.CHECK_IN, "V1", expected_version=0)
    svc.perform(rec, HumanCommand.CHECK_IN, "V2", expected_version=0)
    denied(lambda: svc.perform(
        worker, HumanCommand.CALL, "V2", expected_version=2,
        resource_id="R1", reason_code="STAFF_DELAY",
    ))
    operators.replace_rights(admin, staff_id, grants=(
        P.QUEUE_CHAIR, P.QUEUE_DONE, P.QUEUE_OVERRIDE,
    ))
    new_worker = operators.login_operator("T1", "chairman1", PASS2)
    called = svc.perform(
        new_worker, HumanCommand.CALL, "V2", expected_version=2,
        resource_id="R1", reason_code="STAFF_DELAY",
    )
    assert called.status == "CALLED" and called.version == 4
    with Session(engine) as s:
        event = s.scalar(select(QueueEventRecord).where(
            QueueEventRecord.visit_ref == "V2",
            QueueEventRecord.event_type == "ORDER_OVERRIDE",
        ))
        assert event.reason_code == "STAFF_DELAY"
        assert event.actor_kind == "HUMAN"


def test_concurrent_revoke_cannot_commit_before_in_flight_authorized_command(local, monkeypatch):
    from concurrent.futures import TimeoutError
    _, operators, admin, rec, worker, _, staff_id, svc, engine = local
    svc.perform(rec, HumanCommand.CHECK_IN, "V1", expected_version=0)
    reached_commit = Event()
    release_commit = Event()
    revocation_attempted = Event()
    original = svc._commit_plan

    def suspended(db, row, plan, now):
        reached_commit.set()
        assert release_commit.wait(timeout=10)
        original(db, row, plan, now)

    monkeypatch.setattr(svc, "_commit_plan", suspended)
    with ThreadPoolExecutor(max_workers=2) as pool:
        command_future = pool.submit(
            svc.perform, worker, HumanCommand.CALL, "V1",
            expected_version=2, resource_id="R1",
        )
        assert reached_commit.wait(timeout=8)
        def revoke():
            revocation_attempted.set()
            operators.replace_rights(admin, staff_id, queue_ids=())
        revoke_future = pool.submit(revoke)
        assert revocation_attempted.wait(timeout=8)
        # The A+B SQLite BEGIN IMMEDIATE lock must block revoke until the
        # Queue visit/events commit; revocation cannot win while already authorized.
        with pytest.raises(TimeoutError):
            revoke_future.result(timeout=0.2)
        release_commit.set()
        assert command_future.result(timeout=10).status == "CALLED"
        assert revoke_future.result(timeout=10) is None
    denied(lambda: svc.replay_events(worker, "Q1"), "AUTH_REQUIRED", 401)
    with Session(engine) as s:
        row = s.get(QueueVisitRecord, "V1")
        assert row.status == "CALLED" and row.version == 3
        assert len(s.scalars(select(QueueEventRecord).where(
            QueueEventRecord.visit_ref == "V1",
        )).all()) == 3


def test_08_3_atomic_plan_guard_rejects_tampered_event_without_sql_write(local, monkeypatch):
    """Real protected SQLite/auth transaction: malformed domain plan = zero writes."""
    from dataclasses import replace
    from sqlalchemy import func
    from queue_core.service import authorized_queue as command_module

    _, _, _, reception, _, _, _, svc, engine = local
    real_check_in = command_module.check_in

    def poisoned_check_in(*args, **kwargs):
        valid = real_check_in(*args, **kwargs)
        corrupted = replace(valid.events[1], tenant_id="CROSS_TENANT")
        return replace(valid, events=(valid.events[0], corrupted))

    monkeypatch.setattr(command_module, "check_in", poisoned_check_in)
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_EVENT_MISMATCH"):
        svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)

    with Session(engine) as session:
        row = session.get(QueueVisitRecord, "V1")
        assert row.status == "PLANNED" and row.version == 0
        assert row.arrival_confirmed_at_utc is None
        assert session.scalar(select(func.count()).select_from(QueueEventRecord)) == 0

    # A later valid command must still succeed after the abort.
    monkeypatch.setattr(command_module, "check_in", real_check_in)
    valid = svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    assert valid.status == "WAITING" and valid.version == 2
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(QueueEventRecord)) == 2


def test_08_3_rollback_after_flush_and_restart_has_no_partial_arrival(local, monkeypatch):
    """Inject failure after SQL changes are flushed, then reopen physical SQLite."""
    from sqlalchemy import func
    from queue_core.service import authorized_queue as command_module

    _, _, _, reception, _, _, _, svc, engine = local
    original_commit = svc._commit_plan

    def crash_after_flush(db, row, plan, now):
        original_commit(db, row, plan, now)
        db.flush()  # State and both events reached SQLite, not COMMIT.
        raise RuntimeError("SYNTHETIC_CRASH_BEFORE_COMMIT")

    monkeypatch.setattr(svc, "_commit_plan", crash_after_flush)
    with pytest.raises(RuntimeError, match="SYNTHETIC_CRASH_BEFORE_COMMIT"):
        svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)

    # A separate engine/connection tests the persisted view after the abort.
    recovery_engine = create_engine(engine.url)
    try:
        with Session(recovery_engine) as s:
            row = s.get(QueueVisitRecord, "V1")
            assert row.status == "PLANNED" and row.version == 0
            assert row.arrival_confirmed_at_utc is None
            assert s.scalar(select(func.count()).select_from(QueueEventRecord)) == 0
    finally:
        recovery_engine.dispose()

    monkeypatch.setattr(svc, "_commit_plan", original_commit)
    value = svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    assert value.status == "WAITING" and value.version == 2
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(QueueEventRecord)) == 2


def test_08_3_two_concurrent_commands_cannot_create_duplicate_arrival(local):
    """Competing local sessions: exactly one version-0 check-in wins."""
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import func

    _, _, _, reception, _, _, _, svc, engine = local

    def check_in_once(_i):
        try:
            value = svc.perform(reception, HumanCommand.CHECK_IN, "V1",
                                expected_version=0)
            return value.status
        except QueueDomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(check_in_once, (0, 1)))
    assert sorted(outcomes) == ["VERSION_CONFLICT", "WAITING"]
    with Session(engine) as s:
        row = s.get(QueueVisitRecord, "V1")
        assert row.status == "WAITING" and row.version == 2
        assert s.scalar(select(func.count()).select_from(QueueEventRecord)) == 2


def test_08_3_real_os_process_kill_before_commit_rolls_back_and_recovers(local, tmp_path):
    """OS-terminated separate Python process; rollback verified after real exit.

    This tests an isolated SQLite QUEUE and auth DB with synthetic records, not
    an application kill in a real dental cabinet or any power-loss claim.
    """
    import os
    from pathlib import Path
    import subprocess
    import sys
    import time

    from sqlalchemy import func

    _, _, _, reception, _, _, _, svc, engine = local
    signal_file = tmp_path / "synthetic-child-flushed.marker"
    child_code = r'''
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.service.authorized_queue import AuthorizedLocalQueue, HumanCommand

auth = LocalIdentityStore(
    os.environ["DC_SYNTH_AUTH_PATH"],
    clock=lambda: 1_800_000_000,
    local_guard=lambda: None,
)
operators = LocalOperatorStore(auth, clock=lambda: 1_800_000_000)
engine = create_engine("sqlite+pysqlite:///" + os.environ["DC_SYNTH_QUEUE_PATH"])
service = AuthorizedLocalQueue(
    operators, engine,
    clock=lambda: datetime(2030, 2, 1, 10, tzinfo=timezone.utc),
)
original = service._commit_plan

def flushed_and_blocked(db, row, plan, now):
    original(db, row, plan, now)
    db.flush()
    Path(os.environ["DC_SYNTH_FLUSH_MARKER"]).write_text("AFTER_SQL_FLUSH_BEFORE_COMMIT")
    time.sleep(120)  # Parent will terminate process; no exit or normal rollback.

service._commit_plan = flushed_and_blocked
service.perform(
    os.environ["DC_SYNTH_RECEPTION_BEARER"],
    HumanCommand.CHECK_IN, "V1", expected_version=0,
)
'''
    child_env = os.environ.copy()
    child_env.update({
        "DC_SYNTH_AUTH_PATH": str(svc._operators.auth.path),
        "DC_SYNTH_QUEUE_PATH": str(engine.url.database),
        "DC_SYNTH_FLUSH_MARKER": str(signal_file),
        "DC_SYNTH_RECEPTION_BEARER": reception,
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    repository_root = Path(__file__).resolve().parents[2]
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", child_code],
        cwd=repository_root, env=child_env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 20
        while not signal_file.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert signal_file.is_file(), (
            "The independent process did not reach SQL flush: "
            + (process.stderr.read(1600).decode(errors="replace")
               if process.poll() is not None else "timed out")
        )
        assert signal_file.read_text() == "AFTER_SQL_FLUSH_BEFORE_COMMIT"
        assert process.poll() is None, "Child committed/exited before forced termination"
        process.kill()  # Real SIGKILL on the GitHub Ubuntu runner.
        assert process.wait(timeout=10) != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        process.stdout.close()
        process.stderr.close()

    # Fresh SQLite engine after process death; no state change, no event leak.
    recovered_engine = create_engine(engine.url)
    try:
        with Session(recovered_engine) as session:
            visit = session.get(QueueVisitRecord, "V1")
            assert visit.status == "PLANNED"
            assert visit.version == 0
            assert visit.arrival_confirmed_at_utc is None
            assert session.scalar(select(func.count()).select_from(QueueEventRecord)) == 0
    finally:
        recovered_engine.dispose()

    # The same application service must resume without a manual DB fix.
    result = svc.perform(reception, HumanCommand.CHECK_IN, "V1", expected_version=0)
    assert result.status == "WAITING" and result.version == 2
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(QueueEventRecord)) == 2


@pytest.mark.parametrize("missing_guard", [
    "queue_event_log_no_update", "queue_event_log_no_delete",
])
def test_08_3_legacy_event_ledger_missing_guard_refuses_new_service(
    local, missing_guard,
):
    """Read-only startup gate refuses an old/misconfigured file, never auto-migrates."""
    _, operators, _, _, _, _, _, _, engine = local
    # Simulate an older SQLite file, using only the synthetic fixture.
    with engine.begin() as connection:
        connection.exec_driver_sql(f"DROP TRIGGER {missing_guard}")
    with pytest.raises(ValueError, match="QUEUE_EVENT_IMMUTABILITY_REQUIRED"):
        AuthorizedLocalQueue(operators, engine)
    # Existing visit data remains untouched by the failed initialization.
    with Session(engine) as session:
        row = session.get(QueueVisitRecord, "V1")
        assert row.status == "PLANNED" and row.version == 0
        assert not session.scalars(select(QueueEventRecord)).all()
