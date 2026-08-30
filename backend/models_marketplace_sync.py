from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PartnerSupplierSyncState(Base):
    """État persistant de synchronisation d'un fournisseur Marketplace."""

    __tablename__ = "partner_supplier_sync_states"
    __table_args__ = (
        UniqueConstraint("employer_id", "supplier_id", name="uq_partner_supplier_sync_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("partner_suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_outcome: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    last_error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_payload_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_catalog_version: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    last_product_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
