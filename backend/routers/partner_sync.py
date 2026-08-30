import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_sync import PartnerSupplierSyncState
from backend.routers.auth import require_superadmin
from backend.routers.partner_dispatch import SupplierDispatchError, _assert_public_resolution, _build_supplier_endpoint

router = APIRouter(prefix="/suppliers")

FRESH_SECONDS = 15 * 60
MAX_PRODUCTS = 5000


class SupplierSyncError(Exception):
    def __init__(self, code: str, detail: str, *, http_status: int = 502):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.http_status = http_status


def _utcnow() -> datetime:
    return datetime.utcnow()


def _scoped_supplier(db: Session, employer_id: int, supplier_id: int) -> models.PartnerSupplier:
    supplier = (
        db.query(models.PartnerSupplier)
        .filter(
            models.PartnerSupplier.id == supplier_id,
            models.PartnerSupplier.employer_id == employer_id,
        )
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Fournisseur partenaire introuvable")
    return supplier


def _sync_state(db: Session, employer_id: int, supplier_id: int) -> PartnerSupplierSyncState:
    state = (
        db.query(PartnerSupplierSyncState)
        .filter(
            PartnerSupplierSyncState.employer_id == employer_id,
            PartnerSupplierSyncState.supplier_id == supplier_id,
        )
        .first()
    )
    if state is None:
        state = PartnerSupplierSyncState(employer_id=employer_id, supplier_id=supplier_id)
        db.add(state)
        db.flush()
    return state


def _catalog_endpoint(api_base_url: str) -> str:
    # Réutilise exactement la validation HTTPS/SSRF certifiée en P6, puis change
    # seulement la ressource terminale du même endpoint fournisseur.
    orders_endpoint = _build_supplier_endpoint(api_base_url)
    if not orders_endpoint.endswith("/orders"):
        raise SupplierSyncError("INVALID_ENDPOINT", "Endpoint fournisseur invalide.", http_status=422)
    return f"{orders_endpoint[:-len('/orders')]}/catalog"


def _fetch_supplier_catalog(endpoint: str) -> dict:
    try:
        _assert_public_resolution(endpoint)
    except SupplierDispatchError as error:
        raise SupplierSyncError(error.code, error.detail) from error

    try:
        response = httpx.get(
            endpoint,
            headers={
                "Accept": "application/json",
                "User-Agent": "DigitalCrown-Marketplace/1.0",
            },
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=False,
        )
    except httpx.TimeoutException as error:
        raise SupplierSyncError("TIMEOUT", "Delai de synchronisation fournisseur depasse.") from error
    except httpx.HTTPError as error:
        raise SupplierSyncError("NETWORK_ERROR", "Connexion API fournisseur impossible.") from error

    if response.status_code < 200 or response.status_code >= 300:
        raise SupplierSyncError(
            "HTTP_ERROR",
            f"API fournisseur refuse la synchronisation avec HTTP {response.status_code}.",
        )
    try:
        payload = response.json()
    except ValueError as error:
        raise SupplierSyncError("INVALID_JSON", "API fournisseur: reponse JSON invalide.") from error
    if not isinstance(payload, dict):
        raise SupplierSyncError("INVALID_PAYLOAD", "API fournisseur: objet JSON attendu.")
    return payload


def _canonical_product(raw: Any) -> dict:
    if not isinstance(raw, dict):
        raise SupplierSyncError("INVALID_PRODUCT", "Produit fournisseur invalide.")

    external_id = str(raw.get("externalProductId") or "").strip() or None
    sku = str(raw.get("sku") or "").strip()
    name = str(raw.get("name") or "").strip()
    category = str(raw.get("dentalCategory") or "").strip()
    specialty = str(raw.get("dentalSpecialty") or "").strip()
    unit = str(raw.get("unit") or "").strip()
    if not sku or not name or not category or not specialty or not unit:
        raise SupplierSyncError(
            "INVALID_PRODUCT",
            "Produit fournisseur incomplet: sku, name, dentalCategory, dentalSpecialty et unit sont requis.",
        )

    try:
        price = round(float(raw.get("price")), 2)
    except (TypeError, ValueError) as error:
        raise SupplierSyncError("INVALID_PRODUCT", f"Prix invalide pour {sku}.") from error
    if price < 0:
        raise SupplierSyncError("INVALID_PRODUCT", f"Prix negatif interdit pour {sku}.")

    availability_raw = str(raw.get("availability") or "").strip()
    try:
        availability = models.PartnerProductAvailability(availability_raw)
    except ValueError as error:
        raise SupplierSyncError("INVALID_PRODUCT", f"Disponibilite invalide pour {sku}.") from error

    benefits = raw.get("benefits") or []
    if not isinstance(benefits, list) or any(not isinstance(item, str) for item in benefits):
        raise SupplierSyncError("INVALID_PRODUCT", f"Benefits invalides pour {sku}.")

    return {
        "externalProductId": external_id,
        "sku": sku,
        "name": name,
        "dentalCategory": category,
        "dentalSpecialty": specialty,
        "unit": unit,
        "price": price,
        "availability": availability.value,
        "shortDescription": str(raw.get("shortDescription") or "").strip() or None,
        "longDescription": str(raw.get("longDescription") or "").strip() or None,
        "benefits": benefits,
    }


def _canonical_snapshot(payload: dict) -> tuple[str | None, list[dict], str]:
    products_raw = payload.get("products")
    if not isinstance(products_raw, list):
        raise SupplierSyncError("INVALID_PAYLOAD", "API fournisseur: products[] requis.")
    if len(products_raw) > MAX_PRODUCTS:
        raise SupplierSyncError("PAYLOAD_TOO_LARGE", f"Catalogue limite a {MAX_PRODUCTS} produits.")

    products = [_canonical_product(raw) for raw in products_raw]
    external_ids: set[str] = set()
    skus: set[str] = set()
    for product in products:
        external_id = product["externalProductId"]
        sku_key = product["sku"].casefold()
        if external_id:
            external_key = external_id.casefold()
            if external_key in external_ids:
                raise SupplierSyncError("DUPLICATE_IDENTITY", f"externalProductId duplique: {external_id}.")
            external_ids.add(external_key)
        if sku_key in skus:
            raise SupplierSyncError("DUPLICATE_IDENTITY", f"SKU duplique: {product['sku']}.")
        skus.add(sku_key)

    products.sort(key=lambda item: ((item["externalProductId"] or "").casefold(), item["sku"].casefold()))
    version = str(payload.get("version") or "").strip() or None
    canonical = json.dumps(
        {"version": version, "products": products},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return version, products, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _freshness(state: PartnerSupplierSyncState, now: datetime | None = None) -> dict:
    now = now or _utcnow()
    if state.last_outcome == "FAILED":
        status = "DEGRADED"
    elif state.last_success_at is None:
        status = "NEVER_SYNCED"
    else:
        age_seconds = max(0, int((now - state.last_success_at).total_seconds()))
        status = "FRESH" if age_seconds <= FRESH_SECONDS else "STALE"
    age = None if state.last_success_at is None else max(0, int((now - state.last_success_at).total_seconds()))
    return {
        "status": status,
        "ageSeconds": age,
        "freshForSeconds": FRESH_SECONDS,
        "hasUsableBaseline": state.last_success_at is not None,
    }


def _state_payload(state: PartnerSupplierSyncState) -> dict:
    return {
        "supplierId": state.supplier_id,
        "lastAttemptAt": state.last_attempt_at.isoformat() if state.last_attempt_at else None,
        "lastSuccessAt": state.last_success_at.isoformat() if state.last_success_at else None,
        "lastOutcome": state.last_outcome,
        "lastErrorCode": state.last_error_code,
        "lastErrorDetail": state.last_error_detail,
        "consecutiveFailures": state.consecutive_failures,
        "nextRetryAt": state.next_retry_at.isoformat() if state.next_retry_at else None,
        "lastPayloadSha256": state.last_payload_sha256,
        "lastCatalogVersion": state.last_catalog_version,
        "lastProductCount": state.last_product_count,
        "freshness": _freshness(state),
    }


def _record_failure(db: Session, state: PartnerSupplierSyncState, error: SupplierSyncError) -> None:
    now = _utcnow()
    failures = int(state.consecutive_failures or 0) + 1
    delay_seconds = min(60 * (2 ** (failures - 1)), 3600)
    state.last_attempt_at = now
    state.last_outcome = "FAILED"
    state.last_error_code = error.code
    state.last_error_detail = error.detail[:500]
    state.consecutive_failures = failures
    state.next_retry_at = now + timedelta(seconds=delay_seconds)
    db.commit()


def _apply_snapshot(
    db: Session,
    supplier: models.PartnerSupplier,
    products: list[dict],
) -> dict:
    existing = (
        db.query(models.PartnerCatalogProduct)
        .filter(
            models.PartnerCatalogProduct.employer_id == supplier.employer_id,
            models.PartnerCatalogProduct.supplier_id == supplier.id,
        )
        .all()
    )
    by_external = {
        str(item.external_product_id).casefold(): item
        for item in existing
        if item.external_product_id
    }
    by_sku = {str(item.sku).casefold(): item for item in existing}

    plan: list[tuple[models.PartnerCatalogProduct | None, dict]] = []
    seen_existing: set[int] = set()
    for product in products:
        ext_match = by_external.get(product["externalProductId"].casefold()) if product["externalProductId"] else None
        sku_match = by_sku.get(product["sku"].casefold())
        if ext_match is not None and sku_match is not None and ext_match.id != sku_match.id:
            raise SupplierSyncError(
                "IDENTITY_CONFLICT",
                f"Conflit externalProductId/SKU pour {product['sku']}.",
                http_status=409,
            )
        target = ext_match or sku_match
        if target is not None:
            if target.id in seen_existing:
                raise SupplierSyncError("IDENTITY_CONFLICT", f"Produit local cible plusieurs fois: {product['sku']}.", http_status=409)
            seen_existing.add(target.id)
        plan.append((target, product))

    created = 0
    updated = 0
    for target, product in plan:
        availability = models.PartnerProductAvailability(product["availability"])
        if target is None:
            target = models.PartnerCatalogProduct(
                employer_id=supplier.employer_id,
                supplier_id=supplier.id,
                external_product_id=product["externalProductId"],
                name=product["name"],
                sku=product["sku"],
                dental_category=product["dentalCategory"],
                dental_specialty=product["dentalSpecialty"],
                unit=product["unit"],
                price=product["price"],
                availability=availability,
                short_description=product["shortDescription"],
                long_description=product["longDescription"],
                benefits_json=product["benefits"],
                is_featured=False,
                sort_order=0,
            )
            db.add(target)
            created += 1
            continue

        before = (
            target.external_product_id,
            target.name,
            target.sku,
            target.dental_category,
            target.dental_specialty,
            target.unit,
            round(float(target.price), 2),
            target.availability.value,
            target.short_description,
            target.long_description,
            target.benefits_json or [],
        )
        target.external_product_id = product["externalProductId"] or target.external_product_id
        target.name = product["name"]
        target.sku = product["sku"]
        target.dental_category = product["dentalCategory"]
        target.dental_specialty = product["dentalSpecialty"]
        target.unit = product["unit"]
        target.price = product["price"]
        target.availability = availability
        target.short_description = product["shortDescription"]
        target.long_description = product["longDescription"]
        target.benefits_json = product["benefits"]
        after = (
            target.external_product_id,
            target.name,
            target.sku,
            target.dental_category,
            target.dental_specialty,
            target.unit,
            round(float(target.price), 2),
            target.availability.value,
            target.short_description,
            target.long_description,
            target.benefits_json or [],
        )
        if before != after:
            updated += 1

    return {"created": created, "updated": updated, "received": len(products)}


@router.get("/{supplier_id}/sync-status")
def get_supplier_sync_status(
    supplier_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    supplier = _scoped_supplier(db, employer_id, supplier_id)
    state = _sync_state(db, employer_id, supplier.id)
    db.commit()
    return _state_payload(state)


@router.post("/{supplier_id}/sync")
def sync_supplier_catalog(
    supplier_id: int,
    force: bool = Query(default=False),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_superadmin),
):
    employer_id = current_user.get_employer_id()
    supplier = _scoped_supplier(db, employer_id, supplier_id)
    if not supplier.is_active:
        raise HTTPException(status_code=422, detail="Synchronisation interdite pour un fournisseur inactif.")
    if (supplier.sync_mode or "").strip().lower() != "api":
        raise HTTPException(status_code=422, detail="Le fournisseur doit etre configure en mode API.")
    if not (supplier.api_base_url or "").strip():
        raise HTTPException(status_code=422, detail="URL API fournisseur absente.")

    state = _sync_state(db, employer_id, supplier.id)
    now = _utcnow()
    if not force and state.next_retry_at and state.next_retry_at > now:
        retry_seconds = max(1, int((state.next_retry_at - now).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail={"code": "SYNC_BACKOFF", "retryAfterSeconds": retry_seconds},
        )

    try:
        endpoint = _catalog_endpoint(supplier.api_base_url or "")
        payload = _fetch_supplier_catalog(endpoint)
        version, products, payload_sha256 = _canonical_snapshot(payload)
    except HTTPException:
        raise
    except SupplierSyncError as error:
        _record_failure(db, state, error)
        raise HTTPException(status_code=error.http_status, detail=error.detail) from error

    if state.last_outcome == "SUCCESS" and state.last_payload_sha256 == payload_sha256:
        state.last_attempt_at = now
        state.last_success_at = now
        state.last_outcome = "SUCCESS"
        state.last_error_code = None
        state.last_error_detail = None
        state.consecutive_failures = 0
        state.next_retry_at = None
        state.last_catalog_version = version
        state.last_product_count = len(products)
        db.commit()
        return {
            "idempotentReplay": True,
            "changes": {"created": 0, "updated": 0, "received": len(products)},
            "sync": _state_payload(state),
        }

    try:
        changes = _apply_snapshot(db, supplier, products)
        state.last_attempt_at = now
        state.last_success_at = now
        state.last_outcome = "SUCCESS"
        state.last_error_code = None
        state.last_error_detail = None
        state.consecutive_failures = 0
        state.next_retry_at = None
        state.last_payload_sha256 = payload_sha256
        state.last_catalog_version = version
        state.last_product_count = len(products)
        db.commit()
    except SupplierSyncError as error:
        db.rollback()
        state = _sync_state(db, employer_id, supplier.id)
        _record_failure(db, state, error)
        raise HTTPException(status_code=error.http_status, detail=error.detail) from error
    except Exception:
        db.rollback()
        state = _sync_state(db, employer_id, supplier.id)
        error = SupplierSyncError("SYNC_WRITE_FAILED", "Echec d'ecriture du catalogue fournisseur.")
        _record_failure(db, state, error)
        raise HTTPException(status_code=500, detail=error.detail)

    return {
        "idempotentReplay": False,
        "changes": changes,
        "sync": _state_payload(state),
    }
