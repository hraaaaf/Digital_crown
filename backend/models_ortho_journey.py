from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models_base import Base


class OrthoCase(Base):
    """Durable orthodontic treatment lifecycle.

    This table stores practitioner workflow state only. It must never encode or
    infer diagnosis, severity, treatment success/failure, or treatment quality.
    """

    __tablename__ = "ortho_cases"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('ACTIVE','INTERRUPTED','ABANDONED','CLOSED')",
            name="ck_ortho_cases_lifecycle_status",
        ),
        Index(
            "ix_ortho_cases_employer_patient_status",
            "employer_id",
            "patient_id",
            "lifecycle_status",
        ),
        Index(
            "uq_ortho_cases_one_open_per_patient",
            "employer_id",
            "patient_id",
            unique=True,
            postgresql_where=text("lifecycle_status IN ('ACTIVE','INTERRUPTED')"),
            sqlite_where=text("lifecycle_status IN ('ACTIVE','INTERRUPTED')"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    current_phase_key: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    patient = relationship("Patient", foreign_keys=[patient_id])
    events = relationship(
        "OrthoPhaseEvent",
        back_populates="ortho_case",
        cascade="all, delete-orphan",
        order_by="OrthoPhaseEvent.effective_at",
    )


class OrthoPhaseEvent(Base):
    """Append-only factual lifecycle/phase event for an OrthoCase."""

    __tablename__ = "ortho_phase_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('START','ENTER_PHASE','INTERRUPT','RESUME','ABANDON','CLOSE')",
            name="ck_ortho_phase_events_event_type",
        ),
        CheckConstraint(
            "phase_key IS NULL OR phase_key IN ('DIAGNOSTIC','PREPARATION','APPAREILLAGE','ALIGNEMENT','FINITION','CONTENTION','CLOTURE')",
            name="ck_ortho_phase_events_phase_key",
        ),
        CheckConstraint(
            "event_type <> 'ENTER_PHASE' OR phase_key IS NOT NULL",
            name="ck_ortho_phase_events_enter_phase_requires_phase",
        ),
        CheckConstraint(
            "event_type IN ('START','ENTER_PHASE') OR phase_key IS NULL",
            name="ck_ortho_phase_events_phase_only_on_start_or_enter",
        ),
        Index(
            "ix_ortho_phase_events_employer_patient_effective",
            "employer_id",
            "patient_id",
            "effective_at",
        ),
        Index(
            "ix_ortho_phase_events_case_effective",
            "ortho_case_id",
            "effective_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ortho_case_id: Mapped[int] = mapped_column(
        ForeignKey("ortho_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    phase_key: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    effective_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    ortho_case: Mapped[OrthoCase] = relationship(back_populates="events")


class OrthoControl(Base):
    """Structured factual orthodontic control checkpoint.

    A control records what the practitioner documented at a visit/checkpoint.
    It never infers diagnosis, severity, treatment quality, progress, or phase.
    """

    __tablename__ = "ortho_controls"
    __table_args__ = (
        CheckConstraint(
            "phase_key IS NULL OR phase_key IN ('DIAGNOSTIC','PREPARATION','APPAREILLAGE','ALIGNEMENT','FINITION','CONTENTION','CLOTURE')",
            name="ck_ortho_controls_phase_key",
        ),
        CheckConstraint(
            "next_control_at IS NULL OR next_control_at >= occurred_at",
            name="ck_ortho_controls_next_after_control",
        ),
        Index(
            "ix_ortho_controls_employer_patient_occurred",
            "employer_id",
            "patient_id",
            "occurred_at",
        ),
        Index(
            "ix_ortho_controls_case_occurred",
            "ortho_case_id",
            "occurred_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ortho_case_id: Mapped[int] = mapped_column(
        ForeignKey("ortho_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    appointment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    phase_key: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    appliance_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notable_event: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_planned_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_control_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    ortho_case: Mapped[OrthoCase] = relationship()
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
