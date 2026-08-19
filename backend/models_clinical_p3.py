"""P3 clinical persistence models kept separate from the legacy models god-file.

The tables are registered on ``backend.models.Base.metadata`` as soon as this module is
imported. Patient routers import it before runtime access; P3 tests import it during
collection so SQLite test metadata includes the table before ``create_all``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class PatientOdontogram(Base):
    __tablename__ = "patient_odontograms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    dentition_type: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )


class ClinicalConclusion(Base):
    """Append-only practitioner-retained clinical conclusion.

    Assistant output, when supplied, is stored only as provenance in ``proposal_text``.
    It never becomes authoritative without the distinct practitioner-authored/
    confirmed ``conclusion_text`` and ``validated_by`` identity.
    """

    __tablename__ = "clinical_conclusions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conclusion_text: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposal_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    validated_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)
