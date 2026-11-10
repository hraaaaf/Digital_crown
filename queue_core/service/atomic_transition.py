"""LOT08.3 FUE-0: guard a domain plan before ANY durable state/event write.

A plan is valid only for the exact persisted original aggregate it was derived
from, with consecutive event versions, immutable tenant/queue/visit scope and
unchanged clinical-independent visit identity. The caller still needs a single
database transaction and a version CAS; validation alone is not durability.
"""
from __future__ import annotations

from queue_core.domain import (
    QueueDomainError, QueueVisit, TransitionResult,
)


def validate_atomic_transition(original: QueueVisit, plan: TransitionResult) -> None:
    """Reject inconsistent multi-event transition plans before persistence."""
    if not isinstance(original, QueueVisit) or not isinstance(plan, TransitionResult):
        raise QueueDomainError("ATOMIC_PLAN_INVALID")
    target = plan.visit
    events = plan.events
    if not isinstance(target, QueueVisit) or not isinstance(events, tuple) or not events:
        raise QueueDomainError("ATOMIC_PLAN_INVALID")

    if (
        target.visit_id != original.visit_id
        or target.tenant_id != original.tenant_id
        or target.queue_id != original.queue_id
        or target.kind != original.kind
        or target.scheduled_at != original.scheduled_at
        or target.resource_ids != original.resource_ids
    ):
        raise QueueDomainError("ATOMIC_PLAN_SCOPE_CHANGED")

    if target.version != original.version + len(events):
        raise QueueDomainError("ATOMIC_PLAN_VERSION_CONFLICT")

    first = events[0]
    actor_ref = first.actor_ref
    actor_kind = first.actor_kind
    instant = first.occurred_at
    for index, event in enumerate(events, 1):
        if (
            event.tenant_id != original.tenant_id
            or event.visit_id != original.visit_id
            or event.aggregate_version != original.version + index
            or event.state_before != original.status
            or event.state_after not in (original.status, target.status)
            or event.actor_ref != actor_ref
            or event.actor_kind != actor_kind
            or event.occurred_at != instant
        ):
            raise QueueDomainError("ATOMIC_PLAN_EVENT_MISMATCH")

    if events[-1].state_after != target.status:
        raise QueueDomainError("ATOMIC_PLAN_FINAL_STATE_MISMATCH")
