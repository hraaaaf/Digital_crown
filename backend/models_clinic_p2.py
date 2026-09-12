from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PatientPractitionerAssignment(Base):
    """Additive patient -> practitioner context without rewriting the local patient row.

    Existing patient/document storage remains canonical and untouched. One assignment
    row can exist per patient; clearing the practitioner preserves the patient itself.
    """

    __tablename__ = "patient_practitioner_assignments"
    __table_args__ = (
        UniqueConstraint("patient_id", name="uq_patient_practitioner_assignment_patient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    practitioner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
