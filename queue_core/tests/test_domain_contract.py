from datetime import datetime, timedelta, timezone

import pytest

from queue_core.domain import (
    CheckInMethod,
    QueueDomainError,
    QueueEventType,
    QueueVisit,
    VisitKind,
    VisitStatus,
    call_visit,
    check_in,
    mark_no_show,
    move_to_chair,
    record_unlocated_after_call,
    rank_waiting_visits,
    return_to_waiting,
)

UTC = timezone.utc
T0 = datetime(2026, 11, 8, 8, 45, tzinfo=UTC)


def visit(visit_id, kind, status=VisitStatus.PLANNED, scheduled=None, **kwargs):
    return QueueVisit(
        visit_id=visit_id,
        tenant_id=kwargs.pop("tenant_id", "tenant-a"),
        queue_id=kwargs.pop("queue_id", "queue-a"),
        kind=kind,
        status=status,
        scheduled_at=scheduled,
        **kwargs,
    )


def test_checkin_records_arrival_and_waiting_atomically_and_en_route_is_not_presence():
    en_route = visit("a", VisitKind.APPOINTMENT, VisitStatus.EN_ROUTE, T0)
    result = check_in(
        en_route,
        at=T0 + timedelta(minutes=2),
        actor_ref="staff-1",
        method=CheckInMethod.STAFF,
        queue_sequence=1,
        authorized=True,
    )
    assert result.visit.status is VisitStatus.WAITING
    assert [event.event_type for event in result.events] == [
        QueueEventType.ARRIVED,
        QueueEventType.WAITING_ENTERED,
    ]
    assert result.events[0].state_before is VisitStatus.EN_ROUTE
    assert result.events[0].state_after is VisitStatus.EN_ROUTE
    assert result.visit.arrival_confirmed_at == T0 + timedelta(minutes=2)


def test_no_show_only_unarrived_planned_appointment_and_reason_is_required():
    appointment = visit("a", VisitKind.APPOINTMENT, scheduled=T0)
    with pytest.raises(QueueDomainError, match="AUDIT_REASON_REQUIRED"):
        mark_no_show(appointment, at=T0, actor_ref="staff", reason_code="", authorized=True)
    no_show = mark_no_show(
        appointment, at=T0, actor_ref="staff", reason_code="ABSENT", authorized=True
    )
    assert no_show.visit.status is VisitStatus.NO_SHOW
    en_route = visit("c", VisitKind.APPOINTMENT, VisitStatus.EN_ROUTE, T0)
    assert mark_no_show(
        en_route, at=T0, actor_ref="staff", reason_code="ABSENT", authorized=True
    ).visit.status is VisitStatus.NO_SHOW
    arrived = visit(
        "b", VisitKind.APPOINTMENT, VisitStatus.WAITING, T0,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
    )
    with pytest.raises(QueueDomainError, match="NO_SHOW_STATE_CONFLICT"):
        mark_no_show(arrived, at=T0, actor_ref="staff", reason_code="ABSENT", authorized=True)


def test_unlocated_after_call_is_audited_event_without_state_change():
    called = visit(
        "a", VisitKind.WALK_IN, VisitStatus.CALLED,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
    )
    result = record_unlocated_after_call(
        called, at=T0, actor_ref="staff", reason_code="NOT_FOUND", authorized=True
    )
    assert result.visit.status is VisitStatus.CALLED
    assert result.events[0].event_type is QueueEventType.UNLOCATED_AFTER_CALL
    assert result.events[0].reason_code == "NOT_FOUND"


def test_override_permission_does_not_force_override_when_calling_in_order():
    waiting = visit(
        "a", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
    )
    result = call_visit(
        waiting, at=T0, actor_ref="staff", authorized=True, can_override=True
    )
    assert [event.event_type for event in result.events] == [QueueEventType.CALLED]


def test_chair_return_plan_releases_resource_and_requeues_with_new_sequence():
    waiting = visit(
        "a", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1, resource_ids=frozenset({"chair-1"}),
    )
    called = call_visit(waiting, at=T0, actor_ref="staff", authorized=True)
    chair = move_to_chair(
        called.visit, at=T0, actor_ref="staff", resource_id="chair-1",
        resource_available=True, authorized=True,
    )
    result = return_to_waiting(
        chair.visit, at=T0 + timedelta(minutes=5), actor_ref="staff",
        reason_code="CHAIR_UNAVAILABLE", queue_sequence=2, authorized=True,
    )
    assert result.released_resource_ids == ("chair-1",)
    assert result.visit.status is VisitStatus.WAITING
    assert result.visit.queue_sequence == 2
    assert result.visit.held_resource_id is None
    assert [event.event_type for event in result.events] == [
        QueueEventType.RESOURCE_RELEASED,
        QueueEventType.RETURNED_TO_WAITING,
    ]
    with pytest.raises(QueueDomainError, match="QUEUE_SEQUENCE_INVALID"):
        return_to_waiting(
            chair.visit, at=T0 + timedelta(minutes=5), actor_ref="staff",
            reason_code="CHAIR_UNAVAILABLE", queue_sequence=1, authorized=True,
        )


def test_dynamic_order_matches_g1_oracle_and_never_crosses_tenant_or_resource():
    a = visit("A", VisitKind.APPOINTMENT, VisitStatus.WAITING,
              datetime(2026, 11, 8, 9, 0, tzinfo=UTC), arrival_confirmed_at=T0,
              waiting_since=T0, queue_sequence=1, resource_ids=frozenset({"r1"}))
    b = visit("B", VisitKind.APPOINTMENT, VisitStatus.WAITING,
              datetime(2026, 11, 8, 9, 0, tzinfo=UTC), arrival_confirmed_at=T0,
              waiting_since=datetime(2026, 11, 8, 9, 5, tzinfo=UTC), queue_sequence=2,
              resource_ids=frozenset({"r1"}))
    w = visit("W", VisitKind.WALK_IN, VisitStatus.WAITING,
              arrival_confirmed_at=T0, waiting_since=datetime(2026, 11, 8, 9, 2, tzinfo=UTC),
              queue_sequence=3, resource_ids=frozenset({"r1"}))
    c = visit("C", VisitKind.APPOINTMENT, VisitStatus.WAITING,
              datetime(2026, 11, 8, 9, 10, tzinfo=UTC), arrival_confirmed_at=T0,
              waiting_since=T0, queue_sequence=4, resource_ids=frozenset({"r1"}))
    other_tenant = visit("X", VisitKind.WALK_IN, VisitStatus.WAITING,
              arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
              resource_ids=frozenset({"r1"}), tenant_id="tenant-b")
    other_resource = visit("Y", VisitKind.WALK_IN, VisitStatus.WAITING,
              arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
              resource_ids=frozenset({"r2"}))
    common = dict(tenant_id="tenant-a", queue_id="queue-a", resource_id="r1",
                  available_resource_ids=frozenset({"r1"}), tenant_timezone="Africa/Casablanca")
    at_0905 = rank_waiting_visits([a, b, w, c, other_tenant, other_resource],
                                  evaluated_at=datetime(2026, 11, 8, 9, 5, tzinfo=UTC), **common)
    assert [item.visit.visit_id for item in at_0905] == ["A", "B", "W"]
    at_0910 = rank_waiting_visits([a, b, w, c],
                                  evaluated_at=datetime(2026, 11, 8, 9, 10, tzinfo=UTC), **common)
    assert [item.visit.visit_id for item in at_0910] == ["A", "B", "C", "W"]
