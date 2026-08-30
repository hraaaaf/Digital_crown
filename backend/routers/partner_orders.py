from datetime import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission, require_superadmin

router = APIRouter()


STRATEGY_PRESETS = [
    {
        "key": "sent_commission_10",
        "label": "Commission sur commande envoyée",
        "settlementBasis": "SENT_TO_PARTNER",
        "revenueModel": "COMMISSION_PERCENT",
        "commissionRate": 10.0,
        "discountRate": 0.0,
        "fixedFeeAmount": 0.0,
        "description": "Vous êtes rémunéré dès que la commande est envoyée au fournisseur."
    },
    {
        "key": "confirmed_commission_10",
        "label": "Commission sur commande confirmée",
        "settlementBasis": "CONFIRMED",
        "revenueModel": "COMMISSION_PERCENT",
        "commissionRate": 10.0,
        "discountRate": 0.0,
        "fixedFeeAmount": 0.0,
        "description": "Le revenu n'est reconnu qu'à confirmation fournisseur."
    },
    {
        "key": "resale_discount_30",
        "label": "Remise fournisseur puis revente",
        "settlementBasis": "SENT_TO_PARTNER",
        "revenueModel": "DISCOUNT_RESALE",
        "commissionRate": 0.0,
        "discountRate": 30.0,
        "fixedFeeAmount": 0.0,
        "description": "Le fournisseur vous accorde une remise, vous revendez ensuite à votre prix."
    },
    {
        "key": "fixed_fee_per_order",
        "label": "Forfait fixe par commande",
        "settlementBasis": "SENT_TO_PARTNER",
        "revenueModel": "FIXED_FEE_PER_ORDER",
        "commissionRate": 0.0,
        "discountRate": 0.0,
        "fixedFeeAmount": 150.0,
        "description": "Vous percevez un montant fixe a chaque commande envoyee."
    },
]


ORDER_TRANSITIONS = {
    models.PartnerOrderStatus.DRAFT: (
        models.PartnerOrderStatus.SENT_TO_PARTNER,
        models.PartnerOrderStatus.CANCELLED,
    ),
    models.PartnerOrderStatus.SENT_TO_PARTNER: (
        models.PartnerOrderStatus.MODIFIED_AFTER_SEND,
        models.PartnerOrderStatus.CONFIRMED,
        models.PartnerOrderStatus.CANCELLED,
    ),
    models.PartnerOrderStatus.MODIFIED_AFTER_SEND: (
        models.PartnerOrderStatus.MODIFIED_AFTER_SEND,
        models.PartnerOrderStatus.CONFIRMED,
        models.PartnerOrderStatus.CANCELLED,
    ),
    models.PartnerOrderStatus.CONFIRMED: (
        models.PartnerOrderStatus.FULFILLED,
        models.PartnerOrderStatus.CANCELLED,
    ),
    models.PartnerOrderStatus.FULFILLED: (),
    models.PartnerOrderStatus.CANCELLED: (),
}


class PartnerOrderLineIn(BaseModel):
    productId: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unitPrice: float = Field(..., ge=0)
    lineTotal: float = Field(..., ge=0)


class PartnerOrderCustomerIn(BaseModel):
    fullName: str = Field(..., min_length=1)
    clinic: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    city: str = Field(..., min_length=1)
    note: Optional[str] = None


class PartnerOrderCreateIn(BaseModel):
    partnerId: str = Field(..., min_length=1)
    partnerName: str = Field(..., min_length=1)
    strategyLabel: str = Field(..., min_length=1)
    settlementBasis: str = Field(..., min_length=1)
    revenueModel: str = Field(..., min_length=1)
    commissionRate: float = Field(0.0, ge=0)
    discountRate: float = Field(0.0, ge=0)
    fixedFeeAmount: float = Field(0.0, ge=0)
    customer: PartnerOrderCustomerIn
    lines: List[PartnerOrderLineIn] = Field(..., min_length=1)
    estimatedTotal: float = Field(..., ge=0)


class PartnerOrderUpdateIn(BaseModel):
    status: str = Field(..., min_length=1)
    currentTotal: Optional[float] = Field(None, ge=0)
    partnerReference: Optional[str] = None
    note: Optional[str] = None


def _allowed_transitions(status_value: models.PartnerOrderStatus) -> tuple[models.PartnerOrderStatus, ...]:
    return ORDER_TRANSITIONS[status_value]


def _serialize(order: models.PartnerOrder) -> dict:
    return {
        "id": order.id,
        "orderNumber": order.order_number,
        "partnerId": order.partner_id,
        "partnerName": order.partner_name,
        "status": order.status.value,
        "allowedTransitions": [item.value for item in _allowed_transitions(order.status)],
        "strategyLabel": order.strategy_label,
        "settlementBasis": order.settlement_basis.value,
        "revenueModel": order.revenue_model.value,
        "commissionRate": order.commission_rate,
        "discountRate": order.discount_rate,
        "fixedFeeAmount": order.fixed_fee_amount,
        "customer": {
            "fullName": order.customer_full_name,
            "clinic": order.customer_clinic,
            "phone": order.customer_phone,
            "email": order.customer_email,
            "city": order.customer_city,
            "note": order.customer_note or "",
        },
        "lines": order.lines_json,
        "estimatedTotal": order.estimated_total,
        "sentTotal": order.sent_total,
        "currentTotal": order.current_total,
        "recognizedBaseAmount": order.recognized_base_amount,
        "recognizedRevenueAmount": order.recognized_revenue_amount,
        "revenueDeltaAmount": order.revenue_delta_amount,
        "partnerReference": order.partner_reference,
        "statusNote": order.status_note,
        "sentAt": order.sent_at.isoformat() if order.sent_at else None,
        "lastPartnerUpdateAt": order.last_partner_update_at.isoformat() if order.last_partner_update_at else None,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
        "updatedAt": order.updated_at.isoformat() if order.updated_at else None,
        "events": [
            {
                "id": event.id,
                "eventType": event.event_type,
                "previousStatus": event.previous_status,
                "newStatus": event.new_status,
                "previousTotal": event.previous_total,
                "newTotal": event.new_total,
                "revenueBefore": event.revenue_before,
                "revenueAfter": event.revenue_after,
                "deltaAmount": event.delta_amount,
                "note": event.note,
                "createdAt": event.created_at.isoformat() if event.created_at else None,
            }
            for event in order.events[:5]
        ],
    }


def _build_order_number() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"CMD-PART-{stamp}-{suffix}"


def _coerce_settlement_basis(value: str) -> models.PartnerSettlementBasis:
    try:
        return models.PartnerSettlementBasis(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"Base de remuneration invalide: {value}") from error


def _coerce_revenue_model(value: str) -> models.PartnerRevenueModel:
    try:
        return models.PartnerRevenueModel(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"Mode de remuneration invalide: {value}") from error


def _coerce_order_status(value: str) -> models.PartnerOrderStatus:
    try:
        return models.PartnerOrderStatus(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"Statut partenaire invalide: {value}") from error


def _same_money_value(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) < 0.000001


def _resolve_strategy(payload: PartnerOrderCreateIn) -> dict:
    """Mappe le contrat client sur un preset autorisé puis retourne la version canonique serveur."""
    for preset in STRATEGY_PRESETS:
        if (
            payload.settlementBasis == preset["settlementBasis"]
            and payload.revenueModel == preset["revenueModel"]
            and _same_money_value(payload.commissionRate, preset["commissionRate"])
            and _same_money_value(payload.discountRate, preset["discountRate"])
            and _same_money_value(payload.fixedFeeAmount, preset["fixedFeeAmount"])
        ):
            return preset
    raise HTTPException(
        status_code=422,
        detail="Strategie commerciale non autorisee. Rechargez les options Marketplace avant de recommander.",
    )


def _parse_product_id(raw_product_id: str) -> int:
    try:
        product_id = int(raw_product_id)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Identifiant produit invalide: {raw_product_id}") from error
    if product_id <= 0:
        raise HTTPException(status_code=422, detail=f"Identifiant produit invalide: {raw_product_id}")
    return product_id


def _build_canonical_order_lines(
    db: Session,
    employer_id: int,
    requested_lines: List[PartnerOrderLineIn],
) -> tuple[models.PartnerSupplier, list[dict], float]:
    """Reconstruit fournisseur, lignes et total depuis le catalogue serveur."""
    product_ids: list[int] = []
    quantities: dict[int, int] = {}
    for line in requested_lines:
        product_id = _parse_product_id(line.productId)
        if product_id in quantities:
            raise HTTPException(status_code=422, detail=f"Produit duplique dans la commande: {product_id}")
        product_ids.append(product_id)
        quantities[product_id] = line.quantity

    products = (
        db.query(models.PartnerCatalogProduct)
        .filter(
            models.PartnerCatalogProduct.employer_id == employer_id,
            models.PartnerCatalogProduct.id.in_(product_ids),
        )
        .all()
    )
    products_by_id = {product.id: product for product in products}
    missing_ids = [product_id for product_id in product_ids if product_id not in products_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=422,
            detail=f"Produit(s) indisponible(s) dans le catalogue du cabinet: {', '.join(map(str, missing_ids))}",
        )

    supplier_ids = {product.supplier_id for product in products}
    if len(supplier_ids) != 1:
        raise HTTPException(
            status_code=422,
            detail="Une commande partenaire ne peut contenir que les produits d'un seul fournisseur.",
        )

    supplier_id = next(iter(supplier_ids))
    supplier = (
        db.query(models.PartnerSupplier)
        .filter(
            models.PartnerSupplier.employer_id == employer_id,
            models.PartnerSupplier.id == supplier_id,
        )
        .first()
    )
    if not supplier or not supplier.is_active:
        raise HTTPException(status_code=422, detail="Le fournisseur de cette commande n'est pas actif.")

    canonical_lines: list[dict] = []
    estimated_total = 0.0
    for product_id in product_ids:
        product = products_by_id[product_id]
        if product.availability == models.PartnerProductAvailability.DISCONTINUED:
            raise HTTPException(status_code=422, detail=f"Produit retire du catalogue: {product.name}")

        quantity = quantities[product_id]
        unit_price = round(float(product.price), 2)
        line_total = round(unit_price * quantity, 2)
        canonical_lines.append(
            {
                "productId": str(product.id),
                "name": product.name,
                "sku": product.sku,
                "quantity": quantity,
                "unitPrice": unit_price,
                "lineTotal": line_total,
            }
        )
        estimated_total += line_total

    return supplier, canonical_lines, round(estimated_total, 2)


def _should_recognize(settlement_basis: models.PartnerSettlementBasis, status_value: models.PartnerOrderStatus) -> bool:
    if status_value == models.PartnerOrderStatus.CANCELLED:
        return False
    if settlement_basis == models.PartnerSettlementBasis.SENT_TO_PARTNER:
        return status_value in {
            models.PartnerOrderStatus.SENT_TO_PARTNER,
            models.PartnerOrderStatus.MODIFIED_AFTER_SEND,
            models.PartnerOrderStatus.CONFIRMED,
            models.PartnerOrderStatus.FULFILLED,
        }
    if settlement_basis == models.PartnerSettlementBasis.CONFIRMED:
        return status_value in {models.PartnerOrderStatus.CONFIRMED, models.PartnerOrderStatus.FULFILLED}
    return status_value == models.PartnerOrderStatus.FULFILLED


def _compute_revenue(order: models.PartnerOrder) -> tuple[float, float]:
    if not _should_recognize(order.settlement_basis, order.status):
        return 0.0, 0.0

    # current_total starts equal to sent_total and only changes through the
    # MODIFIED_AFTER_SEND transition. Keep that supplier-adjusted amount
    # through CONFIRMED/FULFILLED instead of reverting to the initial snapshot.
    base_amount = order.current_total

    if order.revenue_model == models.PartnerRevenueModel.COMMISSION_PERCENT:
        revenue = base_amount * (order.commission_rate / 100.0)
    elif order.revenue_model == models.PartnerRevenueModel.DISCOUNT_RESALE:
        revenue = base_amount * (order.discount_rate / 100.0)
    else:
        revenue = order.fixed_fee_amount if base_amount > 0 else 0.0

    return round(base_amount, 2), round(revenue, 2)


def _validate_order_transition(
    order: models.PartnerOrder,
    target_status: models.PartnerOrderStatus,
    payload: PartnerOrderUpdateIn,
) -> None:
    allowed = _allowed_transitions(order.status)
    if target_status not in allowed:
        allowed_label = ", ".join(item.value for item in allowed) or "aucune"
        raise HTTPException(
            status_code=422,
            detail=f"Transition partenaire invalide: {order.status.value} -> {target_status.value}. Autorisees: {allowed_label}.",
        )

    if target_status == models.PartnerOrderStatus.MODIFIED_AFTER_SEND:
        if order.sent_at is None:
            raise HTTPException(status_code=422, detail="Impossible de modifier une commande non envoyee.")
        if payload.currentTotal is None:
            raise HTTPException(status_code=422, detail="currentTotal est requis pour une modification apres envoi.")
        if _same_money_value(payload.currentTotal, order.current_total):
            raise HTTPException(status_code=422, detail="Le total modifie doit differer du total courant.")
    elif payload.currentTotal is not None and not _same_money_value(payload.currentTotal, order.current_total):
        raise HTTPException(
            status_code=422,
            detail="currentTotal ne peut changer que via le statut MODIFIED_AFTER_SEND.",
        )


def _append_event(
    db: Session,
    order: models.PartnerOrder,
    *,
    event_type: str,
    previous_status: Optional[str],
    new_status: str,
    previous_total: Optional[float],
    new_total: float,
    revenue_before: Optional[float],
    revenue_after: float,
    note: Optional[str],
    payload_json: Optional[dict] = None,
):
    event = models.PartnerOrderEvent(
        order_id=order.id,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        previous_total=previous_total,
        new_total=new_total,
        revenue_before=revenue_before,
        revenue_after=revenue_after,
        delta_amount=round(revenue_after - (revenue_before or 0.0), 2),
        note=note,
        payload_json=payload_json,
    )
    db.add(event)


@router.get("/meta")
def get_partner_order_meta(
    current_user: models.User = Depends(require_permission("patients"))
):
    return {
        "supportedStatuses": [status.value for status in models.PartnerOrderStatus],
        "allowedTransitions": {
            status.value: [item.value for item in _allowed_transitions(status)]
            for status in models.PartnerOrderStatus
        },
        "supportedSettlementBases": [item.value for item in models.PartnerSettlementBasis],
        "supportedRevenueModels": [item.value for item in models.PartnerRevenueModel],
        "strategyPresets": STRATEGY_PRESETS,
        "businessRule": "Le revenu reconnu depend de la base de remuneration choisie et peut etre recalcule en cas de modification ou annulation."
    }


@router.get("", response_model=List[dict])
def list_partner_orders(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    orders = (
        db.query(models.PartnerOrder)
        .filter(models.PartnerOrder.employer_id == employer_id)
        .order_by(models.PartnerOrder.created_at.desc(), models.PartnerOrder.id.desc())
        .all()
    )
    return [_serialize(order) for order in orders]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_partner_order(
    payload: PartnerOrderCreateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    if not payload.lines:
        raise HTTPException(status_code=422, detail="La commande doit contenir au moins une ligne.")

    strategy = _resolve_strategy(payload)
    supplier, canonical_lines, estimated_total = _build_canonical_order_lines(db, employer_id, payload.lines)
    settlement_basis = _coerce_settlement_basis(strategy["settlementBasis"])
    revenue_model = _coerce_revenue_model(strategy["revenueModel"])

    order = models.PartnerOrder(
        employer_id=employer_id,
        order_number=_build_order_number(),
        partner_id=str(supplier.id),
        partner_name=supplier.name,
        status=models.PartnerOrderStatus.DRAFT,
        settlement_basis=settlement_basis,
        revenue_model=revenue_model,
        strategy_label=strategy["label"],
        commission_rate=float(strategy["commissionRate"]),
        discount_rate=float(strategy["discountRate"]),
        fixed_fee_amount=float(strategy["fixedFeeAmount"]),
        customer_full_name=payload.customer.fullName,
        customer_clinic=payload.customer.clinic,
        customer_phone=payload.customer.phone,
        customer_email=payload.customer.email,
        customer_city=payload.customer.city,
        customer_note=payload.customer.note,
        lines_json=canonical_lines,
        estimated_total=estimated_total,
        current_total=estimated_total,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    _append_event(
        db,
        order,
        event_type="ORDER_CREATED",
        previous_status=None,
        new_status=order.status.value,
        previous_total=None,
        new_total=order.current_total,
        revenue_before=None,
        revenue_after=order.recognized_revenue_amount,
        note="Commande preparee dans DigitalCrown.",
        payload_json={
            "strategyKey": strategy["key"],
            "pricingAuthority": "SERVER_CATALOG",
            "supplierId": supplier.id,
        },
    )
    db.commit()
    db.refresh(order)
    return _serialize(order)


@router.patch("/{order_id}")
def update_partner_order(
    order_id: int,
    payload: PartnerOrderUpdateIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin)
):
    employer_id = current_user.get_employer_id()
    order = (
        db.query(models.PartnerOrder)
        .filter(models.PartnerOrder.id == order_id, models.PartnerOrder.employer_id == employer_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Commande partenaire introuvable")

    previous_status = order.status.value
    previous_total = order.current_total
    revenue_before = order.recognized_revenue_amount
    target_status = _coerce_order_status(payload.status)
    _validate_order_transition(order, target_status, payload)

    if target_status == models.PartnerOrderStatus.MODIFIED_AFTER_SEND and payload.currentTotal is not None:
        order.current_total = round(payload.currentTotal, 2)
    if payload.partnerReference is not None:
        order.partner_reference = payload.partnerReference
    if payload.note is not None:
        order.status_note = payload.note

    if target_status == models.PartnerOrderStatus.SENT_TO_PARTNER:
        order.sent_at = datetime.utcnow()
        order.sent_total = order.current_total or order.estimated_total

    order.status = target_status
    order.last_partner_update_at = datetime.utcnow()
    order.recognized_base_amount, order.recognized_revenue_amount = _compute_revenue(order)
    order.revenue_delta_amount = round(order.recognized_revenue_amount - revenue_before, 2)

    _append_event(
        db,
        order,
        event_type="STATUS_UPDATED",
        previous_status=previous_status,
        new_status=order.status.value,
        previous_total=previous_total,
        new_total=order.current_total,
        revenue_before=revenue_before,
        revenue_after=order.recognized_revenue_amount,
        note=payload.note,
        payload_json={"partnerReference": payload.partnerReference},
    )
    db.commit()
    db.refresh(order)
    return _serialize(order)
