from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers import partner_orders
from backend.routers.auth import require_superadmin

router = APIRouter()


@router.patch("/{order_id}")
def update_partner_order_with_dispatch_gate(
    order_id: int,
    payload: partner_orders.PartnerOrderUpdateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    if payload.status == models.PartnerOrderStatus.SENT_TO_PARTNER.value:
        raise HTTPException(
            status_code=422,
            detail="SENT_TO_PARTNER requiert une preuve de transport; utilisez /api/partner-orders/{id}/dispatch.",
        )
    return partner_orders.update_partner_order(
        order_id,
        payload,
        db=db,
        current_user=current_user,
    )
