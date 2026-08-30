from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class MarketplaceStockMapping(Base):
    """Mapping explicite produit Marketplace -> article de stock du cabinet."""

    __tablename__ = "marketplace_stock_mappings"
    __table_args__ = (
        UniqueConstraint("employer_id", "product_id", name="uq_marketplace_stock_mapping_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("partner_catalog_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_item_id: Mapped[int] = mapped_column(
        ForeignKey("stock_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_units_per_product_unit: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    min_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class MarketplaceStockMovement(Base):
    """Ledger append-only des mouvements stock issus du Marketplace ou de la consommation."""

    __tablename__ = "marketplace_stock_movements"
    __table_args__ = (
        UniqueConstraint("employer_id", "movement_key", name="uq_marketplace_stock_movement_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_item_id: Mapped[int] = mapped_column(
        ForeignKey("stock_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("partner_catalog_products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    receipt_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("partner_order_receipts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    movement_key: Mapped[str] = mapped_column(String(180), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity_delta: Mapped[float] = mapped_column(Float, nullable=False)
    stock_quantity_after: Mapped[float] = mapped_column(Float, nullable=False)
    lot_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    allocations_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)


class MarketplaceStockLot(Base):
    """Solde lot/péremption pour les quantités réceptionnées via Marketplace."""

    __tablename__ = "marketplace_stock_lots"
    __table_args__ = (
        UniqueConstraint("employer_id", "stock_item_id", "lot_key", name="uq_marketplace_stock_lot_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_item_id: Mapped[int] = mapped_column(
        ForeignKey("stock_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("partner_catalog_products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lot_key: Mapped[str] = mapped_column(String(220), nullable=False)
    lot_number: Mapped[str] = mapped_column(String(120), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    first_received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
