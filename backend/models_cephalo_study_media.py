"""DC-DOS-05 candidate only: explicit, write-once study ↔ original ClinicalAsset binding.

NOT registered in backend/__init__.py and NOT migrated into an existing cabinet.
The table is created ONLY by synthetic isolated test metadata.create_all(), until
a separate, explicitly approved clinical migration and release gate.
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class CephaloStudyMediaBinding(Base):
    __tablename__ = "cephalo_study_media_bindings"
    __table_args__ = (
        UniqueConstraint("study_id", "role", name="uq_ceph_study_media_role_write_once"),
        CheckConstraint(
            "role IN ('RADIO_SOURCE','PHOTO_CONTEXT')",
            name="ck_ceph_study_media_role",
        ),
        CheckConstraint("revision >= 1", name="ck_ceph_study_media_revision"),
        CheckConstraint("length(asset_sha256) = 64", name="ck_ceph_study_media_sha256"),
        Index(
            "ix_ceph_study_media_tenant_patient_study",
            "employer_id", "patient_id", "study_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    study_id: Mapped[int] = mapped_column(
        ForeignKey("cephalo_analyses.id"), nullable=False, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("clinical_assets.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )
