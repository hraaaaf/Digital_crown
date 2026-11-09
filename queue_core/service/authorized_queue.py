"""LOT08.2-B local-only, transactional human-authorized Queue Core adapter.

Real, isolated SQLite schema and domain transitions; no HTTP, SSE listener,
patient identity, installer, device identity or clinical database integration.
The auth DB write lock is ALWAYS acquired before the queue DB write lock. Both
remain held through queue state/event commit, blocking concurrent revocation and
queue reordering during each authorized operation. SQLite local file only.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import re
from typing import Callable, Iterator
from uuid import uuid4

from sqlalchemy import Engine, and_, func, or_, select, update
from sqlalchemy.orm import Session

from queue_core.domain import (
    ActorKind, CheckInMethod, QueueDomainError, QueueVisit, VisitKind,
    VisitStatus, as_utc, call_visit, check_in, complete_visit, mark_no_show,
    move_to_chair, recall_visit,
)
from queue_core.persistence.models import (
    QueueEventRecord, QueueLine, QueueResource, QueueTenant,
    QueueVisitRecord, QueueVisitResource,
)
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import (
    AuthorizationError, Permission, QueueAuthorizer, TargetScope,
    VerifiedPrincipal,
)


class HumanCommand(str, Enum):
    CHECK_IN = "check_in"
    CALL = "call"
    RECALL = "recall"
    CHAIR = "chair"
    DONE = "done"
    NO_SHOW = "no_show"


_ACTIONS = {
    HumanCommand.CHECK_IN: Permission.VISIT_CHECK_IN,
    HumanCommand.CALL: Permission.QUEUE_CALL,
    HumanCommand.RECALL: Permission.QUEUE_RECALL,
    HumanCommand.CHAIR: Permission.QUEUE_CHAIR,
    HumanCommand.DONE: Permission.QUEUE_DONE,
    HumanCommand.NO_SHOW: Permission.QUEUE_NO_SHOW,
}


@dataclass(frozen=True, slots=True)
class QueueEventView:
    id: str
    visit_ref: str
    event_type: str
    aggregate_version: int
    occurred_at_utc: datetime


@dataclass(frozen=True, slots=True)
class QueueVisitView:
    id: str
    queue_id: str
    status: str
    version: int
    queue_sequence: int | None


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        # SQLite DateTime stores UTC instants without TZ offset.
        return value.replace(tzinfo=timezone.utc)
    return as_utc(value)


def _db_datetime(value: datetime | None) -> datetime | None:
    normalized = _utc(value)
    return normalized.replace(tzinfo=None) if normalized else None


def _denied() -> None:
    raise AuthorizationError("AUTHZ_DENIED", 403)


def _audit_reason(value: str | None) -> str:
    # Codes only, never free-text patient notes in the queue event audit log.
    if not isinstance(value, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value) is None:
        raise QueueDomainError("AUDIT_REASON_CODE_INVALID")
    return value


class AuthorizedLocalQueue:
    """In-process local command and event replay boundary; NOT an HTTP API.

    Queue and auth DB paths must exist and be distinct. The caller must have
    already initialized a QueueBase schema explicitly in an isolated file.
    No create_all(), schema migration, side-effectful import or network listener.
    """

    def __init__(
        self, operators: LocalOperatorStore, queue_engine: Engine,
        *, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not isinstance(operators, LocalOperatorStore):
            raise TypeError("AUTH_STORE_REQUIRED")
        if not isinstance(queue_engine, Engine):
            raise TypeError("QUEUE_ENGINE_REQUIRED")
        if not queue_engine.url.drivername.startswith("sqlite"):
            raise ValueError("LOCAL_SQLITE_ONLY")
        queue_filename = queue_engine.url.database
        if not queue_filename or queue_filename == ":memory:":
            raise ValueError("PERSISTENT_QUEUE_SQLITE_REQUIRED")
        queue_path = Path(queue_filename).resolve()
        identity_path = operators.auth.path.resolve()
        if queue_path == identity_path:
            raise ValueError("AUTH_QUEUE_DATABASES_MUST_BE_SEPARATE")
        if not queue_path.is_file():
            raise ValueError("QUEUE_DB_NOT_INITIALIZED")
        self._operators = operators
        self._engine = queue_engine
        self._clock = clock

    @contextmanager
    def _transaction(
        self, token: str
    ) -> Iterator[tuple[Session, VerifiedPrincipal, QueueAuthorizer]]:
        # The operator store's protected connection already uses FK, FULL sync,
        # secure_delete and busy timeout; lock before reading live auth state.
        if not isinstance(token, str) or not token or len(token) > 256:
            raise AuthorizationError("AUTH_REQUIRED", 401)
        with self._operators.auth._connect() as identity:
            identity.execute("BEGIN IMMEDIATE")
            try:
                principal = self._operators._principal(
                    identity, token, self._operators._now()
                )
                if principal is None:
                    raise AuthorizationError("AUTH_REQUIRED", 401)
                authorizer = QueueAuthorizer(lambda _: principal)
                with self._engine.connect() as queue_conn:
                    queue_conn.exec_driver_sql("PRAGMA foreign_keys=ON")
                    queue_conn.exec_driver_sql("PRAGMA busy_timeout=5000")
                    queue_conn.exec_driver_sql("BEGIN IMMEDIATE")
                    try:
                        with Session(bind=queue_conn, expire_on_commit=False) as session:
                            yield session, principal, authorizer
                            session.flush()
                        queue_conn.commit()
                    except BaseException:
                        queue_conn.rollback()
                        raise
                identity.commit()
            except BaseException:
                identity.rollback()
                raise

    @staticmethod
    def _queue(
        db: Session, tenant_id: str, queue_id: str
    ) -> QueueLine:
        queue = db.scalar(
            select(QueueLine).where(
                QueueLine.id == queue_id,
                QueueLine.tenant_id == tenant_id,
                QueueLine.is_active.is_(True),
            )
        )
        if queue is None:
            _denied()
        return queue

    @classmethod
    def _visit(
        cls, db: Session, principal: VerifiedPrincipal, visit_id: str
    ) -> QueueVisitRecord:
        # Scoped query means an object from another tenant is indistinguishable
        # from a nonexistent object. No client-asserted tenant or queue is read.
        if not isinstance(visit_id, str) or len(visit_id) > 128 or not visit_id:
            _denied()
        visit = db.scalar(
            select(QueueVisitRecord).where(
                QueueVisitRecord.id == visit_id,
                QueueVisitRecord.tenant_id == principal.tenant_id,
            )
        )
        if visit is None:
            _denied()
        cls._queue(db, principal.tenant_id, visit.queue_id)
        return visit

    @staticmethod
    def _resource(
        db: Session, visit: QueueVisitRecord, resource_id: str
    ) -> QueueResource:
        if not isinstance(resource_id, str) or not resource_id:
            _denied()
        resource = db.scalar(
            select(QueueResource).join(
                QueueVisitResource,
                and_(
                    QueueVisitResource.resource_id == QueueResource.id,
                    QueueVisitResource.tenant_id == QueueResource.tenant_id,
                ),
            ).where(
                QueueResource.id == resource_id,
                QueueResource.tenant_id == visit.tenant_id,
                QueueResource.is_active.is_(True),
                QueueVisitResource.visit_id == visit.id,
            )
        )
        if resource is None:
            _denied()
        return resource

    @staticmethod
    def _target(visit: QueueVisitRecord, resource: QueueResource | None) -> TargetScope:
        # These bindings originate ONLY from persisted queue/visit/resource rows.
        return TargetScope(
            tenant_id=visit.tenant_id, queue_id=visit.queue_id,
            visit_id=visit.id, visit_tenant_id=visit.tenant_id,
            visit_queue_id=visit.queue_id,
            resource_id=resource.id if resource else None,
            resource_tenant_id=resource.tenant_id if resource else None,
            resource_queue_id=visit.queue_id if resource else None,
        )

    @staticmethod
    def _as_domain(db: Session, row: QueueVisitRecord) -> QueueVisit:
        resources = frozenset(db.scalars(
            select(QueueVisitResource.resource_id).where(
                QueueVisitResource.tenant_id == row.tenant_id,
                QueueVisitResource.visit_id == row.id,
            )
        ))
        return QueueVisit(
            visit_id=row.id,
            tenant_id=row.tenant_id,
            queue_id=row.queue_id,
            kind=VisitKind(row.visit_kind),
            status=VisitStatus(row.status),
            scheduled_at=_utc(row.scheduled_at_utc),
            arrival_confirmed_at=_utc(row.arrival_confirmed_at_utc),
            waiting_since=_utc(row.waiting_since_utc),
            queue_sequence=row.queue_sequence,
            resource_ids=resources,
            held_resource_id=row.held_resource_id,
            version=row.version,
        )

    @staticmethod
    def _resource_available(db: Session, tenant: str, resource_id: str) -> bool:
        return db.scalar(
            select(QueueVisitRecord.id).where(
                QueueVisitRecord.tenant_id == tenant,
                QueueVisitRecord.held_resource_id == resource_id,
            ).limit(1)
        ) is None

    @staticmethod
    def _commit_plan(
        db: Session, original: QueueVisitRecord, plan, now: datetime
    ) -> None:
        next_visit = plan.visit
        result = db.execute(
            update(QueueVisitRecord).where(
                QueueVisitRecord.id == original.id,
                QueueVisitRecord.tenant_id == original.tenant_id,
                QueueVisitRecord.version == original.version,
            ).values(
                status=next_visit.status.value,
                version=next_visit.version,
                arrival_confirmed_at_utc=_db_datetime(next_visit.arrival_confirmed_at),
                waiting_since_utc=_db_datetime(next_visit.waiting_since),
                queue_sequence=next_visit.queue_sequence,
                held_resource_id=next_visit.held_resource_id,
                closed_at_utc=(
                    _db_datetime(now) if next_visit.status in {
                        VisitStatus.DONE, VisitStatus.NO_SHOW,
                    } else None if next_visit.status is VisitStatus.WAITING
                    else original.closed_at_utc
                ),
            )
        )
        if result.rowcount != 1:
            raise QueueDomainError("VERSION_CONFLICT")
        for event in plan.events:
            db.add(QueueEventRecord(
                id=uuid4().hex,
                tenant_id=event.tenant_id,
                visit_ref=event.visit_id,
                aggregate_version=event.aggregate_version,
                event_type=event.event_type.value,
                state_before=event.state_before.value,
                state_after=event.state_after.value,
                occurred_at_utc=_db_datetime(event.occurred_at),
                actor_kind=event.actor_kind.value,
                actor_ref=event.actor_ref,
                reason_code=event.reason_code,
                method=event.method.value if event.method else None,
                resource_id=event.resource_id,
            ))

    def perform(
        self, token: str, command: HumanCommand, visit_id: str, *,
        expected_version: int,
        resource_id: str | None = None,
        reason_code: str | None = None,
    ) -> QueueVisitView:
        """Execute real domain command and persist visit+events behind both locks.

        Command/visit/resource/version are untrusted identifiers and are
        validated against tenant-scoped authoritative rows before use.
        Time and actor are taken from trusted server clock/session.
        """
        with self._transaction(token) as (db, principal, authorizer):
            if not isinstance(command, HumanCommand):
                _denied()
            row = self._visit(db, principal, visit_id)
            if type(expected_version) is not int or expected_version != row.version:
                raise QueueDomainError("VERSION_CONFLICT")
            if command in {HumanCommand.CALL, HumanCommand.RECALL, HumanCommand.CHAIR}:
                resource = self._resource(db, row, resource_id)
            elif command is HumanCommand.DONE:
                # DONE always uses the server-side held chair; no fabricated
                # client resource can alter which resource is released.
                if resource_id is not None and resource_id != row.held_resource_id:
                    _denied()
                resource = self._resource(db, row, row.held_resource_id)
            else:
                if resource_id is not None:
                    _denied()
                resource = None
            action = _ACTIONS[command]
            authorizer.require(token, action, self._target(row, resource))
            if reason_code is not None:
                if command not in {
                    HumanCommand.CHECK_IN, HumanCommand.CALL, HumanCommand.NO_SHOW,
                }:
                    raise QueueDomainError("AUDIT_REASON_UNEXPECTED")
                reason_code = _audit_reason(reason_code)
            now = as_utc(self._clock())
            current = self._as_domain(db, row)
            actor = principal.actor_id

            if command is HumanCommand.CHECK_IN:
                seq = db.scalar(
                    select(func.max(QueueVisitRecord.queue_sequence)).where(
                        QueueVisitRecord.tenant_id == row.tenant_id,
                        QueueVisitRecord.queue_id == row.queue_id,
                    )
                ) or 0
                plan = check_in(
                    current, at=now, actor_ref=actor,
                    method=CheckInMethod.STAFF, actor_kind=ActorKind.HUMAN,
                    queue_sequence=max(seq, current.queue_sequence or 0) + 1,
                    authorized=True, reentry_reason=reason_code,
                )
            elif command is HumanCommand.CALL:
                has_override = False
                if reason_code is not None:
                    authorizer.require(
                        token, Permission.QUEUE_OVERRIDE,
                        self._target(row, resource), reason=reason_code,
                    )
                    has_override = True
                candidates = [
                    self._as_domain(db, candidate)
                    for candidate in db.scalars(
                        select(QueueVisitRecord).where(
                            QueueVisitRecord.tenant_id == row.tenant_id,
                            QueueVisitRecord.queue_id == row.queue_id,
                            QueueVisitRecord.status == VisitStatus.WAITING.value,
                        )
                    )
                ]
                tenant = db.scalar(
                    select(QueueTenant).where(QueueTenant.id == row.tenant_id)
                )
                if tenant is None:
                    _denied()
                available = (
                    frozenset({resource.id})
                    if self._resource_available(db, row.tenant_id, resource.id)
                    else frozenset()
                )
                plan = call_visit(
                    current, at=now, actor_ref=actor, authorized=True,
                    candidates=candidates, resource_id=resource.id,
                    available_resource_ids=available,
                    tenant_timezone=tenant.timezone_name,
                    out_of_order_reason=reason_code, can_override=has_override,
                )
            elif command is HumanCommand.RECALL:
                plan = recall_visit(current, at=now, actor_ref=actor, authorized=True)
            elif command is HumanCommand.CHAIR:
                plan = move_to_chair(
                    current, at=now, actor_ref=actor, resource_id=resource.id,
                    resource_available=self._resource_available(
                        db, row.tenant_id, resource.id
                    ), authorized=True,
                )
            elif command is HumanCommand.DONE:
                plan = complete_visit(current, at=now, actor_ref=actor, authorized=True)
            else:
                plan = mark_no_show(
                    current, at=now, actor_ref=actor, actor_kind=ActorKind.HUMAN,
                    reason_code=_audit_reason(reason_code), authorized=True,
                )
            self._commit_plan(db, row, plan, now)
            return QueueVisitView(
                row.id, row.queue_id, plan.visit.status.value,
                plan.visit.version, plan.visit.queue_sequence,
            )

    def require_queue_read(self, token: str, queue_id: str) -> None:
        """Fail closed on every future stream frame, including buffered frames.

        Caller MUST invoke immediately before yielding each SSE event or
        heartbeat. This is a fresh protected DB lookup, not cached authorizer.
        """
        with self._transaction(token) as (db, principal, authorizer):
            self._queue(db, principal.tenant_id, queue_id)
            authorizer.require(
                token, Permission.QUEUE_READ,
                TargetScope(principal.tenant_id, queue_id),
            )

    def queue_snapshot(self, token: str, queue_id: str) -> tuple[QueueVisitView, ...]:
        """Read only minimal queue facts; recheck live session every call."""
        with self._transaction(token) as (db, principal, authorizer):
            self._queue(db, principal.tenant_id, queue_id)
            authorizer.require(
                token, Permission.QUEUE_READ,
                TargetScope(principal.tenant_id, queue_id),
            )
            rows = db.scalars(
                select(QueueVisitRecord).where(
                    QueueVisitRecord.tenant_id == principal.tenant_id,
                    QueueVisitRecord.queue_id == queue_id,
                ).order_by(QueueVisitRecord.id)
            )
            return tuple(
                QueueVisitView(row.id, row.queue_id, row.status, row.version, row.queue_sequence)
                for row in rows
            )

    def replay_events(
        self, token: str, queue_id: str, *,
        after_event_id: str | None = None,
        limit: int = 100,
    ) -> tuple[QueueEventView, ...]:
        """Bounded, reauthorized event polling, NOT a long-lived SSE stream.

        Every page / future poll MUST repeat authorization; cross-tenant or
        different-queue cursors are refused. Events for purged visits cannot be
        safely queue-scoped and are deliberately omitted, not disclosed.
        """
        with self._transaction(token) as (db, principal, authorizer):
            self._queue(db, principal.tenant_id, queue_id)
            authorizer.require(
                token, Permission.QUEUE_READ,
                TargetScope(principal.tenant_id, queue_id),
            )
            if type(limit) is not int or not 1 <= limit <= 100:
                _denied()
            match_queue = and_(
                QueueEventRecord.tenant_id == QueueVisitRecord.tenant_id,
                QueueEventRecord.visit_ref == QueueVisitRecord.id,
            )
            if after_event_id is not None:
                if not isinstance(after_event_id, str) or len(after_event_id) > 128:
                    _denied()
                cursor = db.scalar(
                    select(QueueEventRecord).join(QueueVisitRecord, match_queue).where(
                        QueueEventRecord.id == after_event_id,
                        QueueVisitRecord.tenant_id == principal.tenant_id,
                        QueueVisitRecord.queue_id == queue_id,
                    )
                )
                if cursor is None:
                    _denied()
                # Stable total order. Several domain events often share an
                # identical UTC timestamp; ID-only ordering would scramble
                # aggregate versions in paged replay.
                same_time = QueueEventRecord.occurred_at_utc == cursor.occurred_at_utc
                same_visit = QueueEventRecord.visit_ref == cursor.visit_ref
                checkpoint = or_(
                    QueueEventRecord.occurred_at_utc > cursor.occurred_at_utc,
                    and_(same_time, QueueEventRecord.visit_ref > cursor.visit_ref),
                    and_(
                        same_time, same_visit,
                        QueueEventRecord.aggregate_version > cursor.aggregate_version,
                    ),
                    and_(
                        same_time, same_visit,
                        QueueEventRecord.aggregate_version == cursor.aggregate_version,
                        QueueEventRecord.id > cursor.id,
                    ),
                )
            else:
                checkpoint = True
            records = db.scalars(
                select(QueueEventRecord).join(QueueVisitRecord, match_queue).where(
                    QueueVisitRecord.tenant_id == principal.tenant_id,
                    QueueVisitRecord.queue_id == queue_id,
                    checkpoint,
                ).order_by(
                    QueueEventRecord.occurred_at_utc,
                    QueueEventRecord.visit_ref,
                    QueueEventRecord.aggregate_version,
                    QueueEventRecord.id,
                ).limit(limit)
            )
            return tuple(
                QueueEventView(
                    item.id, item.visit_ref, item.event_type,
                    item.aggregate_version, _utc(item.occurred_at_utc),
                )
                for item in records
            )
