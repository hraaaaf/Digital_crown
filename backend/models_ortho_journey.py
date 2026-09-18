from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models_base import Base


class OrthoCase(Base):
    """Durable orthodontic treatment lifecycle.

    This table stores practitioner workflow state only. It must never encode or
    infer diagnosis, severity, treatment success/failure, or treatment quality.
    """

    __tablename__ = "ortho_cases"
    __table_args__ = (
        Index(
            "ix_ortho_cases_employer_patient_status",
            "employer_id",
            "patient_id",
            "lifecycle_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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
