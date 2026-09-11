"""Media Core: tenant-scoped clinical asset metadata, provenance and storage state.

C1 introduced the storage-independent ClinicalAsset registry. C2 adds only the metadata
needed to bind an asset to an encrypted content-addressed blob. Import APIs, derivatives,
thumbnails and UI remain later lots.
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

CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1 = "AESGCM_V1"


class ClinicalAsset(Base):
    """Tenant-scoped registry entry for patient clinical media.

    `employer_id` is the tenant authority. `patient_id` must belong to the same employer;
    that invariant is enforced by the creation/storage services before persistence.

    `storage_key` is always a relative, non-patient-identifying key beneath MEDIA_ROOT.
    It never contains an original filename and must never be exposed as a public URL.
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
        Index(
            "ix_clinical_assets_tenant_sha256",
            "employer_id",
            "sha256",
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
    # C1 could record a supplied digest as metadata. Once C2 storage is bound this value
    # is overwritten with the digest computed server-side from plaintext bytes.
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # C2 physical-storage binding. The key is relative to MEDIA_ROOT and content-addressed.
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    storage_format: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    stored_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Longitudinal label only. Media Core does not interpret T0/T1/T2 clinically.
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
