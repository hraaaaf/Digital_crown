"""P4 recoverable imaging lifecycle metadata.

Clinical analysis rows and their files remain untouched when a user sends an image to
trash. This additive table records the lifecycle state without changing scientific data.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class ImagingTrashRecord(Base):
    __tablename__ = "imaging_trash_records"
    __table_args__ = (
        UniqueConstraint("modality", "analysis_id", name="uq_imaging_trash_modality_analysis"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    modality: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    analysis_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deleted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), index=True
    )
