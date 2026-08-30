from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_finance import PartnerSupplierInvoice
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin

router = APIRouter(prefix="/finance")

MONEY_TOLERANCE = 0.01


class SupplierInvoiceIn(BaseModel):
    invoiceKey: str = Field(..., min_length=8, max_length=128)
    invoiceReference: str = Field(..., min_length=1, max_length=160)
    amountTotal: float = Field(..., ge=0)
    currency: str = Field("MAD", min_length=3, max_length=3)
    issuedAt: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=2000)


def _money(value: float) -> float:
    return round(float(value or 0.0), 2)


def _scoped_order(db: Session, employer_id: int, order_id: int):
    order = (
        db.query(models.PartnerOrder)
        .filter(models.PartnerOrder.id == order_id, models.PartnerOrder.employer_id == employer_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Commande partenaire introuvable")
    return order


def _expected_supplier_payable(order: models.PartnerOrder) -> float:
    """Coût fournisseur attendu selon le contrat commercial canonique de la commande."""
    base = _money(order.current_total)
    if order.status == models.PartnerOrderStatus.CANCELLED:
        return 0.0
    if order.revenue_model == models.PartnerRevenueModel.DISCOUNT_RESALE:
        return _money(base * (1.0 - float(order.discount_rate or 0.0) / 100.0))
    return base


def _receipt_progress(db: Session, order: models.PartnerOrder) -> dict:
    ordered_by_product: dict[str, int] = {}
    for line in order.lines_json or []:
        product_id = str(line.get("productId") or "")
        quantity = int(line.get("quantity") or 0)
        if product_id and quantity > 0:
            ordered_by_product[product_id] = quantity

    received_by_product = {product_id: 0 for product_id in ordered_by_product}
    receipts = (
        db.query(PartnerOrderReceipt)
        .filter(
            PartnerOrderReceipt.employer_id == order.employer_id,
            PartnerOrderReceipt.order_id == order.id,
        )
        .order_by(PartnerOrderReceipt.id.asc())
        .all()
    )
    for receipt in receipts:
        for line in receipt.lines_json or []:
            product_id = str(line.get("productId") or "")
            if product_id in received_by_product:
                received_by_product[product_id] += int(line.get("quantityReceived") or 0)

    ordered_units = sum(ordered_by_product.values())
    received_units = sum(min(received_by_product.get(product_id, 0), quantity) for product_id, quantity in ordered_by_product.items())
    ratio = 1.0 if ordered_units == 0 else min(1.0, received_units / ordered_units)
    return {
        "orderedUnits": ordered_units,
        "receivedUnits": received_units,
        "receivedRatio": round(ratio, 4),
        "receiptCount": len(receipts),
        "fullyReceived": bool(ordered_units > 0 and received_units >= ordered_units),
    }


def _invoice_payload(invoice: PartnerSupplierInvoice) -> dict:
    return {
        "id": invoice.id,
        "invoiceKey": invoice.invoice_key,
        "invoiceReference": invoice.invoice_reference,
        "amountTotal": _money(invoice.amount_total),
        "currency": invoice.currency,
        "issuedAt": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "note": invoice.note,
        "createdAt": invoice.created_at.isoformat() if invoice.created_at else None,
    }


def _reconciliation(db: Session, order: models.PartnerOrder) -> dict:
    invoices = (
        db.query(PartnerSupplierInvoice)
        .filter(
            PartnerSupplierInvoice.employer_id == order.employer_id,
            PartnerSupplierInvoice.order_id == order.id,
        )
        .order_by(PartnerSupplierInvoice.id.asc())
        .all()
    )
    invoiced_amount = _money(sum(float(invoice.amount_total) for invoice in invoices))
    expected_payable = _expected_supplier_payable(order)
    variance = _money(invoiced_amount - expected_payable)
    receipt = _receipt_progress(db, order)

    if order.status == models.PartnerOrderStatus.CANCELLED:
        reconciliation_status = "CANCELLED"
    elif not invoices:
        reconciliation_status = "WAITING_INVOICE"
    elif abs(variance) > MONEY_TOLERANCE:
        reconciliation_status = "AMOUNT_MISMATCH"
    elif not receipt["fullyReceived"]:
        reconciliation_status = "WAITING_RECEIPT"
    else:
        reconciliation_status = "MATCHED"

    return {
        "orderId": order.id,
        "orderNumber": order.order_number,
        "status": order.status.value,
        "revenueModel": order.revenue_model.value,
        "settlementBasis": order.settlement_basis.value,
        "currentTotal": _money(order.current_total),
        "recognizedBaseAmount": _money(order.recognized_base_amount),
        "recognizedRevenueAmount": _money(order.recognized_revenue_amount),
        "expectedSupplierPayable": expected_payable,
        "invoicedAmount": invoiced_amount,
        "invoiceVariance": variance,
        "reconciliationStatus": reconciliation_status,
        "receipt": receipt,
        "invoices": [_invoice_payload(invoice) for invoice in invoices],
    }


@router.post("/orders/{order_id}/invoices", status_code=status.HTTP_201_CREATED)
def record_supplier_invoice(
    order_id: int,
    payload: SupplierInvoiceIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _scoped_order(db, employer_id, order_id)
    if order.status in {models.PartnerOrderStatus.DRAFT, models.PartnerOrderStatus.CANCELLED}:
        raise HTTPException(status_code=409, detail="Une facture fournisseur ne peut pas être ajoutée à ce statut de commande.")

    currency = payload.currency.strip().upper()
    if currency != "MAD":
        raise HTTPException(status_code=422, detail="P8 rapproche uniquement les montants canoniques MAD de la commande.")

    invoice_key = payload.invoiceKey.strip()
    invoice_reference = payload.invoiceReference.strip()
    amount_total = _money(payload.amountTotal)
    existing = (
        db.query(PartnerSupplierInvoice)
        .filter(
            PartnerSupplierInvoice.employer_id == employer_id,
            PartnerSupplierInvoice.order_id == order.id,
            PartnerSupplierInvoice.invoice_key == invoice_key,
        )
        .first()
    )
    if existing:
        same_payload = (
            existing.invoice_reference == invoice_reference
            and _money(existing.amount_total) == amount_total
            and existing.currency == currency
            and existing.issued_at == payload.issuedAt
        )
        if not same_payload:
            raise HTTPException(status_code=409, detail="Clé d'idempotence déjà utilisée avec une autre facture.")
        return {
            "idempotentReplay": True,
            "invoice": _invoice_payload(existing),
            "reconciliation": _reconciliation(db, order),
        }

    duplicate_reference = (
        db.query(PartnerSupplierInvoice)
        .filter(
            PartnerSupplierInvoice.employer_id == employer_id,
            PartnerSupplierInvoice.order_id == order.id,
            PartnerSupplierInvoice.invoice_reference == invoice_reference,
        )
        .first()
    )
    if duplicate_reference:
        raise HTTPException(status_code=409, detail="Référence de facture déjà enregistrée pour cette commande.")

    invoice = PartnerSupplierInvoice(
        employer_id=employer_id,
        order_id=order.id,
        invoice_key=invoice_key,
        invoice_reference=invoice_reference,
        amount_total=amount_total,
        currency=currency,
        issued_at=payload.issuedAt,
        note=payload.note,
        payload_json={"source": "MARKETPLACE_P8"},
        created_by_user_id=current_user.id,
    )
    db.add(invoice)
    db.flush()
    db.add(
        models.PartnerOrderEvent(
            order_id=order.id,
            event_type="SUPPLIER_INVOICE_RECORDED",
            previous_status=order.status.value,
            new_status=order.status.value,
            previous_total=order.current_total,
            new_total=order.current_total,
            revenue_before=order.recognized_revenue_amount,
            revenue_after=order.recognized_revenue_amount,
            delta_amount=0.0,
            note=f"Facture fournisseur {invoice_reference}",
            payload_json={"invoiceId": invoice.id, "amountTotal": amount_total, "currency": currency},
        )
    )
    db.commit()
    db.refresh(invoice)
    return {
        "idempotentReplay": False,
        "invoice": _invoice_payload(invoice),
        "reconciliation": _reconciliation(db, order),
    }


@router.get("/orders/{order_id}/reconciliation")
def get_order_finance_reconciliation(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    order = _scoped_order(db, current_user.get_employer_id(), order_id)
    return _reconciliation(db, order)


@router.get("/summary")
def get_marketplace_finance_summary(
    includeCancelled: bool = Query(default=True),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    query = db.query(models.PartnerOrder).filter(models.PartnerOrder.employer_id == employer_id)
    if not includeCancelled:
        query = query.filter(models.PartnerOrder.status != models.PartnerOrderStatus.CANCELLED)
    orders = query.order_by(models.PartnerOrder.id.asc()).all()

    rows = [_reconciliation(db, order) for order in orders]
    recognized_revenue = _money(sum(row["recognizedRevenueAmount"] for row in rows))
    expected_supplier_payable = _money(sum(row["expectedSupplierPayable"] for row in rows))
    invoiced_amount = _money(sum(row["invoicedAmount"] for row in rows))
    current_total = _money(sum(row["currentTotal"] for row in rows if row["status"] != models.PartnerOrderStatus.CANCELLED.value))

    return {
        "ordersCount": len(rows),
        "matchedCount": sum(1 for row in rows if row["reconciliationStatus"] == "MATCHED"),
        "mismatchCount": sum(1 for row in rows if row["reconciliationStatus"] == "AMOUNT_MISMATCH"),
        "waitingInvoiceCount": sum(1 for row in rows if row["reconciliationStatus"] == "WAITING_INVOICE"),
        "waitingReceiptCount": sum(1 for row in rows if row["reconciliationStatus"] == "WAITING_RECEIPT"),
        "cancelledCount": sum(1 for row in rows if row["reconciliationStatus"] == "CANCELLED"),
        "currentOrderAmount": current_total,
        "recognizedRevenueAmount": recognized_revenue,
        "expectedSupplierPayable": expected_supplier_payable,
        "invoicedAmount": invoiced_amount,
        "invoiceVariance": _money(invoiced_amount - expected_supplier_payable),
        "orders": rows,
    }
