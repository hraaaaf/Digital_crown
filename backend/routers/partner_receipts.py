from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin
from backend.routers.partner_orders import _append_event, _compute_revenue, _serialize

router = APIRouter()


class PartnerReceiptLineIn(BaseModel):
    productId: str = Field(..., min_length=1)
    quantityReceived: int = Field(..., ge=1)
    lotNumber: Optional[str] = None
    expiresAt: Optional[datetime] = None


class PartnerReceiptCreateIn(BaseModel):
    lines: List[PartnerReceiptLineIn] = Field(..., min_length=1)
    note: Optional[str] = None


def _serialize_receipt(receipt: PartnerOrderReceipt) -> dict:
    return {
        "id": receipt.id,
        "orderId": receipt.order_id,
        "receivedByUserId": receipt.received_by_user_id,
        "lines": receipt.lines_json,
        "note": receipt.note,
        "receivedAt": receipt.received_at.isoformat() if receipt.received_at else None,
        "createdAt": receipt.created_at.isoformat() if receipt.created_at else None,
    }


def _canonical_receipt_lines(order: models.PartnerOrder, requested: List[PartnerReceiptLineIn]) -> list[dict]:
    ordered_quantities: dict[str, int] = {}
    for line in order.lines_json or []:
        product_id = str(line.get("productId", "")).strip()
        if not product_id:
            raise HTTPException(status_code=409, detail="Commande sans identifiant produit canonique.")
        if product_id in ordered_quantities:
            raise HTTPException(status_code=409, detail=f"Commande incoherente: produit duplique {product_id}.")
        ordered_quantities[product_id] = int(line.get("quantity", 0))

    received_by_product: dict[str, PartnerReceiptLineIn] = {}
    for line in requested:
        product_id = str(line.productId).strip()
        if product_id in received_by_product:
            raise HTTPException(status_code=422, detail=f"Produit duplique dans la reception: {product_id}")
        received_by_product[product_id] = line

    if set(received_by_product) != set(ordered_quantities):
        raise HTTPException(
            status_code=422,
            detail="La reception complete doit contenir exactement les produits de la commande.",
        )

    canonical_lines: list[dict] = []
    for order_line in order.lines_json or []:
        product_id = str(order_line["productId"])
        requested_line = received_by_product[product_id]
        ordered_quantity = ordered_quantities[product_id]
        if requested_line.quantityReceived != ordered_quantity:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Quantite recue invalide pour {product_id}: "
                    f"attendu {ordered_quantity}, recu {requested_line.quantityReceived}."
                ),
            )
        canonical_lines.append(
            {
                "productId": product_id,
                "name": order_line.get("name"),
                "sku": order_line.get("sku"),
                "quantityOrdered": ordered_quantity,
                "quantityReceived": ordered_quantity,
                "unitPrice": order_line.get("unitPrice"),
                "lotNumber": requested_line.lotNumber.strip() if requested_line.lotNumber else None,
                "expiresAt": requested_line.expiresAt.isoformat() if requested_line.expiresAt else None,
            }
        )
    return canonical_lines


@router.post("/{order_id}/receipt", status_code=status.HTTP_201_CREATED)
def create_partner_order_receipt(
    order_id: int,
    payload: PartnerReceiptCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = (
        db.query(models.PartnerOrder)
        .filter(
            models.PartnerOrder.id == order_id,
            models.PartnerOrder.employer_id == employer_id,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Commande partenaire introuvable")

    existing = (
        db.query(PartnerOrderReceipt)
        .filter(
            PartnerOrderReceipt.order_id == order.id,
            PartnerOrderReceipt.employer_id == employer_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Cette commande a deja ete receptionnee.")

    if order.status != models.PartnerOrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=422,
            detail=f"Reception impossible depuis le statut {order.status.value}; CONFIRMED requis.",
        )

    canonical_lines = _canonical_receipt_lines(order, payload.lines)
    previous_status = order.status.value
    previous_total = order.current_total
    revenue_before = order.recognized_revenue_amount

    receipt = PartnerOrderReceipt(
        employer_id=employer_id,
        order_id=order.id,
        received_by_user_id=current_user.id,
        lines_json=canonical_lines,
        note=payload.note,
        received_at=datetime.utcnow(),
    )

    try:
        db.add(receipt)
        db.flush()

        order.status = models.PartnerOrderStatus.FULFILLED
        order.last_partner_update_at = datetime.utcnow()
        order.recognized_base_amount, order.recognized_revenue_amount = _compute_revenue(order)
        order.revenue_delta_amount = round(order.recognized_revenue_amount - revenue_before, 2)

        _append_event(
            db,
            order,
            event_type="RECEIPT_RECORDED",
            previous_status=previous_status,
            new_status=order.status.value,
            previous_total=previous_total,
            new_total=order.current_total,
            revenue_before=revenue_before,
            revenue_after=order.recognized_revenue_amount,
            note=payload.note,
            payload_json={
                "receiptId": receipt.id,
                "receivedByUserId": current_user.id,
                "lineCount": len(canonical_lines),
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(receipt)
    db.refresh(order)
    return {
        "receipt": _serialize_receipt(receipt),
        "order": _serialize(order),
    }
