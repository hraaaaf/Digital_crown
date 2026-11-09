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
