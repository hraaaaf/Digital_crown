"""Versioned regulatory mapping between the clinical CatalogAct and NGAP.

This table is additive and intentionally empty by default. CatalogAct remains the
clinical source of truth. A row can only be used for automatic NGAP resolution when
its primary source is SHA-256 locked and the mapping itself was explicitly validated
by a practitioner.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class NgapCatalogMapping(Base):
    __tablename__ = "ngap_catalog_mappings"
    __table_args__ = (
        UniqueConstraint(
            "catalog_act_id",
            "reference_version",
            name="uq_ngap_catalog_mapping_act_version",
        ),
        CheckConstraint(
            "code_kind IN ('NGAP', 'INTERNAL', 'OTHER')",
            name="ck_ngap_mapping_code_kind",
        ),
        CheckConstraint(
            "verification_status IN ('PRIMARY_HASH_PENDING', 'VERIFIED_PRIMARY', 'OUTDATED')",
            name="ck_ngap_mapping_verification_status",
        ),
        CheckConstraint(
            "code_kind != 'NGAP' OR (ngap_code IS NOT NULL AND coefficient IS NOT NULL)",
            name="ck_ngap_mapping_ngap_payload",
        ),
        CheckConstraint(
            "verification_status != 'VERIFIED_PRIMARY' OR "
            "(source_hash IS NOT NULL AND length(source_hash) = 64 "
            "AND validated_by_practitioner_id IS NOT NULL AND validated_at IS NOT NULL)",
            name="ck_ngap_mapping_verified_evidence",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    catalog_act_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_acts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    code_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    ngap_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    coefficient: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    official_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requires_prior_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_radiograph: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reference_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mapping_rule_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)

    source_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    validated_by_practitioner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
