"""J2.1 FUE-only candidate: append-only scene snapshots in isolated app test DB.

Never import via backend/__init__.py, never mount the candidate router in production.
No clinical migration and no patient or media migration. Synthetic fixtures only.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class CephPremiumSceneFueSnapshot(Base):
    __tablename__ = "ceph_premium_scene_fue_snapshots"
    __table_args__ = (
        UniqueConstraint("study_id", "scene_revision", name="uq_ceph_fue_study_revision"),
        UniqueConstraint("scene_sha256", name="uq_ceph_fue_snapshot_sha"),
        Index("ix_ceph_fue_scope", "employer_id", "patient_id", "study_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    study_id: Mapped[int] = mapped_column(ForeignKey("cephalo_analyses.id"), nullable=False)
    scene_revision: Mapped[int] = mapped_column(nullable=False)
    scene_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_scene_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), nullable=False)
