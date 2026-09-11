"""Media Core C1: tenant-scoped clinical asset metadata and provenance.

This module is intentionally storage-agnostic. A ClinicalAsset identifies a patient media
asset and its provenance; file storage, ingestion, derivatives, thumbnails and deduplication
belong to later Media Core lots.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


CLINICAL_ASSET_TYPES = (
    "PHOTO",
    "RADIOGRAPH",
    "DOCUMENT",
    "VIDEO",
    "AUDIO",
    "OTHER",
)

CLINICAL_ASSET_SOURCE_KINDS = (
    "UPLOAD",
    "IMPORT",
    "DERIVED",
    "CLINICAL_ANALYSIS",
    "DEVICE_CAPTURE",
)


class ClinicalAsset(Base):
    """Storage-independent registry entry for patient clinical media.

    `employer_id` is the tenant authority. `patient_id` must belong to the same employer;
    that invariant is enforced by the creation service before persistence.
    """

    __tablename__ = "clinical_assets"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('PHOTO','RADIOGRAPH','DOCUMENT','VIDEO','AUDIO','OTHER')",
            name="ck_clinical_assets_asset_type",
        ),
        CheckConstraint(
            "source_kind IN ('UPLOAD','IMPORT','DERIVED','CLINICAL_ANALYSIS','DEVICE_CAPTURE')",
            name="ck_clinical_assets_source_kind",
        ),
        CheckConstraint(
            "byte_size IS NULL OR byte_size >= 0",
            name="ck_clinical_assets_byte_size_nonnegative",
        ),
        CheckConstraint(
            "sha256 IS NULL OR length(sha256) = 64",
            name="ck_clinical_assets_sha256_length",
        ),
        Index(
            "ix_clinical_assets_tenant_patient_created",
            "employer_id",
            "patient_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(127), nullable=True)
    byte_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # C1 records a supplied digest; C2 owns digest computation and dedupe semantics.
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Longitudinal label only. C1 does not interpret T0/T1/T2 clinically.
    timepoint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clinical_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provenance_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
