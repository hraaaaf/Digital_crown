"""08.3 FUE-0: genuine domain plans and corrupted plans must fail closed."""
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from queue_core.domain import (
    ActorKind, CheckInMethod, QueueDomainError, QueueVisit,
    TransitionResult, VisitKind, VisitStatus, check_in,
    complete_visit, move_to_chair, recall_visit,
)
from queue_core.service.atomic_transition import validate_atomic_transition


NOW = datetime(2026, 11, 10, 9, tzinfo=timezone.utc)


def _visit(status=VisitStatus.PLANNED, version=0):
    present = status in {
        VisitStatus.WAITING, VisitStatus.CALLED, VisitStatus.CHAIR, VisitStatus.DONE,
    }
    return QueueVisit(
        visit_id="V1", tenant_id="T1", queue_id="Q1",
        kind=VisitKind.APPOINTMENT, status=status,
        scheduled_at=NOW, version=version,
        arrival_confirmed_at=NOW if present else None,
        waiting_since=NOW if present else None,
        queue_sequence=1 if present else None,
        held_resource_id="R1" if status is VisitStatus.CHAIR else None,
        resource_ids=frozenset({"R1"}),
    )


def _checkin():
    before = _visit()
    plan = check_in(
        before, at=NOW, actor_ref="staff1",
        method=CheckInMethod.STAFF, actor_kind=ActorKind.HUMAN,
        queue_sequence=1, authorized=True,
    )
    return before, plan


def test_real_check_in_two_events_and_version_match():
    original, plan = _checkin()
    validate_atomic_transition(original, plan)
    assert len(plan.events) == 2
    assert [e.aggregate_version for e in plan.events] == [1, 2]


def test_real_chair_and_done_two_event_plans():
    before = _visit(VisitStatus.CALLED, version=3)
    plan = move_to_chair(
        before, at=NOW, actor_ref="staff1", resource_id="R1",
        resource_available=True, authorized=True,
    )
    validate_atomic_transition(before, plan)
    assert plan.visit.held_resource_id == "R1"
    done = complete_visit(plan.visit, at=NOW, actor_ref="staff1", authorized=True)
    validate_atomic_transition(plan.visit, done)


def test_recall_one_event_same_state_allowed():
    before = _visit(VisitStatus.CALLED, version=3)
    plan = recall_visit(before, at=NOW, actor_ref="staff1", authorized=True)
    validate_atomic_transition(before, plan)
    assert plan.visit.status is before.status


@pytest.mark.parametrize("change", [
    lambda v: replace(v, tenant_id="T2"),
    lambda v: replace(v, queue_id="Q2"),
    lambda v: replace(v, visit_id="V2"),
    lambda v: replace(v, resource_ids=frozenset()),
    lambda v: replace(v, scheduled_at=NOW.replace(year=2027)),
])
def test_mutated_scope_must_fail_before_commit(change):
    before, plan = _checkin()
    tampered = replace(plan, visit=change(plan.visit))
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_SCOPE_CHANGED"):
        validate_atomic_transition(before, tampered)


@pytest.mark.parametrize("change", [
    lambda e: replace(e, tenant_id="T2"),
    lambda e: replace(e, visit_id="V2"),
    lambda e: replace(e, aggregate_version=5),
    lambda e: replace(e, actor_ref="other"),
    lambda e: replace(e, occurred_at=NOW.replace(day=11)),
])
def test_tampered_event_or_version_fails_closed(change):
    before, plan = _checkin()
    altered = replace(plan, events=(plan.events[0], change(plan.events[1])))
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_EVENT_MISMATCH"):
        validate_atomic_transition(before, altered)


def test_missing_event_rejected_even_with_valid_final_state():
    before, plan = _checkin()
    altered = replace(plan, events=(plan.events[-1],))
    with pytest.raises(QueueDomainError):
        validate_atomic_transition(before, altered)


def test_final_state_must_match_last_event():
    before, plan = _checkin()
    e = replace(plan.events[-1], state_after=VisitStatus.PLANNED)
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_FINAL_STATE_MISMATCH"):
        validate_atomic_transition(before, replace(plan, events=(plan.events[0], e)))


def test_target_version_must_equal_consecutive_event_count():
    before, plan = _checkin()
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_VERSION_CONFLICT"):
        validate_atomic_transition(before, replace(plan, visit=replace(plan.visit, version=3)))


def test_empty_events_fail_closed():
    before, plan = _checkin()
    with pytest.raises(QueueDomainError, match="ATOMIC_PLAN_INVALID"):
        validate_atomic_transition(before, TransitionResult(plan.visit, ()))
