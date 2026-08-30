from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_superadmin
from backend.routers import partner_receipts, partner_stock

router = APIRouter()


def _stock_pending_payload(error: HTTPException) -> dict:
    detail = error.detail
    if isinstance(detail, dict) and detail.get("code") == "STOCK_MAPPING_MISSING":
        return {
            "status": "PENDING_MAPPING",
            "productIds": detail.get("productIds") or [],
        }
    return {
        "status": "PENDING_RETRY",
        "httpStatus": error.status_code,
        "detail": detail,
    }


@router.post("/{order_id}/receipt", status_code=status.HTTP_201_CREATED)
def create_partner_order_receipt_with_stock_sync(
    order_id: int,
    payload: partner_receipts.PartnerReceiptCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    """Enregistre d'abord la réception, puis tente le stock de façon rejouable.

    La réception fournisseur est une vérité métier indépendante et ne doit jamais être
    annulée parce qu'un mapping de stock manque. Le second commit est idempotent : si
    le processus tombe entre les deux étapes, rejouer la même réception complète le
    stock sans dupliquer ni réception ni mouvement.
    """

    result = partner_receipts.create_partner_order_receipt(
        order_id,
        payload,
        db=db,
        current_user=current_user,
    )
    receipt_id = int(result["receipt"]["id"])

    try:
        stock_result = partner_stock.apply_marketplace_receipt_to_stock(
            receipt_id,
            db=db,
            current_user=current_user,
        )
        stock_sync = {
            "status": "APPLIED",
            "idempotentReplay": bool(stock_result.get("idempotentReplay")),
            "movementCount": len(stock_result.get("movements") or []),
        }
    except HTTPException as error:
        stock_sync = _stock_pending_payload(error)

    return {**result, "stockSync": stock_sync}
