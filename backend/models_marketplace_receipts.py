from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PartnerOrderReceipt(Base):
    """Réception locale idempotente, partielle ou complète, d'une commande partenaire."""

    __tablename__ = "partner_order_receipts"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "order_id",
            "receipt_key",
            name="uq_partner_order_receipts_idempotency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receipt_key: Mapped[str] = mapped_column(String(128), nullable=False)
    received_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    lines_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
