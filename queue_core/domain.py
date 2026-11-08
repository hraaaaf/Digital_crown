"""Pure Queue Core domain rules for V1.5-08.1.

No HTTP, authentication, UI, external connector, database engine, or clinical
Digital Crown model is imported here. Callers supply an already-authorized
actor and commit every returned event/state change in one transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class VisitKind(str, Enum):
    APPOINTMENT = "APPOINTMENT"
    WALK_IN = "WALK_IN"


class VisitStatus(str, Enum):
    PLANNED = "PLANNED"
    EN_ROUTE = "EN_ROUTE"  # Informational only; it never confirms presence.
    WAITING = "WAITING"
    CALLED = "CALLED"
    CHAIR = "CHAIR"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class ActorKind(str, Enum):
    HUMAN = "HUMAN"
    DEVICE = "DEVICE"
    SYSTEM = "SYSTEM"


class CheckInMethod(str, Enum):
    STAFF = "STAFF"
    KIOSK_QR = "KIOSK_QR"


class QueueEventType(str, Enum):
    ARRIVED = "ARRIVED"
    WAITING_ENTERED = "WAITING_ENTERED"
    CALLED = "CALLED"
    RECALLED = "RECALLED"
    ORDER_OVERRIDE = "ORDER_OVERRIDE"
    RESOURCE_CLAIMED = "RESOURCE_CLAIMED"
    RESOURCE_RELEASED = "RESOURCE_RELEASED"
    CHAIR = "CHAIR"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    UNLOCATED_AFTER_CALL = "UNLOCATED_AFTER_CALL"
    RETURNED_TO_WAITING = "RETURNED_TO_WAITING"


class QueueDomainError(ValueError):
    """A rejected command with a stable, non-sensitive error code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def as_utc(value: datetime) -> datetime:
    """Require an aware timestamp and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise QueueDomainError("TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


def validate_iana_timezone(value: str) -> str:
    """Validate and return the tenant's explicit IANA timezone identifier."""

    if not value or value != value.strip():
        raise QueueDomainError("TENANT_TIMEZONE_REQUIRED")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise QueueDomainError("TENANT_TIMEZONE_INVALID") from None
    return value


@dataclass(frozen=True, slots=True)
class QueueVisit:
    visit_id: str
    tenant_id: str
    queue_id: str
    kind: VisitKind
    status: VisitStatus
    scheduled_at: datetime | None = None
    arrival_confirmed_at: datetime | None = None
    waiting_since: datetime | None = None
    queue_sequence: int | None = None
    resource_ids: frozenset[str] = frozenset()
    held_resource_id: str | None = None
    version: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.kind, VisitKind) or not isinstance(self.status, VisitStatus):
            raise QueueDomainError("VISIT_ENUM_INVALID")
        if not self.visit_id or not self.tenant_id or not self.queue_id:
            raise QueueDomainError("VISIT_SCOPE_REQUIRED")
        if self.version < 0:
            raise QueueDomainError("VERSION_INVALID")
        if self.kind is VisitKind.APPOINTMENT and self.scheduled_at is None:
            raise QueueDomainError("APPOINTMENT_TIME_REQUIRED")
        if self.kind is VisitKind.WALK_IN and self.scheduled_at is not None:
            raise QueueDomainError("WALK_IN_CANNOT_HAVE_APPOINTMENT_TIME")
        if self.status is VisitStatus.NO_SHOW and self.kind is not VisitKind.APPOINTMENT:
            raise QueueDomainError("NO_SHOW_ONLY_APPOINTMENT")
        for field_name in ("scheduled_at", "arrival_confirmed_at", "waiting_since"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, as_utc(value))
        if self.status in {
            VisitStatus.WAITING,
            VisitStatus.CALLED,
            VisitStatus.CHAIR,
            VisitStatus.DONE,
        }:
            if self.arrival_confirmed_at is None or self.waiting_since is None:
                raise QueueDomainError("PRESENT_VISIT_REQUIRES_ARRIVAL")
            if self.queue_sequence is None or self.queue_sequence < 1:
                raise QueueDomainError("QUEUE_SEQUENCE_REQUIRED")
        if self.status in {VisitStatus.PLANNED, VisitStatus.EN_ROUTE, VisitStatus.NO_SHOW}:
            if self.arrival_confirmed_at is not None:
                raise QueueDomainError("NO_ARRIVAL_STATE_HAS_ARRIVAL_FACT")
        if (
            self.arrival_confirmed_at is not None
            and self.waiting_since is not None
            and self.waiting_since < self.arrival_confirmed_at
        ):
            raise QueueDomainError("WAITING_BEFORE_ARRIVAL")
        if self.status is VisitStatus.CHAIR and self.held_resource_id is None:
            raise QueueDomainError("CHAIR_RESOURCE_REQUIRED")
        if self.status is not VisitStatus.CHAIR and self.held_resource_id is not None:
            raise QueueDomainError("RESOURCE_HELD_OUTSIDE_CHAIR")


@dataclass(frozen=True, slots=True)
class QueueEvent:
    tenant_id: str
    visit_id: str
    event_type: QueueEventType
    occurred_at: datetime
    state_before: VisitStatus
    state_after: VisitStatus
    aggregate_version: int
    actor_ref: str
    actor_kind: ActorKind = ActorKind.HUMAN
    reason_code: str | None = None
    method: CheckInMethod | None = None
    resource_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.event_type, QueueEventType)
            or not isinstance(self.actor_kind, ActorKind)
            or not isinstance(self.state_before, VisitStatus)
            or not isinstance(self.state_after, VisitStatus)
        ):
            raise QueueDomainError("EVENT_ENUM_INVALID")
        object.__setattr__(self, "occurred_at", as_utc(self.occurred_at))
        if not self.actor_ref:
            raise QueueDomainError("ACTOR_REFERENCE_REQUIRED")
        if self.aggregate_version < 1:
            raise QueueDomainError("EVENT_VERSION_INVALID")
        if self.event_type in {QueueEventType.ARRIVED, QueueEventType.WAITING_ENTERED}:
            if not isinstance(self.method, CheckInMethod):
                raise QueueDomainError("CHECK_IN_METHOD_REQUIRED")
        elif self.method is not None:
            raise QueueDomainError("CHECK_IN_METHOD_UNEXPECTED")
        if (
            (self.method is CheckInMethod.STAFF and self.actor_kind is not ActorKind.HUMAN)
            or (self.method is CheckInMethod.KIOSK_QR and self.actor_kind is not ActorKind.DEVICE)
        ):
            raise QueueDomainError("CHECK_IN_ACTOR_METHOD_MISMATCH")
        if self.event_type in {QueueEventType.RESOURCE_CLAIMED, QueueEventType.RESOURCE_RELEASED}:
            if not self.resource_id or not self.resource_id.strip():
                raise QueueDomainError("RESOURCE_EVENT_ID_REQUIRED")
        elif self.resource_id is not None:
            raise QueueDomainError("RESOURCE_ID_UNEXPECTED")
        if self.event_type in {
            QueueEventType.ORDER_OVERRIDE,
            QueueEventType.NO_SHOW,
            QueueEventType.UNLOCATED_AFTER_CALL,
            QueueEventType.RETURNED_TO_WAITING,
            QueueEventType.CANCELLED,
        } and (not self.reason_code or not self.reason_code.strip()):
            raise QueueDomainError("AUDIT_REASON_REQUIRED")


@dataclass(frozen=True, slots=True)
class TransitionResult:
    visit: QueueVisit
    events: tuple[QueueEvent, ...]
    released_resource_ids: tuple[str, ...] = ()
    claimed_resource_id: str | None = None


def _event(
    visit: QueueVisit,
    event_type: QueueEventType,
    at: datetime,
    actor_ref: str,
    version: int,
    *,
    state_after: VisitStatus | None = None,
    actor_kind: ActorKind = ActorKind.HUMAN,
    reason_code: str | None = None,
    method: CheckInMethod | None = None,
    resource_id: str | None = None,
) -> QueueEvent:
    return QueueEvent(
        tenant_id=visit.tenant_id,
        visit_id=visit.visit_id,
        event_type=event_type,
        occurred_at=at,
        state_before=visit.status,
        state_after=state_after or visit.status,
        aggregate_version=version,
        actor_ref=actor_ref,
        actor_kind=actor_kind,
        reason_code=reason_code,
        method=method,
        resource_id=resource_id,
    )


def check_in(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    method: CheckInMethod,
    queue_sequence: int,
    authorized: bool,
    reentry_reason: str | None = None,
    actor_kind: ActorKind = ActorKind.HUMAN,
) -> TransitionResult:
    """Confirm presence and enter WAITING with one atomic two-event plan."""

    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("CHECK_IN_FORBIDDEN")
    if not isinstance(method, CheckInMethod) or not isinstance(actor_kind, ActorKind):
        raise QueueDomainError("CHECK_IN_METHOD_INVALID")
    if queue_sequence < 1:
        raise QueueDomainError("QUEUE_SEQUENCE_INVALID")
    if visit.status not in {VisitStatus.PLANNED, VisitStatus.EN_ROUTE, VisitStatus.NO_SHOW}:
        raise QueueDomainError("CHECK_IN_STATE_CONFLICT")
    if visit.kind is VisitKind.WALK_IN and method is CheckInMethod.KIOSK_QR:
        raise QueueDomainError("WALK_IN_KIOSK_CHECK_IN_FORBIDDEN")
    if method is CheckInMethod.STAFF and actor_kind is not ActorKind.HUMAN:
        raise QueueDomainError("STAFF_CHECK_IN_REQUIRES_HUMAN")
    if method is CheckInMethod.KIOSK_QR and actor_kind is not ActorKind.DEVICE:
        raise QueueDomainError("KIOSK_CHECK_IN_REQUIRES_DEVICE")
    if visit.status is VisitStatus.NO_SHOW:
        if method is not CheckInMethod.STAFF:
            raise QueueDomainError("NO_SHOW_REENTRY_REQUIRES_STAFF")
        if not reentry_reason or not reentry_reason.strip():
            raise QueueDomainError("NO_SHOW_REENTRY_REASON_REQUIRED")
    if visit.queue_sequence is not None and queue_sequence <= visit.queue_sequence:
        raise QueueDomainError("QUEUE_SEQUENCE_INVALID")
    next_visit = replace(
        visit,
        status=VisitStatus.WAITING,
        arrival_confirmed_at=at,
        waiting_since=at,
        queue_sequence=queue_sequence,
        held_resource_id=None,
        version=visit.version + 2,
    )
    arrived = _event(
        visit,
        QueueEventType.ARRIVED,
        at,
        actor_ref,
        visit.version + 1,
        actor_kind=actor_kind,
        reason_code="REENTRY_AFTER_NO_SHOW" if visit.status is VisitStatus.NO_SHOW else None,
        method=method,
    )
    waiting = _event(
        visit,
        QueueEventType.WAITING_ENTERED,
        at,
        actor_ref,
        visit.version + 2,
        state_after=VisitStatus.WAITING,
        actor_kind=actor_kind,
        reason_code=reentry_reason,
        method=method,
    )
    return TransitionResult(next_visit, (arrived, waiting))


def call_visit(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    authorized: bool,
    candidates: Iterable[QueueVisit],
    resource_id: str,
    available_resource_ids: frozenset[str],
    tenant_timezone: str,
    actor_kind: ActorKind = ActorKind.HUMAN,
    out_of_order_reason: str | None = None,
    can_override: bool = False,
) -> TransitionResult:
    """Call only a currently eligible visit; a deviation needs audited override.

    The future 08.3 service MUST read the complete server-side candidate set,
    authorize the actor and commit this plan under one transactional lock.
    A client-supplied or partial candidate list is not an authoritative queue.
    """

    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("CALL_FORBIDDEN")
    if not isinstance(actor_kind, ActorKind) or actor_kind is not ActorKind.HUMAN:
        raise QueueDomainError("CALL_REQUIRES_HUMAN")
    if visit.status is not VisitStatus.WAITING:
        raise QueueDomainError("CALL_STATE_CONFLICT")
    ranked = rank_waiting_visits(
        candidates,
        tenant_id=visit.tenant_id,
        queue_id=visit.queue_id,
        resource_id=resource_id,
        available_resource_ids=available_resource_ids,
        evaluated_at=at,
        tenant_timezone=tenant_timezone,
    )
    matching = next((item for item in ranked if item.visit.visit_id == visit.visit_id), None)
    if matching is None or matching.visit.version != visit.version:
        raise QueueDomainError("CALL_NOT_ELIGIBLE_OR_STALE")
    is_override = ranked[0].visit.visit_id != visit.visit_id
    if is_override and (not can_override or not out_of_order_reason or not out_of_order_reason.strip()):
        raise QueueDomainError("QUEUE_OVERRIDE_REQUIRED")
    if out_of_order_reason and not can_override:
        raise QueueDomainError("QUEUE_OVERRIDE_FORBIDDEN")
    if out_of_order_reason is not None and not out_of_order_reason.strip():
        raise QueueDomainError("AUDIT_REASON_REQUIRED")
    if not is_override and out_of_order_reason:
        raise QueueDomainError("QUEUE_OVERRIDE_NOT_REQUIRED")

    events: list[QueueEvent] = []
    version = visit.version
    if is_override:
        version += 1
        events.append(
            _event(
                visit,
                QueueEventType.ORDER_OVERRIDE,
                at,
                actor_ref,
                version,
                actor_kind=actor_kind,
                reason_code=out_of_order_reason,
            )
        )
    version += 1
    events.append(
        _event(
            visit,
            QueueEventType.CALLED,
            at,
            actor_ref,
            version,
            state_after=VisitStatus.CALLED,
            actor_kind=actor_kind,
            reason_code=out_of_order_reason,
        )
    )
    return TransitionResult(replace(visit, status=VisitStatus.CALLED, version=version), tuple(events))


def recall_visit(
    visit: QueueVisit, *, at: datetime, actor_ref: str, authorized: bool
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("RECALL_FORBIDDEN")
    if visit.status is not VisitStatus.CALLED:
        raise QueueDomainError("RECALL_STATE_CONFLICT")
    event = _event(
        visit,
        QueueEventType.RECALLED,
        at,
        actor_ref,
        visit.version + 1,
    )
    return TransitionResult(replace(visit, version=visit.version + 1), (event,))


def record_unlocated_after_call(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    reason_code: str,
    authorized: bool,
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("UNLOCATED_FORBIDDEN")
    if visit.status is not VisitStatus.CALLED:
        raise QueueDomainError("UNLOCATED_STATE_CONFLICT")
    event = _event(
        visit,
        QueueEventType.UNLOCATED_AFTER_CALL,
        at,
        actor_ref,
        visit.version + 1,
        reason_code=reason_code,
    )
    return TransitionResult(replace(visit, version=visit.version + 1), (event,))


def return_to_waiting(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    reason_code: str,
    queue_sequence: int,
    authorized: bool,
) -> TransitionResult:
    """Re-enter a queue without restoring the former position.

    When the visit is in CHAIR the returned transaction plan includes resource
    release and the new WAITING sequence together. The persistence service in
    08.3 must commit all planned events/state/resource writes atomically.
    """

    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("RETURN_TO_WAITING_FORBIDDEN")
    if visit.status not in {VisitStatus.CALLED, VisitStatus.CHAIR}:
        raise QueueDomainError("RETURN_TO_WAITING_STATE_CONFLICT")
    if not reason_code or not reason_code.strip():
        raise QueueDomainError("AUDIT_REASON_REQUIRED")
    if queue_sequence < 1 or queue_sequence <= (visit.queue_sequence or 0):
        raise QueueDomainError("QUEUE_SEQUENCE_INVALID")
    releasing = (visit.held_resource_id,) if visit.status is VisitStatus.CHAIR else ()
    events: list[QueueEvent] = []
    version = visit.version
    if releasing:
        version += 1
        events.append(
            _event(
                visit,
                QueueEventType.RESOURCE_RELEASED,
                at,
                actor_ref,
                version,
                actor_kind=ActorKind.HUMAN,
                reason_code=reason_code,
                resource_id=releasing[0],
            )
        )
    version += 1
    events.append(
        _event(
            visit,
            QueueEventType.RETURNED_TO_WAITING,
            at,
            actor_ref,
            version,
            state_after=VisitStatus.WAITING,
            reason_code=reason_code,
        )
    )
    next_visit = replace(
        visit,
        status=VisitStatus.WAITING,
        waiting_since=at,
        queue_sequence=queue_sequence,
        held_resource_id=None,
        version=version,
    )
    return TransitionResult(next_visit, tuple(events), released_resource_ids=releasing)


def move_to_chair(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    resource_id: str,
    resource_available: bool,
    authorized: bool,
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("CHAIR_FORBIDDEN")
    if visit.status is not VisitStatus.CALLED:
        raise QueueDomainError("CHAIR_STATE_CONFLICT")
    if resource_id not in visit.resource_ids or not resource_available:
        raise QueueDomainError("RESOURCE_NOT_AVAILABLE")
    claimed = _event(
        visit,
        QueueEventType.RESOURCE_CLAIMED,
        at,
        actor_ref,
        visit.version + 1,
        resource_id=resource_id,
    )
    chair = _event(
        visit,
        QueueEventType.CHAIR,
        at,
        actor_ref,
        visit.version + 2,
        state_after=VisitStatus.CHAIR,
    )
    return TransitionResult(
        replace(
            visit,
            status=VisitStatus.CHAIR,
            held_resource_id=resource_id,
            version=visit.version + 2,
        ),
        (claimed, chair),
        claimed_resource_id=resource_id,
    )


def complete_visit(
    visit: QueueVisit, *, at: datetime, actor_ref: str, authorized: bool
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("DONE_FORBIDDEN")
    if visit.status is not VisitStatus.CHAIR or visit.held_resource_id is None:
        raise QueueDomainError("DONE_STATE_CONFLICT")
    released = _event(
        visit,
        QueueEventType.RESOURCE_RELEASED,
        at,
        actor_ref,
        visit.version + 1,
        resource_id=visit.held_resource_id,
    )
    done = _event(
        visit,
        QueueEventType.DONE,
        at,
        actor_ref,
        visit.version + 2,
        state_after=VisitStatus.DONE,
    )
    resource_id = visit.held_resource_id
    return TransitionResult(
        replace(
            visit,
            status=VisitStatus.DONE,
            held_resource_id=None,
            version=visit.version + 2,
        ),
        (released, done),
        released_resource_ids=(resource_id,),
    )


def cancel_visit(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    reason_code: str,
    authorized: bool,
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("CANCEL_FORBIDDEN")
    if not reason_code or not reason_code.strip():
        raise QueueDomainError("AUDIT_REASON_REQUIRED")
    if visit.status not in {
        VisitStatus.PLANNED,
        VisitStatus.WAITING,
        VisitStatus.CALLED,
    }:
        raise QueueDomainError("CANCEL_STATE_CONFLICT")
    event = _event(
        visit,
        QueueEventType.CANCELLED,
        at,
        actor_ref,
        visit.version + 1,
        state_after=VisitStatus.CANCELLED,
        reason_code=reason_code,
    )
    return TransitionResult(
        replace(visit, status=VisitStatus.CANCELLED, held_resource_id=None, version=visit.version + 1),
        (event,),
    )


def mark_no_show(
    visit: QueueVisit,
    *,
    at: datetime,
    actor_ref: str,
    actor_kind: ActorKind,
    reason_code: str,
    authorized: bool,
) -> TransitionResult:
    at = as_utc(at)
    if not authorized:
        raise QueueDomainError("NO_SHOW_FORBIDDEN")
    if not isinstance(actor_kind, ActorKind) or actor_kind is not ActorKind.HUMAN:
        raise QueueDomainError("NO_SHOW_REQUIRES_HUMAN")
    if visit.kind is not VisitKind.APPOINTMENT or visit.status not in {
        VisitStatus.PLANNED,
        VisitStatus.EN_ROUTE,
    }:
        raise QueueDomainError("NO_SHOW_STATE_CONFLICT")
    if visit.arrival_confirmed_at is not None:
        raise QueueDomainError("NO_SHOW_AFTER_ARRIVAL_FORBIDDEN")
    if visit.scheduled_at is None or visit.scheduled_at > at:
        raise QueueDomainError("NO_SHOW_BEFORE_APPOINTMENT_FORBIDDEN")
    event = _event(
        visit,
        QueueEventType.NO_SHOW,
        at,
        actor_ref,
        visit.version + 1,
        state_after=VisitStatus.NO_SHOW,
        actor_kind=actor_kind,
        reason_code=reason_code,
    )
    return TransitionResult(replace(visit, status=VisitStatus.NO_SHOW, version=visit.version + 1), (event,))


@dataclass(frozen=True, slots=True)
class RankedVisit:
    visit: QueueVisit
    rank: int
    explanation_code: str


def rank_waiting_visits(
    visits: Iterable[QueueVisit],
    *,
    tenant_id: str,
    queue_id: str,
    resource_id: str,
    available_resource_ids: frozenset[str],
    evaluated_at: datetime,
    tenant_timezone: str,
) -> tuple[RankedVisit, ...]:
    """Recompute the callable order for one available queue resource.

    Due arrived appointments sort before admitted walk-ins. Future appointments
    are not callable yet. All keys use UTC instants; IANA zone validation is
    explicit so callers cannot inherit the host machine's local timezone.
    """

    evaluated_at = as_utc(evaluated_at)
    validate_iana_timezone(tenant_timezone)
    if resource_id not in available_resource_ids:
        return ()

    appointments: list[QueueVisit] = []
    walk_ins: list[QueueVisit] = []
    for visit in visits:
        if (
            visit.tenant_id != tenant_id
            or visit.queue_id != queue_id
            or visit.status is not VisitStatus.WAITING
            or visit.arrival_confirmed_at is None
            or visit.arrival_confirmed_at > evaluated_at
            or visit.waiting_since is None
            or visit.waiting_since > evaluated_at
            or visit.queue_sequence is None
            or resource_id not in visit.resource_ids
        ):
            continue
        if visit.kind is VisitKind.APPOINTMENT:
            if visit.scheduled_at is not None and visit.scheduled_at <= evaluated_at:
                appointments.append(visit)
        else:
            walk_ins.append(visit)

    appointments.sort(
        key=lambda item: (item.scheduled_at, item.arrival_confirmed_at, item.queue_sequence, item.visit_id)
    )
    walk_ins.sort(key=lambda item: (item.arrival_confirmed_at, item.queue_sequence, item.visit_id))
    ordered = [(item, "ELIGIBLE_APPOINTMENT") for item in appointments]
    ordered.extend((item, "ADMITTED_WALK_IN") for item in walk_ins)
    return tuple(RankedVisit(visit=item, rank=index + 1, explanation_code=code) for index, (item, code) in enumerate(ordered))
