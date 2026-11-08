"""Portable Queue Core persistence contract for 08.1.

These models define a separate schema only. They do not open a connection,
create tables, migrate a database, or import Digital Crown clinical models.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from queue_core.persistence.base import QueueBase


class QueueTenant(QueueBase):
    __tablename__ = "queue_tenants"
    __table_args__ = (UniqueConstraint("id", "timezone_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at_utc: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class QueueLine(QueueBase):
    __tablename__ = "queue_lines"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_queue_lines_tenant_id_id"),
        UniqueConstraint("tenant_id", "queue_key", name="uq_queue_lines_tenant_key"),
        ForeignKeyConstraint(["tenant_id"], ["queue_tenants.id"], ondelete="RESTRICT"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    queue_key: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class QueueResource(QueueBase):
    __tablename__ = "queue_resources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_queue_resources_tenant_id_id"),
        UniqueConstraint("tenant_id", "resource_key", name="uq_queue_resources_tenant_key"),
        ForeignKeyConstraint(["tenant_id"], ["queue_tenants.id"], ondelete="RESTRICT"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    resource_key: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class QueueVisitRecord(QueueBase):
    __tablename__ = "queue_visits"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_queue_visits_tenant_id_id"),
        UniqueConstraint("tenant_id", "queue_id", "queue_sequence", name="uq_queue_visits_queue_sequence"),
        # NULL occupancy permits multiple non-CHAIR visits, but one held chair per tenant.
        UniqueConstraint("tenant_id", "held_resource_id", name="uq_queue_visit_active_resource"),
        ForeignKeyConstraint(["tenant_id"], ["queue_tenants.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "queue_id"],
            ["queue_lines.tenant_id", "queue_lines.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "held_resource_id"],
            ["queue_resources.tenant_id", "queue_resources.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(status = 'CHAIR' AND held_resource_id IS NOT NULL) OR "
            "(status <> 'CHAIR' AND held_resource_id IS NULL)",
            name="ck_queue_held_resource_iff_chair",
        ),
        CheckConstraint(
            "(visit_kind = 'APPOINTMENT' AND scheduled_at_utc IS NOT NULL) OR "
            "(visit_kind = 'WALK_IN' AND scheduled_at_utc IS NULL)",
            name="ck_queue_visit_schedule_by_kind",
        ),
        CheckConstraint(
            "visit_kind IN ('APPOINTMENT', 'WALK_IN')",
            name="ck_queue_visit_kind",
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'EN_ROUTE', 'WAITING', 'CALLED', 'CHAIR', 'DONE', 'CANCELLED', 'NO_SHOW')",
            name="ck_queue_visit_status",
        ),
        CheckConstraint("version >= 0", name="ck_queue_visit_version_nonnegative"),
        Index("ix_queue_visits_tenant_queue_status", "tenant_id", "queue_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    queue_id: Mapped[str] = mapped_column(String(36), nullable=False)
    visit_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    scheduled_at_utc: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_confirmed_at_utc: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waiting_since_utc: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queue_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    public_ticket_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    held_resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    closed_at_utc: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QueueVisitResource(QueueBase):
    __tablename__ = "queue_visit_resources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "visit_id"],
            ["queue_visits.tenant_id", "queue_visits.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "resource_id"],
            ["queue_resources.tenant_id", "queue_resources.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_queue_visit_resources_resource", "tenant_id", "resource_id", "visit_id"),
    )

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    visit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(36), primary_key=True)


class QueueEventRecord(QueueBase):
    """Minimized append-only event facts; no unrestricted JSON payload."""

    __tablename__ = "queue_event_log"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "visit_ref", "aggregate_version", name="uq_queue_event_visit_version"
        ),
        ForeignKeyConstraint(["tenant_id"], ["queue_tenants.id"], ondelete="RESTRICT"),
        CheckConstraint("aggregate_version >= 1", name="ck_queue_event_version_positive"),
        CheckConstraint(
            "actor_kind IN ('HUMAN', 'DEVICE', 'SYSTEM')",
            name="ck_queue_event_actor_kind",
        ),
        CheckConstraint(
            "event_type IN ('ARRIVED', 'WAITING_ENTERED', 'CALLED', 'RECALLED', "
            "'ORDER_OVERRIDE', 'RESOURCE_CLAIMED', 'RESOURCE_RELEASED', 'CHAIR', "
            "'DONE', 'CANCELLED', 'NO_SHOW', 'UNLOCATED_AFTER_CALL', "
            "'RETURNED_TO_WAITING')",
            name="ck_queue_event_known_type",
        ),
        CheckConstraint(
            "state_before IN ('PLANNED', 'EN_ROUTE', 'WAITING', 'CALLED', "
            "'CHAIR', 'DONE', 'CANCELLED', 'NO_SHOW')",
            name="ck_queue_event_known_state_before",
        ),
        CheckConstraint(
            "state_after IN ('PLANNED', 'EN_ROUTE', 'WAITING', 'CALLED', "
            "'CHAIR', 'DONE', 'CANCELLED', 'NO_SHOW')",
            name="ck_queue_event_known_state_after",
        ),
        CheckConstraint(
            "(event_type NOT IN ('NO_SHOW', 'ORDER_OVERRIDE', "
            "'UNLOCATED_AFTER_CALL', 'RETURNED_TO_WAITING', 'CANCELLED')) OR "
            "(reason_code IS NOT NULL AND length(trim(reason_code)) > 0)",
            name="ck_queue_event_reason_required",
        ),
        CheckConstraint(
            "event_type <> 'NO_SHOW' OR actor_kind = 'HUMAN'",
            name="ck_queue_event_manual_no_show",
        ),
        CheckConstraint(
            "(event_type NOT IN ('ARRIVED', 'WAITING_ENTERED')) OR "
            "(method = 'STAFF' AND actor_kind = 'HUMAN') OR "
            "(method = 'KIOSK_QR' AND actor_kind = 'DEVICE')",
            name="ck_queue_event_method_actor_kind",
        ),
        CheckConstraint(
            "(event_type IN ('ARRIVED', 'WAITING_ENTERED') AND "
            "method IS NOT NULL AND method IN ('STAFF', 'KIOSK_QR')) OR "
            "(event_type NOT IN ('ARRIVED', 'WAITING_ENTERED') AND method IS NULL)",
            name="ck_queue_event_checkin_method",
        ),
        CheckConstraint(
            "(event_type IN ('RESOURCE_CLAIMED', 'RESOURCE_RELEASED') AND "
            "resource_id IS NOT NULL AND resource_id <> '') OR "
            "(event_type NOT IN ('RESOURCE_CLAIMED', 'RESOURCE_RELEASED') AND resource_id IS NULL)",
            name="ck_queue_event_resource_reference",
        ),
        Index("ix_queue_event_tenant_time", "tenant_id", "occurred_at_utc"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # This opaque reference intentionally survives visit-row purge so the
    # minimized audit window can outlive the identifiable visit window.
    visit_ref: Mapped[str] = mapped_column(String(36), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    state_before: Mapped[str] = mapped_column(String(24), nullable=False)
    state_after: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at_utc: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Opaque resource audit reference survives resource-row churn; no clinical FK.
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class QueueExternalReference(QueueBase):
    __tablename__ = "queue_external_references"
    __table_args__ = (
        # This 08.1 schema maps appointment references ONLY. Patient identity
        # mappings are deferred to LOT09 to avoid blocking repeat visits.
        CheckConstraint("entity_kind = 'APPOINTMENT'", name="ck_queue_external_kind_appointment"),
        UniqueConstraint(
            "tenant_id",
            "source_system",
            "entity_kind",
            "external_id",
            name="uq_queue_external_appointment",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "visit_id"],
            ["queue_visits.tenant_id", "queue_visits.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    visit_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
