from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_procurement import PartnerOrderProcurement
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin
from backend.routers.partner_orders import _append_event, _serialize

router = APIRouter()


class PartnerBackorderLineIn(BaseModel):
    productId: str = Field(..., min_length=1)
    quantityBackordered: int = Field(..., ge=1)


class PartnerProcurementAckIn(BaseModel):
    supplierReference: str = Field(..., min_length=1, max_length=120)
    expectedDeliveryAt: Optional[datetime] = None
    backorderedLines: List[PartnerBackorderLineIn] = Field(default_factory=list)
    note: Optional[str] = None


def _scoped_order(db: Session, employer_id: int, order_id: int) -> models.PartnerOrder:
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
    return order


def _received_quantities(db: Session, employer_id: int, order_id: int) -> dict[str, int]:
    receipts = (
        db.query(PartnerOrderReceipt)
        .filter(
            PartnerOrderReceipt.order_id == order_id,
            PartnerOrderReceipt.employer_id == employer_id,
        )
        .all()
    )
    totals: dict[str, int] = {}
    for receipt in receipts:
        for line in receipt.lines_json or []:
            product_id = str(line.get("productId", "")).strip()
            quantity = int(line.get("quantityReceived", 0))
            if product_id and quantity > 0:
                totals[product_id] = totals.get(product_id, 0) + quantity
    return totals


def _canonical_backorders(
    db: Session,
    employer_id: int,
    order: models.PartnerOrder,
    requested: List[PartnerBackorderLineIn],
) -> list[dict]:
    order_lines = {
        str(line.get("productId", "")).strip(): line
        for line in order.lines_json or []
        if str(line.get("productId", "")).strip()
    }
    received = _received_quantities(db, employer_id, order.id)
    requested_by_product: dict[str, int] = {}

    for line in requested:
        product_id = str(line.productId).strip()
        if not product_id:
            raise HTTPException(status_code=422, detail="Identifiant produit backorder invalide.")
        if product_id in requested_by_product:
            raise HTTPException(status_code=422, detail=f"Produit backorder duplique: {product_id}")
        order_line = order_lines.get(product_id)
        if not order_line:
            raise HTTPException(status_code=422, detail=f"Produit absent de la commande: {product_id}")
        ordered_quantity = int(order_line.get("quantity", 0))
        if ordered_quantity < 1:
            raise HTTPException(status_code=409, detail=f"Ligne commande incoherente: {product_id}")
        received_quantity = received.get(product_id, 0)
        outstanding_quantity = ordered_quantity - received_quantity
        if outstanding_quantity < 0:
            raise HTTPException(status_code=409, detail=f"Historique de sur-reception detecte pour {product_id}.")
        if line.quantityBackordered > outstanding_quantity:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Backorder superieur au reliquat pour {product_id}: "
                    f"reste {outstanding_quantity}, backorder {line.quantityBackordered}."
                ),
            )
        requested_by_product[product_id] = line.quantityBackordered

    canonical: list[dict] = []
    for order_line in order.lines_json or []:
        product_id = str(order_line.get("productId", "")).strip()
        if product_id not in requested_by_product:
            continue
        ordered_quantity = int(order_line.get("quantity", 0))
        received_quantity = received.get(product_id, 0)
        canonical.append(
            {
                "productId": product_id,
                "name": order_line.get("name"),
                "sku": order_line.get("sku"),
                "quantityOrdered": ordered_quantity,
                "quantityReceived": received_quantity,
                "quantityOutstanding": ordered_quantity - received_quantity,
                "quantityBackordered": requested_by_product[product_id],
            }
        )
    return canonical


def _serialize_procurement(state: PartnerOrderProcurement) -> dict:
    return {
        "id": state.id,
        "orderId": state.order_id,
        "supplierReference": state.supplier_reference,
        "expectedDeliveryAt": state.expected_delivery_at.isoformat() if state.expected_delivery_at else None,
        "backorderedLines": state.backorder_json or [],
        "note": state.note,
        "acknowledgedAt": state.acknowledged_at.isoformat() if state.acknowledged_at else None,
        "updatedAt": state.updated_at.isoformat() if state.updated_at else None,
    }


def _same_ack(
    state: PartnerOrderProcurement,
    *,
    supplier_reference: str,
    expected_delivery_at: Optional[datetime],
    backorders: list[dict],
    note: Optional[str],
) -> bool:
    return (
        state.supplier_reference == supplier_reference
        and state.expected_delivery_at == expected_delivery_at
        and (state.backorder_json or []) == backorders
        and state.note == note
    )


@router.get("/{order_id}/procurement")
def get_partner_order_procurement(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _scoped_order(db, employer_id, order_id)
    state = (
        db.query(PartnerOrderProcurement)
        .filter(
            PartnerOrderProcurement.order_id == order.id,
            PartnerOrderProcurement.employer_id == employer_id,
        )
        .first()
    )
    return {
        "order": _serialize(order),
        "procurement": _serialize_procurement(state) if state else None,
    }


@router.put("/{order_id}/procurement")
def acknowledge_partner_order_procurement(
    order_id: int,
    payload: PartnerProcurementAckIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _scoped_order(db, employer_id, order_id)
    if order.status != models.PartnerOrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=422,
            detail=f"Accuse fournisseur impossible depuis {order.status.value}; CONFIRMED requis.",
        )

    supplier_reference = payload.supplierReference.strip()
    if not supplier_reference:
        raise HTTPException(status_code=422, detail="supplierReference ne peut pas etre vide.")
    backorders = _canonical_backorders(db, employer_id, order, payload.backorderedLines)
    state = (
        db.query(PartnerOrderProcurement)
        .filter(
            PartnerOrderProcurement.order_id == order.id,
            PartnerOrderProcurement.employer_id == employer_id,
        )
        .first()
    )

    if state and _same_ack(
        state,
        supplier_reference=supplier_reference,
        expected_delivery_at=payload.expectedDeliveryAt,
        backorders=backorders,
        note=payload.note,
    ):
        return {
            "order": _serialize(order),
            "procurement": _serialize_procurement(state),
            "idempotentReplay": True,
        }

    previous_reference = order.partner_reference
    if state is None:
        state = PartnerOrderProcurement(
            employer_id=employer_id,
            order_id=order.id,
            supplier_reference=supplier_reference,
            expected_delivery_at=payload.expectedDeliveryAt,
            backorder_json=backorders,
            note=payload.note,
            acknowledged_at=datetime.utcnow(),
        )
        db.add(state)
    else:
        state.supplier_reference = supplier_reference
        state.expected_delivery_at = payload.expectedDeliveryAt
        state.backorder_json = backorders
        state.note = payload.note
        state.acknowledged_at = datetime.utcnow()

    order.partner_reference = supplier_reference
    order.last_partner_update_at = datetime.utcnow()
    _append_event(
        db,
        order,
        event_type="PROCUREMENT_ACKNOWLEDGED",
        previous_status=order.status.value,
        new_status=order.status.value,
        previous_total=order.current_total,
        new_total=order.current_total,
        revenue_before=order.recognized_revenue_amount,
        revenue_after=order.recognized_revenue_amount,
        note=payload.note,
        payload_json={
            "previousPartnerReference": previous_reference,
            "partnerReference": supplier_reference,
            "expectedDeliveryAt": payload.expectedDeliveryAt.isoformat() if payload.expectedDeliveryAt else None,
            "backorderedLines": backorders,
        },
    )
    db.commit()
    db.refresh(state)
    db.refresh(order)
    return {
        "order": _serialize(order),
        "procurement": _serialize_procurement(state),
        "idempotentReplay": False,
    }
