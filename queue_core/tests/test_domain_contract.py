from datetime import datetime, timedelta, timezone

import pytest

from queue_core.domain import (
    ActorKind,
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
    complete_visit,
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
        mark_no_show(appointment, at=T0, actor_ref="staff", actor_kind=ActorKind.HUMAN, reason_code="", authorized=True)
    no_show = mark_no_show(
        appointment, at=T0, actor_ref="staff", actor_kind=ActorKind.HUMAN, reason_code="ABSENT", authorized=True
    )
    assert no_show.visit.status is VisitStatus.NO_SHOW
    en_route = visit("c", VisitKind.APPOINTMENT, VisitStatus.EN_ROUTE, T0)
    assert mark_no_show(
        en_route, at=T0, actor_ref="staff", actor_kind=ActorKind.HUMAN, reason_code="ABSENT", authorized=True
    ).visit.status is VisitStatus.NO_SHOW
    arrived = visit(
        "b", VisitKind.APPOINTMENT, VisitStatus.WAITING, T0,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
    )
    with pytest.raises(QueueDomainError, match="NO_SHOW_STATE_CONFLICT"):
        mark_no_show(arrived, at=T0, actor_ref="staff", actor_kind=ActorKind.HUMAN, reason_code="ABSENT", authorized=True)


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
        resource_ids=frozenset({"chair-1"}),
    )
    result = call_visit(
        waiting, at=T0, actor_ref="staff", authorized=True, can_override=True,
        candidates=[waiting], resource_id="chair-1",
        available_resource_ids=frozenset({"chair-1"}), tenant_timezone="Africa/Casablanca",
    )
    assert [event.event_type for event in result.events] == [QueueEventType.CALLED]


def test_chair_return_plan_releases_resource_and_requeues_with_new_sequence():
    waiting = visit(
        "a", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1, resource_ids=frozenset({"chair-1"}),
    )
    called = call_visit(
        waiting, at=T0, actor_ref="staff", authorized=True,
        candidates=[waiting], resource_id="chair-1",
        available_resource_ids=frozenset({"chair-1"}), tenant_timezone="Africa/Casablanca",
    )
    chair = move_to_chair(
        called.visit, at=T0, actor_ref="staff", resource_id="chair-1",
        resource_available=True, authorized=True,
    )
    assert chair.events[0].resource_id == "chair-1"
    completed = complete_visit(
        chair.visit, at=T0 + timedelta(minutes=2), actor_ref="staff", authorized=True,
    )
    assert completed.events[0].resource_id == "chair-1"
    assert completed.visit.status is VisitStatus.DONE
    result = return_to_waiting(
        chair.visit, at=T0 + timedelta(minutes=5), actor_ref="staff",
        reason_code="CHAIR_UNAVAILABLE", queue_sequence=2, authorized=True,
    )
    assert result.released_resource_ids == ("chair-1",)
    assert result.events[0].resource_id == "chair-1"
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
              datetime(2026, 11, 8, 9, 0, tzinfo=UTC),
              arrival_confirmed_at=datetime(2026, 11, 8, 9, 5, tzinfo=UTC),
              waiting_since=datetime(2026, 11, 8, 9, 5, tzinfo=UTC), queue_sequence=2,
              resource_ids=frozenset({"r1"}))
    w = visit("W", VisitKind.WALK_IN, VisitStatus.WAITING,
              arrival_confirmed_at=datetime(2026, 11, 8, 9, 2, tzinfo=UTC),
              waiting_since=datetime(2026, 11, 8, 9, 2, tzinfo=UTC),
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


def test_call_refuses_out_of_order_walkin_without_explicit_audited_override():
    at = datetime(2026, 11, 8, 9, 5, tzinfo=UTC)
    appointment = visit(
        "A", VisitKind.APPOINTMENT, VisitStatus.WAITING,
        datetime(2026, 11, 8, 9, 0, tzinfo=UTC),
        arrival_confirmed_at=T0, waiting_since=T0,
        queue_sequence=1, resource_ids=frozenset({"r1"}), version=2,
    )
    walkin_arrived = datetime(2026, 11, 8, 9, 2, tzinfo=UTC)
    walkin = visit(
        "W", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=walkin_arrived, waiting_since=walkin_arrived,
        queue_sequence=2, resource_ids=frozenset({"r1"}), version=2,
    )
    kwargs = dict(
        at=at, actor_ref="staff", authorized=True,
        candidates=[walkin, appointment],
        resource_id="r1", available_resource_ids=frozenset({"r1"}),
        tenant_timezone="Africa/Casablanca",
    )
    with pytest.raises(QueueDomainError, match="QUEUE_OVERRIDE_REQUIRED"):
        call_visit(walkin, **kwargs)
    with pytest.raises(QueueDomainError, match="QUEUE_OVERRIDE_REQUIRED"):
        call_visit(walkin, can_override=True, **kwargs)
    with pytest.raises(QueueDomainError, match="QUEUE_OVERRIDE_REQUIRED"):
        call_visit(walkin, out_of_order_reason="BUSY", **kwargs)
    with pytest.raises(QueueDomainError, match="QUEUE_OVERRIDE_REQUIRED"):
        call_visit(walkin, out_of_order_reason="  ", can_override=True, **kwargs)
    overridden = call_visit(
        walkin, can_override=True, out_of_order_reason="RECEPTION_ADMISSION", **kwargs
    )
    assert overridden.visit.status is VisitStatus.CALLED
    assert [event.event_type for event in overridden.events] == [
        QueueEventType.ORDER_OVERRIDE, QueueEventType.CALLED,
    ]
    assert overridden.events[0].reason_code == "RECEPTION_ADMISSION"
    normal = call_visit(appointment, **kwargs)
    assert [event.event_type for event in normal.events] == [QueueEventType.CALLED]
    with pytest.raises(QueueDomainError, match="CALL_REQUIRES_HUMAN"):
        call_visit(appointment, actor_kind=ActorKind.DEVICE, **kwargs)


def test_call_refuses_future_visit_missing_resource_and_stale_snapshot():
    at = datetime(2026, 11, 8, 9, 5, tzinfo=UTC)
    future = visit(
        "F", VisitKind.APPOINTMENT, VisitStatus.WAITING,
        datetime(2026, 11, 8, 9, 10, tzinfo=UTC),
        arrival_confirmed_at=T0, waiting_since=T0,
        queue_sequence=1, resource_ids=frozenset({"r1"}), version=2,
    )
    base = dict(
        at=at, actor_ref="staff", authorized=True, resource_id="r1",
        available_resource_ids=frozenset({"r1"}), tenant_timezone="Africa/Casablanca",
    )
    with pytest.raises(QueueDomainError, match="CALL_NOT_ELIGIBLE_OR_STALE"):
        call_visit(future, candidates=[future], **base)
    now_ready = visit(
        "N", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0,
        queue_sequence=2, resource_ids=frozenset({"r1"}), version=3,
    )
    stale = visit(
        "N", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0,
        queue_sequence=2, resource_ids=frozenset({"r1"}), version=2,
    )
    with pytest.raises(QueueDomainError, match="CALL_NOT_ELIGIBLE_OR_STALE"):
        call_visit(stale, candidates=[now_ready], **base)
    with pytest.raises(QueueDomainError, match="CALL_NOT_ELIGIBLE_OR_STALE"):
        call_visit(now_ready, candidates=[now_ready], **{**base, "available_resource_ids": frozenset()})


def test_tiebreak_uses_confirmed_arrival_before_waiting_entry():
    at = datetime(2026, 11, 8, 9, 30, tzinfo=UTC)
    scheduled = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)
    early = visit(
        "EARLY", VisitKind.APPOINTMENT, VisitStatus.WAITING, scheduled,
        arrival_confirmed_at=T0, waiting_since=datetime(2026, 11, 8, 9, 20, tzinfo=UTC),
        queue_sequence=9, resource_ids=frozenset({"r1"}),
    )
    later = visit(
        "LATER", VisitKind.APPOINTMENT, VisitStatus.WAITING, scheduled,
        arrival_confirmed_at=datetime(2026, 11, 8, 9, 5, tzinfo=UTC),
        waiting_since=datetime(2026, 11, 8, 9, 5, tzinfo=UTC),
        queue_sequence=1, resource_ids=frozenset({"r1"}),
    )
    ranked = rank_waiting_visits(
        [later, early], tenant_id="tenant-a", queue_id="queue-a",
        resource_id="r1", available_resource_ids=frozenset({"r1"}),
        evaluated_at=at, tenant_timezone="Africa/Casablanca",
    )
    assert [item.visit.visit_id for item in ranked] == ["EARLY", "LATER"]


def test_walkin_cannot_confirm_own_arrival_from_kiosk():
    walkin = visit("W", VisitKind.WALK_IN)
    with pytest.raises(QueueDomainError, match="WALK_IN_KIOSK_CHECK_IN_FORBIDDEN"):
        check_in(
            walkin, at=T0, actor_ref="kiosk-1", actor_kind=ActorKind.DEVICE,
            method=CheckInMethod.KIOSK_QR, queue_sequence=1, authorized=True,
        )
    with pytest.raises(QueueDomainError, match="STAFF_CHECK_IN_REQUIRES_HUMAN"):
        check_in(
            walkin, at=T0, actor_ref="kiosk-1", actor_kind=ActorKind.DEVICE,
            method=CheckInMethod.STAFF, queue_sequence=1, authorized=True,
        )
    allowed = check_in(
        walkin, at=T0, actor_ref="reception-1", actor_kind=ActorKind.HUMAN,
        method=CheckInMethod.STAFF, queue_sequence=1, authorized=True,
    )
    assert allowed.visit.status is VisitStatus.WAITING


def test_kiosk_checkin_existing_appointment_requires_device_identity():
    appt = visit("A", VisitKind.APPOINTMENT, scheduled=T0)
    with pytest.raises(QueueDomainError, match="KIOSK_CHECK_IN_REQUIRES_DEVICE"):
        check_in(
            appt, at=T0, actor_ref="not-a-device",
            method=CheckInMethod.KIOSK_QR, queue_sequence=1, authorized=True,
        )
    success = check_in(
        appt, at=T0, actor_ref="paired-kiosk", actor_kind=ActorKind.DEVICE,
        method=CheckInMethod.KIOSK_QR, queue_sequence=1, authorized=True,
    )
    assert [event.event_type for event in success.events] == [
        QueueEventType.ARRIVED, QueueEventType.WAITING_ENTERED,
    ]
    with pytest.raises(QueueDomainError, match="CHECK_IN_STATE_CONFLICT"):
        check_in(
            success.visit, at=T0 + timedelta(minutes=1), actor_ref="paired-kiosk",
            actor_kind=ActorKind.DEVICE, method=CheckInMethod.KIOSK_QR,
            queue_sequence=2, authorized=True,
        )


def test_no_show_reentry_requires_human_and_reason_and_new_sequence():
    appt = visit("A", VisitKind.APPOINTMENT, scheduled=T0)
    no_show = mark_no_show(
        appt, at=T0, actor_ref="staff", actor_kind=ActorKind.HUMAN, reason_code="ABSENT", authorized=True,
    ).visit
    with pytest.raises(QueueDomainError, match="NO_SHOW_REENTRY_REQUIRES_STAFF"):
        check_in(
            no_show, at=T0 + timedelta(minutes=5), actor_ref="kiosk",
            actor_kind=ActorKind.DEVICE, method=CheckInMethod.KIOSK_QR,
            queue_sequence=2, authorized=True, reentry_reason="ARRIVED_LATER",
        )
    with pytest.raises(QueueDomainError, match="NO_SHOW_REENTRY_REASON_REQUIRED"):
        check_in(
            no_show, at=T0 + timedelta(minutes=5), actor_ref="staff",
            method=CheckInMethod.STAFF, queue_sequence=2, authorized=True,
            reentry_reason="  ",
        )
    reentry = check_in(
        no_show, at=T0 + timedelta(minutes=5), actor_ref="staff",
        method=CheckInMethod.STAFF, queue_sequence=2, authorized=True,
        reentry_reason="ARRIVED_LATER",
    )
    assert reentry.visit.status is VisitStatus.WAITING
    assert reentry.visit.queue_sequence == 2
    assert reentry.events[0].state_before is VisitStatus.NO_SHOW
    assert reentry.events[0].event_type is QueueEventType.ARRIVED


def test_invalid_temporal_facts_are_rejected_fail_closed():
    with pytest.raises(QueueDomainError, match="WAITING_BEFORE_ARRIVAL"):
        visit(
            "X", VisitKind.WALK_IN, VisitStatus.WAITING,
            arrival_confirmed_at=T0 + timedelta(minutes=2),
            waiting_since=T0, queue_sequence=1,
        )
    with pytest.raises(QueueDomainError, match="TIMEZONE_REQUIRED"):
        visit("X", VisitKind.APPOINTMENT, scheduled=datetime(2026, 11, 8, 9, 0))
    waiting = visit(
        "Y", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
    )
    with pytest.raises(QueueDomainError, match="AUDIT_REASON_REQUIRED"):
        return_to_waiting(
            visit(
                "Y", VisitKind.WALK_IN, VisitStatus.CALLED,
                arrival_confirmed_at=T0, waiting_since=T0, queue_sequence=1,
            ),
            at=T0 + timedelta(minutes=10), actor_ref="staff",
            reason_code="  ", queue_sequence=2, authorized=True,
        )


def test_raw_string_enums_cannot_bypass_domain_contract():
    with pytest.raises(QueueDomainError, match="VISIT_ENUM_INVALID"):
        visit("A", "WALK_IN")
    with pytest.raises(QueueDomainError, match="VISIT_ENUM_INVALID"):
        visit("A", VisitKind.APPOINTMENT, status="WAITING", scheduled=T0)
    appt = visit("A", VisitKind.APPOINTMENT, scheduled=T0)
    with pytest.raises(QueueDomainError, match="CHECK_IN_METHOD_INVALID"):
        check_in(
            appt, at=T0, actor_ref="staff", method="STAFF",
            queue_sequence=1, authorized=True,
        )


def test_ranking_excludes_visits_not_yet_in_waiting_at_evaluation_instant():
    at = datetime(2026, 11, 8, 9, 5, tzinfo=UTC)
    waiting_after = visit(
        "FUTURE", VisitKind.WALK_IN, VisitStatus.WAITING,
        arrival_confirmed_at=T0,
        waiting_since=at + timedelta(minutes=5),
        queue_sequence=1, resource_ids=frozenset({"r1"}),
    )
    assert rank_waiting_visits(
        [waiting_after], tenant_id="tenant-a", queue_id="queue-a",
        resource_id="r1", available_resource_ids=frozenset({"r1"}),
        evaluated_at=at, tenant_timezone="Africa/Casablanca",
    ) == ()

def test_no_show_fails_closed_for_device_system_and_unspecified_actor():
    appointment = visit("N", VisitKind.APPOINTMENT, scheduled=T0)
    for kind in (ActorKind.DEVICE, ActorKind.SYSTEM, "HUMAN", None):
        with pytest.raises(QueueDomainError, match="NO_SHOW_REQUIRES_HUMAN"):
            mark_no_show(
                appointment, at=T0, actor_ref="claimed-staff", actor_kind=kind,
                reason_code="ABSENT", authorized=True,
            )
    with pytest.raises(TypeError, match="actor_kind"):
        mark_no_show(appointment, at=T0, actor_ref="claimed-staff",
                     reason_code="ABSENT", authorized=True)
    accepted = mark_no_show(
        appointment, at=T0, actor_ref="staff-1", actor_kind=ActorKind.HUMAN,
        reason_code="ABSENT", authorized=True,
    )
    assert accepted.events[0].actor_kind is ActorKind.HUMAN
    assert accepted.visit.status is VisitStatus.NO_SHOW



def test_checkin_event_contract_cannot_lose_method_or_spoof_other_events():
    from queue_core.domain import QueueEvent

    common = dict(
        tenant_id="tenant-a", visit_id="X", occurred_at=T0,
        state_before=VisitStatus.PLANNED, state_after=VisitStatus.PLANNED,
        aggregate_version=1, actor_ref="staff-1", actor_kind=ActorKind.HUMAN,
    )
    with pytest.raises(QueueDomainError, match="CHECK_IN_METHOD_REQUIRED"):
        QueueEvent(event_type=QueueEventType.ARRIVED, **common)
    with pytest.raises(QueueDomainError, match="CHECK_IN_METHOD_REQUIRED"):
        QueueEvent(event_type=QueueEventType.WAITING_ENTERED, method="STAFF", **common)
    with pytest.raises(QueueDomainError, match="CHECK_IN_METHOD_UNEXPECTED"):
        QueueEvent(event_type=QueueEventType.CALLED, method=CheckInMethod.STAFF, **common)
    arrived = QueueEvent(
        event_type=QueueEventType.ARRIVED, method=CheckInMethod.STAFF, **common
    )
    assert arrived.method is CheckInMethod.STAFF



def test_resource_event_audit_requires_explicit_resource_identifier():
    from queue_core.domain import QueueEvent

    common = dict(
        tenant_id="tenant-a", visit_id="V", occurred_at=T0,
        state_before=VisitStatus.CALLED, state_after=VisitStatus.CALLED,
        aggregate_version=1, actor_ref="staff", actor_kind=ActorKind.HUMAN,
    )
    with pytest.raises(QueueDomainError, match="RESOURCE_EVENT_ID_REQUIRED"):
        QueueEvent(event_type=QueueEventType.RESOURCE_CLAIMED, **common)
    with pytest.raises(QueueDomainError, match="RESOURCE_ID_UNEXPECTED"):
        QueueEvent(event_type=QueueEventType.CALLED, resource_id="chair-1", **common)
    event = QueueEvent(
        event_type=QueueEventType.RESOURCE_CLAIMED,
        resource_id="chair-1", **common
    )
    assert event.resource_id == "chair-1"
