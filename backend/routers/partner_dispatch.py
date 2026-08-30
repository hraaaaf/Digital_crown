import hashlib
import ipaddress
import json
import socket
from datetime import datetime
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_dispatch import PartnerOrderDispatch
from backend.routers.auth import require_superadmin
from backend.routers.partner_orders import _append_event, _compute_revenue, _serialize

router = APIRouter()


class SupplierDispatchError(Exception):
    def __init__(self, code: str, detail: str, response_status: int | None = None):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.response_status = response_status


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


def _supplier_for_order(db: Session, employer_id: int, order: models.PartnerOrder) -> models.PartnerSupplier:
    try:
        supplier_id = int(order.partner_id)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=409, detail="Commande sans fournisseur canonique exploitable.") from error

    supplier = (
        db.query(models.PartnerSupplier)
        .filter(
            models.PartnerSupplier.id == supplier_id,
            models.PartnerSupplier.employer_id == employer_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=409, detail="Fournisseur canonique de la commande introuvable.")
    if not supplier.is_active:
        raise HTTPException(status_code=422, detail="Impossible d'envoyer vers un fournisseur inactif.")
    if (supplier.sync_mode or "").strip().lower() != "api":
        raise HTTPException(status_code=422, detail="Le fournisseur doit etre configure en mode API pour un envoi prouve.")
    if not (supplier.api_base_url or "").strip():
        raise HTTPException(status_code=422, detail="Le fournisseur ne dispose pas d'une URL API configuree.")
    return supplier


def _build_supplier_endpoint(api_base_url: str) -> str:
    raw = api_base_url.strip()
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise HTTPException(status_code=422, detail="L'API fournisseur doit utiliser une URL HTTPS valide.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=422, detail="L'URL API fournisseur ne doit contenir ni credentials, query ni fragment.")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        raise HTTPException(status_code=422, detail="Hote API fournisseur prive ou local interdit.")
    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None
    if literal_ip is not None and not literal_ip.is_global:
        raise HTTPException(status_code=422, detail="Adresse IP fournisseur non publique interdite.")

    return f"{raw.rstrip('/')}/orders"


def _assert_public_resolution(endpoint: str) -> None:
    hostname = urlparse(endpoint).hostname
    if not hostname:
        raise SupplierDispatchError("INVALID_ENDPOINT", "Hote fournisseur invalide.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    except OSError as error:
        raise SupplierDispatchError("DNS_FAILURE", "Resolution DNS fournisseur impossible.") from error
    if not addresses:
        raise SupplierDispatchError("DNS_FAILURE", "Aucune adresse fournisseur resolue.")
    for raw_address in addresses:
        try:
            address = ipaddress.ip_address(raw_address)
        except ValueError as error:
            raise SupplierDispatchError("DNS_FAILURE", "Adresse fournisseur resolue invalide.") from error
        if not address.is_global:
            raise SupplierDispatchError("PRIVATE_ENDPOINT", "Resolution fournisseur vers une adresse non publique interdite.")


def _canonical_dispatch_payload(order: models.PartnerOrder, supplier: models.PartnerSupplier) -> dict:
    return {
        "orderNumber": order.order_number,
        "supplierId": supplier.supplier_key,
        "customer": {
            "fullName": order.customer_full_name,
            "clinic": order.customer_clinic,
            "phone": order.customer_phone,
            "email": order.customer_email,
            "city": order.customer_city,
            "note": order.customer_note,
        },
        "lines": order.lines_json or [],
        "total": round(float(order.current_total or order.estimated_total), 2),
        "currency": "MAD",
    }


def _payload_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _post_supplier_order(endpoint: str, payload: dict, idempotency_key: str) -> tuple[int, str]:
    _assert_public_resolution(endpoint)
    try:
        response = httpx.post(
            endpoint,
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "Accept": "application/json",
                "User-Agent": "DigitalCrown-Marketplace/1.0",
            },
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=False,
        )
    except httpx.TimeoutException as error:
        raise SupplierDispatchError("TIMEOUT", "Delai d'envoi fournisseur depasse.") from error
    except httpx.HTTPError as error:
        raise SupplierDispatchError("NETWORK_ERROR", "Connexion API fournisseur impossible.") from error

    if response.status_code < 200 or response.status_code >= 300:
        raise SupplierDispatchError(
            "HTTP_ERROR",
            f"API fournisseur refuse l'envoi avec HTTP {response.status_code}.",
            response_status=response.status_code,
        )
    try:
        data = response.json()
    except ValueError as error:
        raise SupplierDispatchError(
            "INVALID_RESPONSE",
            "API fournisseur: reponse JSON invalide.",
            response_status=response.status_code,
        ) from error

    supplier_reference = str(data.get("reference") or "").strip() if isinstance(data, dict) else ""
    if not supplier_reference:
        raise SupplierDispatchError(
            "MISSING_REFERENCE",
            "API fournisseur: reference de commande absente.",
            response_status=response.status_code,
        )
    if len(supplier_reference) > 120:
        raise SupplierDispatchError(
            "INVALID_REFERENCE",
            "API fournisseur: reference trop longue.",
            response_status=response.status_code,
        )
    return response.status_code, supplier_reference


def _serialize_dispatch(dispatch: PartnerOrderDispatch) -> dict:
    return {
        "id": dispatch.id,
        "orderId": dispatch.order_id,
        "transport": dispatch.transport,
        "endpoint": dispatch.endpoint,
        "requestSha256": dispatch.request_sha256,
        "idempotencyKey": dispatch.idempotency_key,
        "outcome": dispatch.outcome,
        "attemptCount": dispatch.attempt_count,
        "responseStatus": dispatch.response_status,
        "supplierReference": dispatch.supplier_reference,
        "errorCode": dispatch.error_code,
        "errorDetail": dispatch.error_detail,
        "attemptedAt": dispatch.attempted_at.isoformat() if dispatch.attempted_at else None,
        "completedAt": dispatch.completed_at.isoformat() if dispatch.completed_at else None,
    }


@router.get("/{order_id}/dispatch")
def get_partner_order_dispatch(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _scoped_order(db, employer_id, order_id)
    dispatch = (
        db.query(PartnerOrderDispatch)
        .filter(
            PartnerOrderDispatch.order_id == order.id,
            PartnerOrderDispatch.employer_id == employer_id,
        )
        .order_by(PartnerOrderDispatch.id.desc())
        .first()
    )
    return {
        "order": _serialize(order),
        "dispatch": _serialize_dispatch(dispatch) if dispatch else None,
    }


@router.post("/{order_id}/dispatch")
def dispatch_partner_order(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    order = _scoped_order(db, employer_id, order_id)
    supplier = _supplier_for_order(db, employer_id, order)
    endpoint = _build_supplier_endpoint(supplier.api_base_url or "")
    idempotency_key = f"digitalcrown:{order.order_number}"
    payload = _canonical_dispatch_payload(order, supplier)
    request_sha256 = _payload_sha256(payload)

    dispatch = (
        db.query(PartnerOrderDispatch)
        .filter(
            PartnerOrderDispatch.order_id == order.id,
            PartnerOrderDispatch.employer_id == employer_id,
            PartnerOrderDispatch.idempotency_key == idempotency_key,
        )
        .first()
    )

    if dispatch and dispatch.outcome == "SUCCEEDED":
        return {
            "order": _serialize(order),
            "dispatch": _serialize_dispatch(dispatch),
            "idempotentReplay": True,
        }

    if order.status != models.PartnerOrderStatus.DRAFT:
        raise HTTPException(
            status_code=422,
            detail=f"Envoi fournisseur impossible depuis {order.status.value}; DRAFT requis sans preuve existante.",
        )

    if dispatch is None:
        dispatch = PartnerOrderDispatch(
            employer_id=employer_id,
            order_id=order.id,
            supplier_id=supplier.id,
            idempotency_key=idempotency_key,
            transport="HTTP_API",
            endpoint=endpoint,
            request_sha256=request_sha256,
            outcome="PENDING",
            attempt_count=0,
        )
        db.add(dispatch)
        db.flush()
    elif dispatch.request_sha256 != request_sha256 or dispatch.endpoint != endpoint:
        raise HTTPException(
            status_code=409,
            detail="La commande ou la destination fournisseur a change apres une tentative d'envoi; intervention requise.",
        )

    dispatch.attempt_count += 1
    dispatch.attempted_at = datetime.utcnow()
    dispatch.error_code = None
    dispatch.error_detail = None
    dispatch.response_status = None

    try:
        response_status, supplier_reference = _post_supplier_order(endpoint, payload, idempotency_key)
    except SupplierDispatchError as error:
        dispatch.outcome = "FAILED"
        dispatch.response_status = error.response_status
        dispatch.error_code = error.code
        dispatch.error_detail = error.detail[:500]
        dispatch.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=502, detail=error.detail) from error

    previous_status = order.status.value
    revenue_before = order.recognized_revenue_amount
    order.status = models.PartnerOrderStatus.SENT_TO_PARTNER
    order.sent_at = datetime.utcnow()
    order.sent_total = round(float(order.current_total or order.estimated_total), 2)
    order.partner_reference = supplier_reference
    order.last_partner_update_at = datetime.utcnow()
    order.recognized_base_amount, order.recognized_revenue_amount = _compute_revenue(order)
    order.revenue_delta_amount = round(order.recognized_revenue_amount - revenue_before, 2)

    dispatch.outcome = "SUCCEEDED"
    dispatch.response_status = response_status
    dispatch.supplier_reference = supplier_reference
    dispatch.error_code = None
    dispatch.error_detail = None
    dispatch.completed_at = datetime.utcnow()

    _append_event(
        db,
        order,
        event_type="ORDER_DISPATCHED",
        previous_status=previous_status,
        new_status=order.status.value,
        previous_total=order.current_total,
        new_total=order.current_total,
        revenue_before=revenue_before,
        revenue_after=order.recognized_revenue_amount,
        note="Commande envoyee via API fournisseur avec preuve de transport.",
        payload_json={
            "dispatchId": dispatch.id,
            "transport": dispatch.transport,
            "requestSha256": request_sha256,
            "supplierReference": supplier_reference,
            "responseStatus": response_status,
        },
    )
    db.commit()
    db.refresh(dispatch)
    db.refresh(order)
    return {
        "order": _serialize(order),
        "dispatch": _serialize_dispatch(dispatch),
        "idempotentReplay": False,
    }
