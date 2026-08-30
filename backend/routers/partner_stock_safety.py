from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_stock import MarketplaceStockLot, MarketplaceStockMapping, MarketplaceStockMovement
from backend.routers.auth import require_permission
from backend.routers.partner_stock import StockConsumptionIn, _as_float, _movement_payload, _scoped_stock_item

router = APIRouter(prefix="/marketplace")


def _stock_availability(db: Session, employer_id: int, stock_item: models.StockItem) -> dict:
    lots = (
        db.query(MarketplaceStockLot)
        .filter(
            MarketplaceStockLot.employer_id == employer_id,
            MarketplaceStockLot.stock_item_id == stock_item.id,
            MarketplaceStockLot.quantity > 0,
        )
        .all()
    )
    now = datetime.utcnow()
    tracked_total = _as_float(sum(float(lot.quantity) for lot in lots))
    expired_total = _as_float(
        sum(float(lot.quantity) for lot in lots if lot.expires_at is not None and lot.expires_at < now)
    )
    usable_lots = [lot for lot in lots if lot.expires_at is None or lot.expires_at >= now]
    usable_tracked = _as_float(sum(float(lot.quantity) for lot in usable_lots))
    # StockItem peut contenir un stock historique non loti. On le conserve comme utilisable,
    # sans inventer de lot ni de péremption.
    untracked = _as_float(max(0.0, float(stock_item.quantite) - tracked_total))
    usable_total = _as_float(untracked + usable_tracked)
    return {
        "lots": lots,
        "usableLots": usable_lots,
        "trackedTotal": tracked_total,
        "expiredTotal": expired_total,
        "untrackedTotal": untracked,
        "usableTotal": usable_total,
    }


@router.post("/items/{stock_item_id}/consume", status_code=status.HTTP_201_CREATED)
def consume_marketplace_stock_safely(
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
        if (
            existing.stock_item_id != item.id
            or existing.movement_type != "CONSUMPTION"
            or _as_float(existing.quantity_delta) != -quantity
        ):
            raise HTTPException(status_code=409, detail="Clé d'idempotence déjà utilisée avec un mouvement différent.")
        return {
            "idempotentReplay": True,
            "movement": _movement_payload(existing),
            "stockQuantity": _as_float(item.quantite),
        }

    availability = _stock_availability(db, employer_id, item)
    if availability["usableTotal"] < quantity:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "USABLE_STOCK_INSUFFICIENT",
                "requestedQuantity": quantity,
                "usableQuantity": availability["usableTotal"],
                "expiredQuantity": availability["expiredTotal"],
                "aggregateQuantity": _as_float(item.quantite),
            },
        )

    # FEFO : lots datés les plus proches d'abord, puis lots sans péremption.
    usable_lots = sorted(
        availability["usableLots"],
        key=lambda lot: (lot.expires_at is None, lot.expires_at or datetime.max, lot.id),
    )
    remaining = quantity
    allocations = []
    for lot in usable_lots:
        if remaining <= 0:
            break
        taken = min(_as_float(lot.quantity), remaining)
        if taken <= 0:
            continue
        lot.quantity = _as_float(lot.quantity - taken)
        remaining = _as_float(remaining - taken)
        allocations.append({
            "lotId": lot.id,
            "lotNumber": lot.lot_number,
            "quantity": taken,
            "source": "LOT",
        })

    if remaining > 0:
        # Le reliquat vient nécessairement du stock historique non loti calculé ci-dessus.
        allocations.append({
            "lotId": None,
            "lotNumber": None,
            "quantity": remaining,
            "source": "UNTRACKED",
        })
        remaining = 0.0

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
    return {
        "idempotentReplay": False,
        "movement": _movement_payload(movement),
        "stockQuantity": _as_float(item.quantite),
    }


@router.get("/reorder-suggestions")
def get_marketplace_reorder_suggestions_safely(
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
            .filter(
                models.PartnerCatalogProduct.id == mapping.product_id,
                models.PartnerCatalogProduct.employer_id == employer_id,
            )
            .first()
        )
        if not item or not product:
            continue
        availability = _stock_availability(db, employer_id, item)
        usable = availability["usableTotal"]
        if usable > mapping.min_quantity:
            continue
        deficit = max(0.0, mapping.target_quantity - usable)
        units = max(1, int(-(-deficit // mapping.stock_units_per_product_unit)))
        suggestions.append({
            "productId": product.id,
            "productName": product.name,
            "sku": product.sku,
            "supplierId": product.supplier_id,
            "availability": product.availability.value,
            "stockItemId": item.id,
            "stockItemName": item.nom,
            "aggregateQuantity": _as_float(item.quantite),
            "usableQuantity": usable,
            "expiredQuantity": availability["expiredTotal"],
            "minQuantity": _as_float(mapping.min_quantity),
            "targetQuantity": _as_float(mapping.target_quantity),
            "suggestedOrderUnits": units,
            "projectedUsableQuantity": _as_float(usable + units * mapping.stock_units_per_product_unit),
        })
    return sorted(suggestions, key=lambda item: (item["usableQuantity"] - item["minQuantity"], item["productName"]))
