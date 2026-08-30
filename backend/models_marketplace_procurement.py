from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PartnerOrderProcurement(Base):
    """Accusé fournisseur local et état d'approvisionnement d'une commande partenaire."""

    __tablename__ = "partner_order_procurement"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "order_id",
            name="uq_partner_order_procurement_order",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_reference: Mapped[str] = mapped_column(String(120), nullable=False)
    expected_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    backorder_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
