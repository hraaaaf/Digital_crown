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
    idempotencyKey: str = Field(..., min_length=8, max_length=128)
    lines: List[PartnerReceiptLineIn] = Field(..., min_length=1)
    note: Optional[str] = None


def _serialize_receipt(receipt: PartnerOrderReceipt) -> dict:
    return {
        "id": receipt.id,
        "orderId": receipt.order_id,
        "idempotencyKey": receipt.receipt_key,
        "receivedByUserId": receipt.received_by_user_id,
        "lines": receipt.lines_json,
        "note": receipt.note,
        "receivedAt": receipt.received_at.isoformat() if receipt.received_at else None,
        "createdAt": receipt.created_at.isoformat() if receipt.created_at else None,
    }


def _get_scoped_order(db: Session, employer_id: int, order_id: int) -> models.PartnerOrder:
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


def _ordered_quantities(order: models.PartnerOrder) -> dict[str, int]:
    quantities: dict[str, int] = {}
    for line in order.lines_json or []:
        product_id = str(line.get("productId", "")).strip()
        quantity = int(line.get("quantity", 0))
        if not product_id or quantity < 1:
            raise HTTPException(status_code=409, detail="Commande sans ligne produit canonique valide.")
        if product_id in quantities:
            raise HTTPException(status_code=409, detail=f"Commande incoherente: produit duplique {product_id}.")
        quantities[product_id] = quantity
    if not quantities:
        raise HTTPException(status_code=409, detail="Commande sans ligne produit canonique valide.")
    return quantities


def _load_receipts(db: Session, employer_id: int, order_id: int) -> list[PartnerOrderReceipt]:
    return (
        db.query(PartnerOrderReceipt)
        .filter(
            PartnerOrderReceipt.order_id == order_id,
            PartnerOrderReceipt.employer_id == employer_id,
        )
        .order_by(PartnerOrderReceipt.id.asc())
        .all()
    )


def _received_quantities(receipts: list[PartnerOrderReceipt]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for receipt in receipts:
        for line in receipt.lines_json or []:
            product_id = str(line.get("productId", "")).strip()
            quantity = int(line.get("quantityReceived", 0))
            if product_id and quantity > 0:
                totals[product_id] = totals.get(product_id, 0) + quantity
    return totals


def _receipt_progress(order: models.PartnerOrder, receipts: list[PartnerOrderReceipt]) -> dict:
    ordered = _ordered_quantities(order)
    received = _received_quantities(receipts)
    unexpected_products = set(received) - set(ordered)
    if unexpected_products:
        raise HTTPException(status_code=409, detail="Historique de reception incoherent avec la commande.")

    lines = []
    for order_line in order.lines_json or []:
        product_id = str(order_line["productId"])
        quantity_ordered = ordered[product_id]
        quantity_received = received.get(product_id, 0)
        if quantity_received > quantity_ordered:
            raise HTTPException(status_code=409, detail=f"Historique de sur-reception detecte pour {product_id}.")
        lines.append(
            {
                "productId": product_id,
                "name": order_line.get("name"),
                "sku": order_line.get("sku"),
                "quantityOrdered": quantity_ordered,
                "quantityReceived": quantity_received,
                "quantityOutstanding": quantity_ordered - quantity_received,
            }
        )
    return {
        "isComplete": all(line["quantityOutstanding"] == 0 for line in lines),
        "receiptCount": len(receipts),
        "lines": lines,
    }


def _canonical_receipt_lines(
    order: models.PartnerOrder,
    requested: List[PartnerReceiptLineIn],
    already_received: dict[str, int],
) -> list[dict]:
    ordered = _ordered_quantities(order)
    order_lines = {str(line["productId"]): line for line in order.lines_json or []}
    received_by_product: dict[str, PartnerReceiptLineIn] = {}

    for line in requested:
        product_id = str(line.productId).strip()
        if product_id in received_by_product:
            raise HTTPException(status_code=422, detail=f"Produit duplique dans la reception: {product_id}")
        if product_id not in ordered:
            raise HTTPException(status_code=422, detail=f"Produit absent de la commande: {product_id}")
        previous = already_received.get(product_id, 0)
        remaining = ordered[product_id] - previous
        if remaining < 0:
            raise HTTPException(status_code=409, detail=f"Historique de sur-reception detecte pour {product_id}.")
        if line.quantityReceived > remaining:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Sur-reception interdite pour {product_id}: reste {remaining}, "
                    f"recu {line.quantityReceived}."
                ),
            )
        received_by_product[product_id] = line

    canonical_lines: list[dict] = []
    for product_id, order_line in order_lines.items():
        requested_line = received_by_product.get(product_id)
        if requested_line is None:
            continue
        canonical_lines.append(
            {
                "productId": product_id,
                "name": order_line.get("name"),
                "sku": order_line.get("sku"),
                "quantityOrdered": ordered[product_id],
                "quantityPreviouslyReceived": already_received.get(product_id, 0),
                "quantityReceived": requested_line.quantityReceived,
                "unitPrice": order_line.get("unitPrice"),
                "lotNumber": requested_line.lotNumber.strip() if requested_line.lotNumber else None,
                "expiresAt": requested_line.expiresAt.isoformat() if requested_line.expiresAt else None,
            }
        )
    return canonical_lines


def _idempotent_payload_matches(receipt: PartnerOrderReceipt, payload: PartnerReceiptCreateIn) -> bool:
    requested_ids = [str(line.productId).strip() for line in payload.lines]
    if any(not product_id for product_id in requested_ids) or len(set(requested_ids)) != len(requested_ids):
        return False

    stored = {
        str(line.get("productId")): (
            int(line.get("quantityReceived", 0)),
            line.get("lotNumber"),
            line.get("expiresAt"),
        )
        for line in receipt.lines_json or []
    }
    requested = {
        str(line.productId).strip(): (
            line.quantityReceived,
            line.lotNumber.strip() if line.lotNumber else None,
            line.expiresAt.isoformat() if line.expiresAt else None,
        )
        for line in payload.lines
    }
    return stored == requested and receipt.note == payload.note


@router.get("/{order_id}/receipts")
def get_partner_order_receipts(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _get_scoped_order(db, employer_id, order_id)
    receipts = _load_receipts(db, employer_id, order.id)
    return {
        "order": _serialize(order),
        "receipts": [_serialize_receipt(receipt) for receipt in receipts],
        "progress": _receipt_progress(order, receipts),
    }


@router.post("/{order_id}/receipt", status_code=status.HTTP_201_CREATED)
def create_partner_order_receipt(
    order_id: int,
    payload: PartnerReceiptCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _get_scoped_order(db, employer_id, order_id)
    receipt_key = payload.idempotencyKey.strip()
    if len(receipt_key) < 8:
        raise HTTPException(status_code=422, detail="idempotencyKey doit contenir au moins 8 caracteres utiles.")

    existing = (
        db.query(PartnerOrderReceipt)
        .filter(
            PartnerOrderReceipt.order_id == order.id,
            PartnerOrderReceipt.employer_id == employer_id,
            PartnerOrderReceipt.receipt_key == receipt_key,
        )
        .first()
    )
    if existing:
        if not _idempotent_payload_matches(existing, payload):
            raise HTTPException(status_code=409, detail="Cle d'idempotence deja utilisee avec un contenu different.")
        receipts = _load_receipts(db, employer_id, order.id)
        return {
            "receipt": _serialize_receipt(existing),
            "order": _serialize(order),
            "progress": _receipt_progress(order, receipts),
            "idempotentReplay": True,
        }

    if order.status != models.PartnerOrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=422,
            detail=f"Reception impossible depuis le statut {order.status.value}; CONFIRMED requis.",
        )

    receipts_before = _load_receipts(db, employer_id, order.id)
    already_received = _received_quantities(receipts_before)
    canonical_lines = _canonical_receipt_lines(order, payload.lines, already_received)
    previous_status = order.status.value
    previous_total = order.current_total
    revenue_before = order.recognized_revenue_amount

    receipt = PartnerOrderReceipt(
        employer_id=employer_id,
        order_id=order.id,
        receipt_key=receipt_key,
        received_by_user_id=current_user.id,
        lines_json=canonical_lines,
        note=payload.note,
        received_at=datetime.utcnow(),
    )

    try:
        db.add(receipt)
        db.flush()
        receipts_after = [*receipts_before, receipt]
        progress = _receipt_progress(order, receipts_after)

        if progress["isComplete"]:
            order.status = models.PartnerOrderStatus.FULFILLED
        order.last_partner_update_at = datetime.utcnow()
        order.recognized_base_amount, order.recognized_revenue_amount = _compute_revenue(order)
        order.revenue_delta_amount = round(order.recognized_revenue_amount - revenue_before, 2)

        _append_event(
            db,
            order,
            event_type="RECEIPT_COMPLETED" if progress["isComplete"] else "RECEIPT_PARTIAL_RECORDED",
            previous_status=previous_status,
            new_status=order.status.value,
            previous_total=previous_total,
            new_total=order.current_total,
            revenue_before=revenue_before,
            revenue_after=order.recognized_revenue_amount,
            note=payload.note,
            payload_json={
                "receiptId": receipt.id,
                "receiptKey": receipt_key,
                "receivedByUserId": current_user.id,
                "lineCount": len(canonical_lines),
                "isComplete": progress["isComplete"],
                "progress": progress["lines"],
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
        "progress": progress,
        "idempotentReplay": False,
    }
