"""Standalone Queue Core domain and persistence contracts.

This package intentionally has no imports from the Digital Crown clinical
backend. Runtime composition, database connection and API wiring belong to
later LOT08 sub-lots.
"""

from queue_core.domain import (
    ActorKind,
    CheckInMethod,
    QueueDomainError,
    QueueEvent,
    QueueEventType,
    QueueVisit,
    TransitionResult,
    VisitKind,
    VisitStatus,
    call_visit,
    cancel_visit,
    check_in,
    complete_visit,
    mark_no_show,
    move_to_chair,
    record_unlocated_after_call,
    rank_waiting_visits,
    recall_visit,
    return_to_waiting,
)

__all__ = [
    "ActorKind",
    "CheckInMethod",
    "QueueDomainError",
    "QueueEvent",
    "QueueEventType",
    "QueueVisit",
    "TransitionResult",
    "VisitKind",
    "VisitStatus",
    "call_visit",
    "cancel_visit",
    "check_in",
    "complete_visit",
    "mark_no_show",
    "move_to_chair",
    "record_unlocated_after_call",
    "rank_waiting_visits",
    "recall_visit",
    "return_to_waiting",
]
