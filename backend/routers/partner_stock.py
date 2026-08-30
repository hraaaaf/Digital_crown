import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.models_marketplace_stock import (
    MarketplaceStockLot,
    MarketplaceStockMapping,
    MarketplaceStockMovement,
)
from backend.routers.auth import require_permission, require_superadmin

router = APIRouter(prefix="/marketplace")


class StockMappingIn(BaseModel):
    stockItemId: int
    stockUnitsPerProductUnit: float = Field(1.0, gt=0)
    minQuantity: float = Field(0.0, ge=0)
    targetQuantity: float = Field(..., gt=0)
    isActive: bool = True


class StockConsumptionIn(BaseModel):
    quantity: float = Field(..., gt=0)
    idempotencyKey: str = Field(..., min_length=8, max_length=128)
    note: Optional[str] = None


def _as_float(value: float) -> float:
    return round(float(value), 6)


def _parse_datetime(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as error:
            raise HTTPException(status_code=409, detail=f"Date de péremption invalide: {value}") from error
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _mapping_payload(mapping: MarketplaceStockMapping, product, item) -> dict:
    return {
        "id": mapping.id,
        "productId": mapping.product_id,
        "productName": product.name if product else None,
        "sku": product.sku if product else None,
        "stockItemId": mapping.stock_item_id,
        "stockItemName": item.nom if item else None,
        "stockQuantity": _as_float(item.quantite) if item else None,
        "stockUnit": item.unite if item else None,
        "stockUnitsPerProductUnit": _as_float(mapping.stock_units_per_product_unit),
        "minQuantity": _as_float(mapping.min_quantity),
        "targetQuantity": _as_float(mapping.target_quantity),
        "isActive": bool(mapping.is_active),
    }


def _movement_payload(movement: MarketplaceStockMovement) -> dict:
    return {
        "id": movement.id,
        "stockItemId": movement.stock_item_id,
        "productId": movement.product_id,
        "receiptId": movement.receipt_id,
        "movementKey": movement.movement_key,
        "type": movement.movement_type,
        "quantityDelta": _as_float(movement.quantity_delta),
        "stockQuantityAfter": _as_float(movement.stock_quantity_after),
        "lotNumber": movement.lot_number,
        "expiresAt": movement.expires_at.isoformat() if movement.expires_at else None,
        "allocations": movement.allocations_json or [],
        "note": movement.note,
        "createdAt": movement.created_at.isoformat() if movement.created_at else None,
    }


def _lot_payload(lot: MarketplaceStockLot) -> dict:
    now = datetime.utcnow()
    return {
        "id": lot.id,
        "stockItemId": lot.stock_item_id,
        "productId": lot.product_id,
        "lotNumber": lot.lot_number,
        "expiresAt": lot.expires_at.isoformat() if lot.expires_at else None,
        "quantity": _as_float(lot.quantity),
        "expired": bool(lot.expires_at and lot.expires_at < now),
        "firstReceivedAt": lot.first_received_at.isoformat() if lot.first_received_at else None,
    }


def _scoped_product(db: Session, employer_id: int, product_id: int):
    product = (
        db.query(models.PartnerCatalogProduct)
        .filter(
            models.PartnerCatalogProduct.id == product_id,
            models.PartnerCatalogProduct.employer_id == employer_id,
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produit Marketplace introuvable")
    return product


def _scoped_stock_item(db: Session, employer_id: int, stock_item_id: int):
    item = (
        db.query(models.StockItem)
        .filter(models.StockItem.id == stock_item_id, models.StockItem.employer_id == employer_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Article de stock introuvable")
    return item


def _lot_key(lot_number: str, expires_at: Optional[datetime]) -> str:
    return f"{lot_number.strip()}|{expires_at.isoformat() if expires_at else 'NO_EXPIRY'}"


@router.get("/mappings")
def list_marketplace_stock_mappings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    mappings = (
        db.query(MarketplaceStockMapping)
        .filter(MarketplaceStockMapping.employer_id == employer_id)
        .order_by(MarketplaceStockMapping.product_id.asc())
        .all()
    )
    products = {
        item.id: item
        for item in db.query(models.PartnerCatalogProduct)
        .filter(models.PartnerCatalogProduct.employer_id == employer_id)
        .all()
    }
    stock_items = {
        item.id: item
        for item in db.query(models.StockItem)
        .filter(models.StockItem.employer_id == employer_id)
        .all()
    }
    return [_mapping_payload(mapping, products.get(mapping.product_id), stock_items.get(mapping.stock_item_id)) for mapping in mappings]


@router.put("/mappings/{product_id}")
def upsert_marketplace_stock_mapping(
    product_id: int,
    payload: StockMappingIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    if payload.targetQuantity <= payload.minQuantity:
        raise HTTPException(status_code=422, detail="targetQuantity doit être strictement supérieur à minQuantity.")
    product = _scoped_product(db, employer_id, product_id)
    item = _scoped_stock_item(db, employer_id, payload.stockItemId)

    mapping = (
        db.query(MarketplaceStockMapping)
        .filter(
            MarketplaceStockMapping.employer_id == employer_id,
            MarketplaceStockMapping.product_id == product_id,
        )
        .first()
    )
    if mapping is None:
        mapping = MarketplaceStockMapping(employer_id=employer_id, product_id=product_id, stock_item_id=item.id)
        db.add(mapping)

    mapping.stock_item_id = item.id
    mapping.stock_units_per_product_unit = _as_float(payload.stockUnitsPerProductUnit)
    mapping.min_quantity = _as_float(payload.minQuantity)
    mapping.target_quantity = _as_float(payload.targetQuantity)
    mapping.is_active = payload.isActive
    db.commit()
    db.refresh(mapping)
    return _mapping_payload(mapping, product, item)


@router.post("/receipts/{receipt_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_marketplace_receipt_to_stock(
    receipt_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    receipt = (
        db.query(PartnerOrderReceipt)
        .filter(PartnerOrderReceipt.id == receipt_id, PartnerOrderReceipt.employer_id == employer_id)
        .first()
    )
    if not receipt:
        raise HTTPException(status_code=404, detail="Réception Marketplace introuvable")

    lines = receipt.lines_json or []
    product_ids = [int(str(line.get("productId", "0"))) for line in lines if str(line.get("productId", "")).isdigit()]
    if len(product_ids) != len(lines) or len(set(product_ids)) != len(product_ids) or not product_ids:
        raise HTTPException(status_code=409, detail="Réception sans lignes produit canoniques exploitables.")

    mappings = (
        db.query(MarketplaceStockMapping)
        .filter(
            MarketplaceStockMapping.employer_id == employer_id,
            MarketplaceStockMapping.product_id.in_(product_ids),
            MarketplaceStockMapping.is_active.is_(True),
        )
        .all()
    )
    mapping_by_product = {mapping.product_id: mapping for mapping in mappings}
    missing = sorted(set(product_ids) - set(mapping_by_product))
    if missing:
        raise HTTPException(status_code=409, detail={"code": "STOCK_MAPPING_MISSING", "productIds": missing})

    stock_item_ids = {mapping.stock_item_id for mapping in mappings}
    stock_items = (
        db.query(models.StockItem)
        .filter(models.StockItem.employer_id == employer_id, models.StockItem.id.in_(stock_item_ids))
        .all()
    )
    stock_by_id = {item.id: item for item in stock_items}
    if set(stock_by_id) != stock_item_ids:
        raise HTTPException(status_code=409, detail="Mapping vers un article de stock inexistant.")

    movement_keys = [f"marketplace-receipt:{receipt.id}:product:{product_id}" for product_id in product_ids]
    existing = (
        db.query(MarketplaceStockMovement)
        .filter(
            MarketplaceStockMovement.employer_id == employer_id,
            MarketplaceStockMovement.movement_key.in_(movement_keys),
        )
        .all()
    )
    if existing:
        if len(existing) != len(movement_keys):
            raise HTTPException(status_code=409, detail="Application stock partielle détectée; intervention requise.")
        return {
            "receiptId": receipt.id,
            "idempotentReplay": True,
            "movements": [_movement_payload(item) for item in sorted(existing, key=lambda value: value.id)],
        }

    created: list[MarketplaceStockMovement] = []
    try:
        for line in lines:
            product_id = int(line["productId"])
            received = int(line.get("quantityReceived", 0))
            if received < 1:
                raise HTTPException(status_code=409, detail=f"Quantité reçue invalide pour {product_id}.")
            mapping = mapping_by_product[product_id]
            stock_item = stock_by_id[mapping.stock_item_id]
            delta = _as_float(received * mapping.stock_units_per_product_unit)
            stock_item.quantite = _as_float(stock_item.quantite + delta)

            lot_number = str(line.get("lotNumber") or "").strip() or None
            expires_at = _parse_datetime(line.get("expiresAt"))
            if expires_at and not lot_number:
                raise HTTPException(status_code=409, detail=f"Péremption sans numéro de lot pour {product_id}.")
            if lot_number:
                key = _lot_key(lot_number, expires_at)
                lot = (
                    db.query(MarketplaceStockLot)
                    .filter(
                        MarketplaceStockLot.employer_id == employer_id,
                        MarketplaceStockLot.stock_item_id == stock_item.id,
                        MarketplaceStockLot.lot_key == key,
                    )
                    .first()
                )
                if lot is None:
                    lot = MarketplaceStockLot(
                        employer_id=employer_id,
                        stock_item_id=stock_item.id,
                        product_id=product_id,
                        lot_key=key,
                        lot_number=lot_number,
                        expires_at=expires_at,
                        quantity=0.0,
                        first_received_at=receipt.received_at or datetime.utcnow(),
                    )
                    db.add(lot)
                lot.quantity = _as_float(lot.quantity + delta)

            movement = MarketplaceStockMovement(
                employer_id=employer_id,
                stock_item_id=stock_item.id,
                product_id=product_id,
                receipt_id=receipt.id,
                movement_key=f"marketplace-receipt:{receipt.id}:product:{product_id}",
                movement_type="RECEIPT",
                quantity_delta=delta,
                stock_quantity_after=stock_item.quantite,
                lot_number=lot_number,
                expires_at=expires_at,
                allocations_json=[],
                note=receipt.note,
                created_by_user_id=current_user.id,
            )
            db.add(movement)
            db.flush()
            created.append(movement)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for movement in created:
        db.refresh(movement)
    return {
        "receiptId": receipt.id,
        "idempotentReplay": False,
        "movements": [_movement_payload(item) for item in created],
    }


@router.post("/items/{stock_item_id}/consume", status_code=status.HTTP_201_CREATED)
def consume_marketplace_stock(
    stock_item_id: int,
    payload: StockConsumptionIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    item = _scoped_stock_item(db, employer_id, stock_item_id)
    movement_key = f"stock-consumption:{payload.idempotencyKey.strip()}"
    quantity = _as_float(payload.quantity)

    existing = (
        db.query(MarketplaceStockMovement)
        .filter(
            MarketplaceStockMovement.employer_id == employer_id,
            MarketplaceStockMovement.movement_key == movement_key,
        )
        .first()
    )
    if existing:
        if existing.stock_item_id != item.id or existing.movement_type != "CONSUMPTION" or _as_float(existing.quantity_delta) != -quantity:
            raise HTTPException(status_code=409, detail="Clé d'idempotence déjà utilisée avec un mouvement différent.")
        return {"idempotentReplay": True, "movement": _movement_payload(existing), "stockQuantity": _as_float(item.quantite)}

    if item.quantite < quantity:
        raise HTTPException(status_code=422, detail="Stock insuffisant pour cette consommation.")

    remaining = quantity
    allocations = []
    lots = (
        db.query(MarketplaceStockLot)
        .filter(
            MarketplaceStockLot.employer_id == employer_id,
            MarketplaceStockLot.stock_item_id == item.id,
            MarketplaceStockLot.quantity > 0,
        )
        .order_by(
            MarketplaceStockLot.expires_at.is_(None).asc(),
            MarketplaceStockLot.expires_at.asc(),
            MarketplaceStockLot.id.asc(),
        )
        .all()
    )
    for lot in lots:
        if remaining <= 0:
            break
        taken = min(_as_float(lot.quantity), remaining)
        if taken <= 0:
            continue
        lot.quantity = _as_float(lot.quantity - taken)
        remaining = _as_float(remaining - taken)
        allocations.append({"lotId": lot.id, "lotNumber": lot.lot_number, "quantity": taken})

    item.quantite = _as_float(item.quantite - quantity)
    movement = MarketplaceStockMovement(
        employer_id=employer_id,
        stock_item_id=item.id,
        movement_key=movement_key,
        movement_type="CONSUMPTION",
        quantity_delta=-quantity,
        stock_quantity_after=item.quantite,
        allocations_json=allocations,
        note=payload.note,
        created_by_user_id=current_user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return {"idempotentReplay": False, "movement": _movement_payload(movement), "stockQuantity": _as_float(item.quantite)}


@router.get("/lots")
def list_marketplace_stock_lots(
    stock_item_id: Optional[int] = Query(default=None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    query = db.query(MarketplaceStockLot).filter(MarketplaceStockLot.employer_id == employer_id)
    if stock_item_id is not None:
        _scoped_stock_item(db, employer_id, stock_item_id)
        query = query.filter(MarketplaceStockLot.stock_item_id == stock_item_id)
    lots = query.order_by(MarketplaceStockLot.expires_at.is_(None).asc(), MarketplaceStockLot.expires_at.asc()).all()
    return [_lot_payload(lot) for lot in lots]


@router.get("/movements")
def list_marketplace_stock_movements(
    stock_item_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    query = db.query(MarketplaceStockMovement).filter(MarketplaceStockMovement.employer_id == employer_id)
    if stock_item_id is not None:
        _scoped_stock_item(db, employer_id, stock_item_id)
        query = query.filter(MarketplaceStockMovement.stock_item_id == stock_item_id)
    movements = query.order_by(MarketplaceStockMovement.id.desc()).limit(limit).all()
    return [_movement_payload(movement) for movement in movements]


@router.get("/reorder-suggestions")
def get_marketplace_reorder_suggestions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    mappings = (
        db.query(MarketplaceStockMapping)
        .filter(
            MarketplaceStockMapping.employer_id == employer_id,
            MarketplaceStockMapping.is_active.is_(True),
        )
        .all()
    )
    suggestions = []
    for mapping in mappings:
        item = (
            db.query(models.StockItem)
            .filter(models.StockItem.id == mapping.stock_item_id, models.StockItem.employer_id == employer_id)
            .first()
        )
        product = (
            db.query(models.PartnerCatalogProduct)
            .filter(models.PartnerCatalogProduct.id == mapping.product_id, models.PartnerCatalogProduct.employer_id == employer_id)
            .first()
        )
        if not item or not product or item.quantite > mapping.min_quantity:
            continue
        deficit = max(0.0, mapping.target_quantity - item.quantite)
        units = max(1, math.ceil(deficit / mapping.stock_units_per_product_unit))
        suggestions.append({
            "productId": product.id,
            "productName": product.name,
            "sku": product.sku,
            "supplierId": product.supplier_id,
            "availability": product.availability.value,
            "stockItemId": item.id,
            "stockItemName": item.nom,
            "currentQuantity": _as_float(item.quantite),
            "minQuantity": _as_float(mapping.min_quantity),
            "targetQuantity": _as_float(mapping.target_quantity),
            "suggestedOrderUnits": units,
            "projectedQuantity": _as_float(item.quantite + units * mapping.stock_units_per_product_unit),
        })
    return sorted(suggestions, key=lambda item: (item["currentQuantity"] - item["minQuantity"], item["productName"]))
