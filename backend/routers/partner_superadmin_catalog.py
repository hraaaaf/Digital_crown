from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_governance import MarketplaceGovernanceEvent
from backend.routers.auth import require_superadmin
from backend.routers.partner_catalog import (
    ProductCreateIn,
    ProductUpdateIn,
    SupplierUpdateIn,
    _coerce_availability,
    _serialize_product,
    _serialize_supplier,
)

# Monté dans partner_superadmin.router, qui porte déjà /marketplace.
router = APIRouter()


class GlobalSupplierCreateIn(BaseModel):
    confirm: bool = False
    employerId: int
    supplierKey: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    badge: Optional[str] = None
    description: Optional[str] = None
    promise: Optional[str] = None
    apiBaseUrl: Optional[str] = None
    syncMode: Optional[str] = "manual"
    isActive: bool = True


class GlobalSupplierUpdateIn(SupplierUpdateIn):
    confirm: bool = False
    name: Optional[str] = None


class GlobalProductCreateIn(ProductCreateIn):
    confirm: bool = False
    employerId: int


class GlobalProductUpdateIn(ProductUpdateIn):
    confirm: bool = False


def _require_confirm(value: bool) -> None:
    if value is not True:
        raise HTTPException(status_code=409, detail="Confirmation explicite requise pour une mutation Marketplace globale.")


def _clean_required(value: str, label: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail=f"{label} ne peut pas être vide")
    return cleaned


def _owner_exists(db: Session, employer_id: int) -> models.User:
    owner = (
        db.query(models.User)
        .filter(
            models.User.id == employer_id,
            models.User.employer_id.is_(None),
            models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE]),
        )
        .first()
    )
    if not owner:
        raise HTTPException(status_code=404, detail="Cabinet cible introuvable")
    return owner


def _audit(
    db: Session,
    admin: models.User,
    employer_id: int,
    entity_type: str,
    entity_id: str,
    action: str,
    payload: dict,
) -> None:
    db.add(MarketplaceGovernanceEvent(
        admin_user_id=admin.id,
        employer_id=employer_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload_json=payload,
    ))


def _supplier(db: Session, supplier_id: int):
    item = db.query(models.PartnerSupplier).filter(models.PartnerSupplier.id == supplier_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Fournisseur Marketplace introuvable")
    return item


def _product(db: Session, product_id: int):
    item = db.query(models.PartnerCatalogProduct).filter(models.PartnerCatalogProduct.id == product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produit Marketplace introuvable")
    return item


def _ensure_supplier_key_available(db: Session, employer_id: int, supplier_key: str) -> None:
    key = supplier_key.strip().lower()
    existing = (
        db.query(models.PartnerSupplier.id)
        .filter(
            models.PartnerSupplier.employer_id == employer_id,
            func.lower(models.PartnerSupplier.supplier_key) == key,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Cette clé fournisseur existe déjà pour ce cabinet")


def _ensure_product_identity_available(
    db: Session,
    *,
    supplier_id: int,
    sku: str,
    external_product_id: Optional[str],
    exclude_product_id: Optional[int] = None,
) -> None:
    sku_query = db.query(models.PartnerCatalogProduct.id).filter(
        models.PartnerCatalogProduct.supplier_id == supplier_id,
        func.lower(models.PartnerCatalogProduct.sku) == sku.strip().lower(),
    )
    if exclude_product_id is not None:
        sku_query = sku_query.filter(models.PartnerCatalogProduct.id != exclude_product_id)
    if sku_query.first():
        raise HTTPException(status_code=409, detail="SKU déjà utilisé pour ce fournisseur")

    external = (external_product_id or "").strip()
    if not external:
        return
    external_query = db.query(models.PartnerCatalogProduct.id).filter(
        models.PartnerCatalogProduct.supplier_id == supplier_id,
        func.lower(models.PartnerCatalogProduct.external_product_id) == external.lower(),
    )
    if exclude_product_id is not None:
        external_query = external_query.filter(models.PartnerCatalogProduct.id != exclude_product_id)
    if external_query.first():
        raise HTTPException(status_code=409, detail="externalProductId déjà utilisé pour ce fournisseur")


@router.get("/suppliers")
def global_suppliers(
    employerId: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    query = db.query(models.PartnerSupplier)
    if employerId is not None:
        query = query.filter(models.PartnerSupplier.employer_id == employerId)
    items = query.order_by(
        models.PartnerSupplier.employer_id.asc(),
        models.PartnerSupplier.name.asc(),
    ).limit(limit).all()
    return [{"employerId": item.employer_id, **_serialize_supplier(item)} for item in items]


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_global_supplier(
    payload: GlobalSupplierCreateIn,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    _require_confirm(payload.confirm)
    _owner_exists(db, payload.employerId)
    supplier_key = _clean_required(payload.supplierKey, "supplierKey")
    name = _clean_required(payload.name, "name")
    _ensure_supplier_key_available(db, payload.employerId, supplier_key)

    item = models.PartnerSupplier(
        employer_id=payload.employerId,
        supplier_key=supplier_key,
        name=name,
        badge=payload.badge,
        description=payload.description,
        promise=payload.promise,
        api_base_url=payload.apiBaseUrl,
        sync_mode=payload.syncMode,
        is_active=payload.isActive,
    )
    db.add(item)
    db.flush()
    _audit(
        db,
        admin,
        payload.employerId,
        "SUPPLIER",
        str(item.id),
        "SUPPLIER_CREATED",
        {"supplierKey": item.supplier_key, "name": item.name},
    )
    db.commit()
    db.refresh(item)
    return {"employerId": item.employer_id, **_serialize_supplier(item)}


@router.patch("/suppliers/{supplier_id}")
def update_global_supplier(
    supplier_id: int,
    payload: GlobalSupplierUpdateIn,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    _require_confirm(payload.confirm)
    item = _supplier(db, supplier_id)
    before = _serialize_supplier(item)
    if payload.name is not None:
        item.name = _clean_required(payload.name, "name")
    if payload.badge is not None:
        item.badge = payload.badge
    if payload.description is not None:
        item.description = payload.description
    if payload.promise is not None:
        item.promise = payload.promise
    if payload.apiBaseUrl is not None:
        item.api_base_url = payload.apiBaseUrl
    if payload.syncMode is not None:
        item.sync_mode = payload.syncMode
    if payload.isActive is not None:
        item.is_active = payload.isActive
    db.flush()
    after = _serialize_supplier(item)
    if before == after:
        db.rollback()
        raise HTTPException(status_code=422, detail="Aucune modification fournisseur")
    _audit(
        db,
        admin,
        item.employer_id,
        "SUPPLIER",
        str(item.id),
        "SUPPLIER_UPDATED",
        {"before": before, "after": after},
    )
    db.commit()
    db.refresh(item)
    return {"employerId": item.employer_id, **_serialize_supplier(item)}


@router.get("/products")
def global_products(
    employerId: Optional[int] = Query(None),
    supplierId: Optional[int] = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    query = db.query(models.PartnerCatalogProduct)
    if employerId is not None:
        query = query.filter(models.PartnerCatalogProduct.employer_id == employerId)
    if supplierId is not None:
        query = query.filter(models.PartnerCatalogProduct.supplier_id == supplierId)
    items = query.order_by(
        models.PartnerCatalogProduct.employer_id.asc(),
        models.PartnerCatalogProduct.id.asc(),
    ).limit(limit).all()
    return [{"employerId": item.employer_id, **_serialize_product(item)} for item in items]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_global_product(
    payload: GlobalProductCreateIn,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    _require_confirm(payload.confirm)
    _owner_exists(db, payload.employerId)
    supplier = _supplier(db, payload.supplierId)
    if supplier.employer_id != payload.employerId:
        raise HTTPException(status_code=409, detail="Le fournisseur n'appartient pas au cabinet cible")

    name = _clean_required(payload.name, "name")
    sku = _clean_required(payload.sku, "sku")
    category = _clean_required(payload.dentalCategory, "dentalCategory")
    specialty = _clean_required(payload.dentalSpecialty, "dentalSpecialty")
    unit = _clean_required(payload.unit, "unit")
    external_id = (payload.externalProductId or "").strip() or None
    _ensure_product_identity_available(
        db,
        supplier_id=supplier.id,
        sku=sku,
        external_product_id=external_id,
    )

    item = models.PartnerCatalogProduct(
        employer_id=payload.employerId,
        supplier_id=supplier.id,
        external_product_id=external_id,
        name=name,
        sku=sku,
        dental_category=category,
        dental_specialty=specialty,
        unit=unit,
        price=payload.price,
        availability=_coerce_availability(payload.availability),
        short_description=payload.shortDescription,
        long_description=payload.longDescription,
        benefits_json=payload.benefits,
        is_featured=payload.isFeatured,
        sort_order=payload.sortOrder,
    )
    db.add(item)
    db.flush()
    _audit(
        db,
        admin,
        payload.employerId,
        "PRODUCT",
        str(item.id),
        "PRODUCT_CREATED",
        {"sku": item.sku, "name": item.name},
    )
    db.commit()
    db.refresh(item)
    return {"employerId": item.employer_id, **_serialize_product(item)}


@router.patch("/products/{product_id}")
def update_global_product(
    product_id: int,
    payload: GlobalProductUpdateIn,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    _require_confirm(payload.confirm)
    item = _product(db, product_id)
    before = _serialize_product(item)

    target_supplier = item.supplier
    if payload.supplierId is not None:
        target_supplier = _supplier(db, payload.supplierId)
        if target_supplier.employer_id != item.employer_id:
            raise HTTPException(status_code=409, detail="Transfert produit cross-cabinet interdit")

    final_sku = _clean_required(payload.sku, "sku") if payload.sku is not None else item.sku
    final_external = (
        (payload.externalProductId or "").strip() or None
        if payload.externalProductId is not None
        else item.external_product_id
    )
    _ensure_product_identity_available(
        db,
        supplier_id=target_supplier.id,
        sku=final_sku,
        external_product_id=final_external,
        exclude_product_id=item.id,
    )

    if payload.supplierId is not None:
        item.supplier_id = target_supplier.id
    if payload.externalProductId is not None:
        item.external_product_id = final_external
    if payload.name is not None:
        item.name = _clean_required(payload.name, "name")
    if payload.sku is not None:
        item.sku = final_sku
    if payload.dentalCategory is not None:
        item.dental_category = _clean_required(payload.dentalCategory, "dentalCategory")
    if payload.dentalSpecialty is not None:
        item.dental_specialty = _clean_required(payload.dentalSpecialty, "dentalSpecialty")
    if payload.unit is not None:
        item.unit = _clean_required(payload.unit, "unit")
    if payload.price is not None:
        item.price = payload.price
    if payload.availability is not None:
        item.availability = _coerce_availability(payload.availability)
    if payload.shortDescription is not None:
        item.short_description = payload.shortDescription
    if payload.longDescription is not None:
        item.long_description = payload.longDescription
    if payload.benefits is not None:
        item.benefits_json = payload.benefits
    if payload.isFeatured is not None:
        item.is_featured = payload.isFeatured
    if payload.sortOrder is not None:
        item.sort_order = payload.sortOrder

    db.flush()
    after = _serialize_product(item)
    if before == after:
        db.rollback()
        raise HTTPException(status_code=422, detail="Aucune modification produit")
    _audit(
        db,
        admin,
        item.employer_id,
        "PRODUCT",
        str(item.id),
        "PRODUCT_UPDATED",
        {"before": before, "after": after},
    )
    db.commit()
    db.refresh(item)
    return {"employerId": item.employer_id, **_serialize_product(item)}
