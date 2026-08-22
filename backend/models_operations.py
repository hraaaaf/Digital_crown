import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models_base import Base

class LabJobStatus(str, enum.Enum):
    PRESCRIPTION = "PRESCRIPTION"
    SENT = "SENT"
    IN_PROGRESS = "IN_PROGRESS"
    TRY_IN = "TRY_IN"
    READY = "READY"
    DELIVERED = "DELIVERED"

# ==============================================================================
# LAB JOBS — SUIVI DES TRAVAUX PROTHÉTIQUES
# ==============================================================================

class Lab(Base):
    """Laboratoire dentaire partenaire."""
    __tablename__ = "labs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class LabJob(Base):
    """Travail prothétique envoyé au laboratoire."""
    __tablename__ = "lab_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    act_id: Mapped[int] = mapped_column(ForeignKey("actes.id"), nullable=False)
    lab_id: Mapped[Optional[int]] = mapped_column(ForeignKey("labs.id"), nullable=True)

    material: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    shade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    tooth_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[LabJobStatus] = mapped_column(SQLEnum(LabJobStatus), default=LabJobStatus.PRESCRIPTION, nullable=False)
    is_remake: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient")
    act: Mapped["Acte"] = relationship("Acte")
    lab: Mapped[Optional["Lab"]] = relationship("Lab")

    @property
    def is_late(self) -> bool:
        if self.status in (LabJobStatus.READY, LabJobStatus.DELIVERED):
            return False
        return datetime.now() > self.deadline

# ==============================================================================
# STOCK — GESTION DES CONSOMMABLES ET MATÉRIAUX
# ==============================================================================

class StockCategorie(str, enum.Enum):
    CONSOMMABLE = "CONSOMMABLE"
    MATERIAU    = "MATERIAU"
    MEDICAMENT  = "MEDICAMENT"
    EQUIPEMENT  = "EQUIPEMENT"

class StockItem(Base):
    """Article de stock du cabinet (consommable, matériau, médicament, équipement)."""
    __tablename__ = "stock_items"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    nom:           Mapped[str]            = mapped_column(String(255), nullable=False)
    categorie:     Mapped[StockCategorie] = mapped_column(SQLEnum(StockCategorie), nullable=False)
    quantite:      Mapped[float]          = mapped_column(Float, nullable=False, default=0.0)
    seuil_alerte:  Mapped[float]          = mapped_column(Float, nullable=False, default=5.0)
    unite:         Mapped[str]            = mapped_column(String(50), nullable=False, default="unité")
    prix_unitaire: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fournisseur:   Mapped[Optional[str]]   = mapped_column(String(255), nullable=True)
    notes:         Mapped[Optional[str]]   = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# ==============================================================================
# PARTNER MARKETPLACE - COMMANDES PARTENAIRE
# ==============================================================================

class PartnerOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT_TO_PARTNER = "SENT_TO_PARTNER"
    MODIFIED_AFTER_SEND = "MODIFIED_AFTER_SEND"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class PartnerSettlementBasis(str, enum.Enum):
    SENT_TO_PARTNER = "SENT_TO_PARTNER"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"


class PartnerRevenueModel(str, enum.Enum):
    COMMISSION_PERCENT = "COMMISSION_PERCENT"
    DISCOUNT_RESALE = "DISCOUNT_RESALE"
    FIXED_FEE_PER_ORDER = "FIXED_FEE_PER_ORDER"


class PartnerProductAvailability(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_REQUEST = "ON_REQUEST"
    DISCONTINUED = "DISCONTINUED"


class PartnerOrder(Base):
    """Commande partenaire capturee dans DigitalCrown, isolee par cabinet."""
    __tablename__ = "partner_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    partner_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default-partner")
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Partenaire")
    status: Mapped[PartnerOrderStatus] = mapped_column(SQLEnum(PartnerOrderStatus), nullable=False, default=PartnerOrderStatus.DRAFT)
    settlement_basis: Mapped[PartnerSettlementBasis] = mapped_column(
        SQLEnum(PartnerSettlementBasis), nullable=False, default=PartnerSettlementBasis.SENT_TO_PARTNER
    )
    revenue_model: Mapped[PartnerRevenueModel] = mapped_column(
        SQLEnum(PartnerRevenueModel), nullable=False, default=PartnerRevenueModel.COMMISSION_PERCENT
    )
    strategy_label: Mapped[str] = mapped_column(String(255), nullable=False, default="Commission sur envoi")
    commission_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fixed_fee_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    customer_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_clinic: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_city: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    estimated_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sent_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recognized_base_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recognized_revenue_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    revenue_delta_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    partner_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_partner_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    events: Mapped[List["PartnerOrderEvent"]] = relationship(
        "PartnerOrderEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PartnerOrderEvent.created_at.desc()"
    )


class PartnerOrderEvent(Base):
    """Historique de recalcul et de statut pour audit commercial."""
    __tablename__ = "partner_order_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    new_status: Mapped[str] = mapped_column(String(60), nullable=False)
    previous_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_total: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_after: Mapped[float] = mapped_column(Float, nullable=False)
    delta_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    order: Mapped["PartnerOrder"] = relationship("PartnerOrder", back_populates="events")


class PartnerSupplier(Base):
    """Fournisseur partenaire du cabinet, configurable pour futur import API."""
    __tablename__ = "partner_suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    supplier_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sync_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="manual")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    products: Mapped[List["PartnerCatalogProduct"]] = relationship(
        "PartnerCatalogProduct",
        back_populates="supplier",
        cascade="all, delete-orphan",
        order_by="PartnerCatalogProduct.sort_order.asc(), PartnerCatalogProduct.name.asc()"
    )


class PartnerCatalogProduct(Base):
    """Produit catalogue partenaire, pret pour import externe et storefront."""
    __tablename__ = "partner_catalog_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("partner_suppliers.id", ondelete="CASCADE"), nullable=False, index=True)

    external_product_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dental_category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dental_specialty: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="unite")
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    availability: Mapped[PartnerProductAvailability] = mapped_column(
        SQLEnum(PartnerProductAvailability), nullable=False, default=PartnerProductAvailability.AVAILABLE
    )
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    supplier: Mapped["PartnerSupplier"] = relationship("PartnerSupplier", back_populates="products")
