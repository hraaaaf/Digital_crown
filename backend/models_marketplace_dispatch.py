from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class PartnerOrderDispatch(Base):
    """Preuve minimale et idempotente d'expédition externe d'une commande partenaire."""

    __tablename__ = "partner_order_dispatches"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "order_id",
            "idempotency_key",
            name="uq_partner_order_dispatch_idempotency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("partner_suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    transport: Mapped[str] = mapped_column(String(40), nullable=False, default="HTTP_API")
    endpoint: Mapped[str] = mapped_column(String(700), nullable=False)
    request_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    supplier_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
