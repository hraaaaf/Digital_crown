from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PartnerSupplierInvoice(Base):
    """Facture fournisseur liée à une commande Marketplace, idempotente et tenant-scoped."""

    __tablename__ = "partner_supplier_invoices"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "order_id",
            "invoice_key",
            name="uq_partner_supplier_invoice_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_key: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_reference: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    amount_total: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)
