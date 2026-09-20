from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PatientCompanionNotificationPreference(Base):
    """Per-access patient notification category preferences."""

    __tablename__ = "patient_companion_notification_preferences"
    __table_args__ = (
        UniqueConstraint("access_id", name="uq_pc_notification_preferences_access"),
        Index("ix_pc_notification_preferences_tenant_patient", "employer_id", "patient_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    appointments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    documents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    questionnaires: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PatientCompanionNotificationReceipt(Base):
    """Per-access interaction state for a projected patient notification.

    No title/body/domain payload is stored here: source_key points to canonical
    agenda/share/questionnaire/consent state.
    """

    __tablename__ = "patient_companion_notification_receipts"
    __table_args__ = (
        UniqueConstraint("access_id", "source_key", name="uq_pc_notification_receipt_access_source"),
        Index("ix_pc_notification_receipt_access_id", "access_id"),
        Index("ix_pc_notification_receipt_tenant_patient", "employer_id", "patient_id"),
        Index("ix_pc_notification_receipt_read_at", "read_at"),
        Index("ix_pc_notification_receipt_snoozed_until", "snoozed_until"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_key: Mapped[str] = mapped_column(String(180), nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
