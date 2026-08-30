from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import is_superadmin_user, require_permission, require_superadmin

router = APIRouter()


PARTNER_CATEGORIES = [
    "Consommables",
    "Restauration",
    "Endodontie",
    "Instrumentation",
    "Implantologie",
    "Orthodontie",
    "Prophylaxie",
    "Imagerie",
]

PARTNER_SPECIALTIES = [
    "Omnipratique",
    "Orthodontie",
    "Parodontie",
    "Chirurgie orale",
    "Prothèse",
    "Endodontie",
    "Dentisterie pédiatrique",
    "Implantologie",
]


class SupplierCreateIn(BaseModel):
    supplierKey: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    badge: Optional[str] = None
    description: Optional[str] = None
    promise: Optional[str] = None
    apiBaseUrl: Optional[str] = None
    syncMode: Optional[str] = "manual"
    isActive: bool = True


class SupplierUpdateIn(BaseModel):
    badge: Optional[str] = None
    description: Optional[str] = None
    promise: Optional[str] = None
    apiBaseUrl: Optional[str] = None
    syncMode: Optional[str] = None
    isActive: Optional[bool] = None


class ProductCreateIn(BaseModel):
    supplierId: int
    externalProductId: Optional[str] = None
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    dentalCategory: str = Field(..., min_length=1)
    dentalSpecialty: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    availability: str = Field(..., min_length=1)
    shortDescription: Optional[str] = None
    longDescription: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    isFeatured: bool = False
    sortOrder: int = 0


class ProductUpdateIn(BaseModel):
    supplierId: Optional[int] = None
    externalProductId: Optional[str] = None
    name: Optional[str] = None
    sku: Optional[str] = None
    dentalCategory: Optional[str] = None
    dentalSpecialty: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    availability: Optional[str] = None
    shortDescription: Optional[str] = None
    longDescription: Optional[str] = None
    benefits: Optional[List[str]] = None
    isFeatured: Optional[bool] = None
    sortOrder: Optional[int] = None


def _serialize_supplier(supplier: models.PartnerSupplier) -> dict:
    return {
        "id": supplier.id,
        "supplierKey": supplier.supplier_key,
        "name": supplier.name,
        "badge": supplier.badge,
        "description": supplier.description,
        "promise": supplier.promise,
        "apiBaseUrl": supplier.api_base_url,
        "syncMode": supplier.sync_mode,
        "isActive": supplier.is_active,
        "productCount": len(supplier.products),
        "createdAt": supplier.created_at.isoformat() if supplier.created_at else None,
        "updatedAt": supplier.updated_at.isoformat() if supplier.updated_at else None,
    }


def _serialize_product(product: models.PartnerCatalogProduct) -> dict:
    return {
        "id": product.id,
        "supplierId": product.supplier_id,
        "supplierName": product.supplier.name if product.supplier else None,
        "externalProductId": product.external_product_id,
        "name": product.name,
        "sku": product.sku,
        "dentalCategory": product.dental_category,
        "dentalSpecialty": product.dental_specialty,
        "unit": product.unit,
        "price": product.price,
        "availability": product.availability.value,
        "shortDescription": product.short_description,
        "longDescription": product.long_description,
        "benefits": product.benefits_json,
        "isFeatured": product.is_featured,
        "sortOrder": product.sort_order,
        "createdAt": product.created_at.isoformat() if product.created_at else None,
        "updatedAt": product.updated_at.isoformat() if product.updated_at else None,
    }


def _coerce_availability(value: str) -> models.PartnerProductAvailability:
    try:
        return models.PartnerProductAvailability(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"Disponibilite invalide: {value}") from error


def _validate_pagination(offset: int, limit: Optional[int], *, max_limit: int) -> None:
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset doit etre positif ou nul.")
    if limit is not None and (limit < 1 or limit > max_limit):
        raise HTTPException(status_code=422, detail=f"limit doit etre compris entre 1 et {max_limit}.")


def _get_supplier_or_404(db: Session, employer_id: int, supplier_id: int) -> models.PartnerSupplier:
    supplier = (
        db.query(models.PartnerSupplier)
        .filter(models.PartnerSupplier.id == supplier_id, models.PartnerSupplier.employer_id == employer_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur partenaire introuvable")
    return supplier


def _get_product_or_404(db: Session, employer_id: int, product_id: int) -> models.PartnerCatalogProduct:
    product = (
        db.query(models.PartnerCatalogProduct)
        .filter(models.PartnerCatalogProduct.id == product_id, models.PartnerCatalogProduct.employer_id == employer_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit partenaire introuvable")
    return product


def _ensure_supplier_visible(supplier: models.PartnerSupplier, current_user: models.User) -> None:
    if not supplier.is_active and not is_superadmin_user(current_user):
        raise HTTPException(status_code=404, detail="Fournisseur partenaire introuvable")


def _ensure_product_visible(product: models.PartnerCatalogProduct, current_user: models.User) -> None:
    if product.supplier and not product.supplier.is_active and not is_superadmin_user(current_user):
        raise HTTPException(status_code=404, detail="Produit partenaire introuvable")


@router.get("/meta")
def get_partner_catalog_meta(current_user: models.User = Depends(require_permission("patients"))):
    return {
        "categories": PARTNER_CATEGORIES,
        "specialties": PARTNER_SPECIALTIES,
        "availability": [item.value for item in models.PartnerProductAvailability],
    }


@router.get("/suppliers")
def list_suppliers(
    offset: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    _validate_pagination(offset, limit, max_limit=200)
    employer_id = current_user.get_employer_id()
    query = db.query(models.PartnerSupplier).filter(models.PartnerSupplier.employer_id == employer_id)
    if not is_superadmin_user(current_user):
        query = query.filter(models.PartnerSupplier.is_active.is_(True))
    query = query.order_by(models.PartnerSupplier.name.asc()).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    suppliers = query.all()
    return [_serialize_supplier(supplier) for supplier in suppliers]


@router.get("/suppliers/{supplier_id}")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    supplier = _get_supplier_or_404(db, employer_id, supplier_id)
    _ensure_supplier_visible(supplier, current_user)
    return _serialize_supplier(supplier)


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    existing = (
        db.query(models.PartnerSupplier)
        .filter(
            models.PartnerSupplier.employer_id == employer_id,
            models.PartnerSupplier.supplier_key == payload.supplierKey,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Un fournisseur avec cette cle existe deja.")

    supplier = models.PartnerSupplier(
        employer_id=employer_id,
        supplier_key=payload.supplierKey,
        name=payload.name,
        badge=payload.badge,
        description=payload.description,
        promise=payload.promise,
        api_base_url=payload.apiBaseUrl,
        sync_mode=payload.syncMode,
        is_active=payload.isActive,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return _serialize_supplier(supplier)


@router.patch("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    supplier = _get_supplier_or_404(db, employer_id, supplier_id)

    if payload.badge is not None:
        supplier.badge = payload.badge
    if payload.description is not None:
        supplier.description = payload.description
    if payload.promise is not None:
        supplier.promise = payload.promise
    if payload.apiBaseUrl is not None:
        supplier.api_base_url = payload.apiBaseUrl
    if payload.syncMode is not None:
        supplier.sync_mode = payload.syncMode
    if payload.isActive is not None:
        supplier.is_active = payload.isActive

    db.commit()
    db.refresh(supplier)
    return _serialize_supplier(supplier)


@router.get("/products")
def list_products(
    supplier_id: Optional[int] = Query(default=None),
    category: Optional[str] = Query(default=None),
    specialty: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    offset: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    _validate_pagination(offset, limit, max_limit=500)
    employer_id = current_user.get_employer_id()
    query = (
        db.query(models.PartnerCatalogProduct)
        .filter(models.PartnerCatalogProduct.employer_id == employer_id)
        .join(models.PartnerSupplier)
    )
    if not is_superadmin_user(current_user):
        query = query.filter(models.PartnerSupplier.is_active.is_(True))
    if supplier_id:
        query = query.filter(models.PartnerCatalogProduct.supplier_id == supplier_id)
    if category:
        query = query.filter(models.PartnerCatalogProduct.dental_category == category)
    if specialty:
        query = query.filter(models.PartnerCatalogProduct.dental_specialty == specialty)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(
            models.PartnerCatalogProduct.name.ilike(pattern) |
            models.PartnerCatalogProduct.sku.ilike(pattern) |
            models.PartnerCatalogProduct.short_description.ilike(pattern) |
            models.PartnerCatalogProduct.long_description.ilike(pattern)
        )
    query = query.order_by(
        models.PartnerCatalogProduct.dental_category.asc(),
        models.PartnerCatalogProduct.dental_specialty.asc(),
        models.PartnerCatalogProduct.sort_order.asc(),
        models.PartnerCatalogProduct.name.asc(),
    ).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    products = query.all()
    return [_serialize_product(product) for product in products]


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    product = _get_product_or_404(db, employer_id, product_id)
    _ensure_product_visible(product, current_user)
    return _serialize_product(product)


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    _get_supplier_or_404(db, employer_id, payload.supplierId)

    product = models.PartnerCatalogProduct(
        employer_id=employer_id,
        supplier_id=payload.supplierId,
        external_product_id=payload.externalProductId,
        name=payload.name,
        sku=payload.sku,
        dental_category=payload.dentalCategory,
        dental_specialty=payload.dentalSpecialty,
        unit=payload.unit,
        price=payload.price,
        availability=_coerce_availability(payload.availability),
        short_description=payload.shortDescription,
        long_description=payload.longDescription,
        benefits_json=payload.benefits,
        is_featured=payload.isFeatured,
        sort_order=payload.sortOrder,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _serialize_product(product)


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    product = _get_product_or_404(db, employer_id, product_id)

    if payload.supplierId is not None:
        _get_supplier_or_404(db, employer_id, payload.supplierId)
        product.supplier_id = payload.supplierId
    if payload.externalProductId is not None:
        product.external_product_id = payload.externalProductId
    if payload.name is not None:
        product.name = payload.name
    if payload.sku is not None:
        product.sku = payload.sku
    if payload.dentalCategory is not None:
        product.dental_category = payload.dentalCategory
    if payload.dentalSpecialty is not None:
        product.dental_specialty = payload.dentalSpecialty
    if payload.unit is not None:
        product.unit = payload.unit
    if payload.price is not None:
        product.price = payload.price
    if payload.availability is not None:
        product.availability = _coerce_availability(payload.availability)
    if payload.shortDescription is not None:
        product.short_description = payload.shortDescription
    if payload.longDescription is not None:
        product.long_description = payload.longDescription
    if payload.benefits is not None:
        product.benefits_json = payload.benefits
    if payload.isFeatured is not None:
        product.is_featured = payload.isFeatured
    if payload.sortOrder is not None:
        product.sort_order = payload.sortOrder

    db.commit()
    db.refresh(product)
    return _serialize_product(product)
