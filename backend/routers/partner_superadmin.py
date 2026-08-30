from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_marketplace_finance import PartnerSupplierInvoice
from backend.models_marketplace_governance import MarketplaceGovernanceEvent, PartnerSupplierAgreement
from backend.models_marketplace_sync import PartnerSupplierSyncState
from backend.routers.auth import require_superadmin
from backend.routers.partner_sync import _freshness

router = APIRouter(prefix="/marketplace")
AGREEMENT_STATUSES = {"NONE", "DRAFT", "ACTIVE", "SUSPENDED", "TERMINATED"}


class SupplierGovernanceIn(BaseModel):
    confirm: bool = False
    isActive: Optional[bool] = None
    agreementStatus: Optional[str] = None
    agreementReference: Optional[str] = Field(None, max_length=160)
    effectiveAt: Optional[datetime] = None
    expiresAt: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=4000)


def _supplier(db: Session, supplier_id: int):
    item = db.query(models.PartnerSupplier).filter(models.PartnerSupplier.id == supplier_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Fournisseur Marketplace introuvable")
    return item


def _agreement(db: Session, supplier):
    return db.query(PartnerSupplierAgreement).filter(
        PartnerSupplierAgreement.employer_id == supplier.employer_id,
        PartnerSupplierAgreement.supplier_id == supplier.id,
    ).first()


def _agreement_payload(item):
    if item is None:
        return {"status": "NONE", "reference": None, "effectiveAt": None, "expiresAt": None, "notes": None}
    effective = "EXPIRED" if item.status == "ACTIVE" and item.expires_at and item.expires_at < datetime.utcnow() else item.status
    return {
        "status": effective,
        "storedStatus": item.status,
        "reference": item.reference,
        "effectiveAt": item.effective_at.isoformat() if item.effective_at else None,
        "expiresAt": item.expires_at.isoformat() if item.expires_at else None,
        "notes": item.notes,
    }


def _owner(db: Session, employer_id: int):
    user = db.query(models.User).filter(models.User.id == employer_id).first()
    return {"employerId": employer_id, "ownerEmail": user.email if user else None, "ownerName": user.nom_complet if user else None}


def _audit(db, admin, supplier, before, after):
    db.add(MarketplaceGovernanceEvent(
        admin_user_id=admin.id,
        employer_id=supplier.employer_id,
        entity_type="SUPPLIER",
        entity_id=str(supplier.id),
        action="SUPPLIER_GOVERNANCE_UPDATED",
        payload_json={"before": before, "after": after},
    ))


@router.get("/overview")
def overview(db: Session = Depends(database.get_db), admin: models.User = Depends(require_superadmin)):
    suppliers = db.query(models.PartnerSupplier).all()
    orders = db.query(models.PartnerOrder).all()
    sync_states = db.query(PartnerSupplierSyncState).all()
    agreements = db.query(PartnerSupplierAgreement).all()
    invoices = db.query(PartnerSupplierInvoice).all()
    employers = {x.employer_id for x in suppliers} | {x.employer_id for x in orders}
    statuses = {x.value: 0 for x in models.PartnerOrderStatus}
    for order in orders:
        statuses[order.status.value] += 1
    freshness = [_freshness(state)["status"] for state in sync_states]
    return {
        "cabinetsCount": len(employers),
        "suppliersCount": len(suppliers),
        "activeSuppliersCount": sum(x.is_active for x in suppliers),
        "productsCount": db.query(models.PartnerCatalogProduct).count(),
        "ordersCount": len(orders),
        "ordersByStatus": statuses,
        "recognizedRevenueAmount": round(sum(float(x.recognized_revenue_amount or 0) for x in orders), 2),
        "invoicedSupplierAmount": round(sum(float(x.amount_total or 0) for x in invoices), 2),
        "syncDegradedCount": freshness.count("DEGRADED"),
        "syncStaleCount": freshness.count("STALE"),
        "activeAgreementsCount": sum(_agreement_payload(x)["status"] == "ACTIVE" for x in agreements),
    }


@router.get("/orders")
def global_orders(
    employerId: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    query = db.query(models.PartnerOrder)
    if employerId is not None:
        query = query.filter(models.PartnerOrder.employer_id == employerId)
    if status:
        try:
            state = models.PartnerOrderStatus(status)
        except ValueError as error:
            raise HTTPException(status_code=422, detail="Statut Marketplace invalide") from error
        query = query.filter(models.PartnerOrder.status == state)
    items = query.order_by(models.PartnerOrder.id.desc()).limit(limit).all()
    return [{
        **_owner(db, x.employer_id),
        "id": x.id,
        "orderNumber": x.order_number,
        "supplierName": x.partner_name,
        "status": x.status.value,
        "currentTotal": round(float(x.current_total or 0), 2),
        "recognizedRevenueAmount": round(float(x.recognized_revenue_amount or 0), 2),
        "partnerReference": x.partner_reference,
    } for x in items]


@router.get("/sync-incidents")
def sync_incidents(db: Session = Depends(database.get_db), admin: models.User = Depends(require_superadmin)):
    states = db.query(PartnerSupplierSyncState).order_by(PartnerSupplierSyncState.id.desc()).all()
    result = []
    for state in states:
        fresh = _freshness(state)
        if fresh["status"] not in {"DEGRADED", "STALE"}:
            continue
        supplier = db.query(models.PartnerSupplier).filter(models.PartnerSupplier.id == state.supplier_id).first()
        result.append({
            **_owner(db, state.employer_id),
            "supplierId": state.supplier_id,
            "supplierName": supplier.name if supplier else None,
            "freshness": fresh,
            "lastErrorCode": state.last_error_code,
            "lastErrorDetail": state.last_error_detail,
            "consecutiveFailures": state.consecutive_failures,
            "nextRetryAt": state.next_retry_at.isoformat() if state.next_retry_at else None,
        })
    return result


@router.get("/suppliers/{supplier_id}/governance")
def get_governance(supplier_id: int, db: Session = Depends(database.get_db), admin: models.User = Depends(require_superadmin)):
    supplier = _supplier(db, supplier_id)
    return {
        **_owner(db, supplier.employer_id),
        "supplierId": supplier.id,
        "supplierName": supplier.name,
        "isActive": supplier.is_active,
        "syncMode": supplier.sync_mode,
        "agreement": _agreement_payload(_agreement(db, supplier)),
    }


@router.patch("/suppliers/{supplier_id}/governance")
def update_governance(
    supplier_id: int,
    payload: SupplierGovernanceIn,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    if payload.confirm is not True:
        raise HTTPException(status_code=409, detail="Confirmation explicite requise pour une mutation Marketplace globale.")
    if payload.agreementStatus is not None and payload.agreementStatus not in AGREEMENT_STATUSES:
        raise HTTPException(status_code=422, detail="Statut d'accord invalide")
    if payload.effectiveAt and payload.expiresAt and payload.expiresAt <= payload.effectiveAt:
        raise HTTPException(status_code=422, detail="expiresAt doit être postérieur à effectiveAt")

    supplier = _supplier(db, supplier_id)
    agreement = _agreement(db, supplier)
    before = {"isActive": supplier.is_active, "agreement": _agreement_payload(agreement)}
    if payload.isActive is not None:
        supplier.is_active = payload.isActive
    if any(x is not None for x in (payload.agreementStatus, payload.agreementReference, payload.effectiveAt, payload.expiresAt, payload.notes)):
        if agreement is None:
            agreement = PartnerSupplierAgreement(employer_id=supplier.employer_id, supplier_id=supplier.id)
            db.add(agreement)
        if payload.agreementStatus is not None: agreement.status = payload.agreementStatus
        if payload.agreementReference is not None: agreement.reference = payload.agreementReference.strip() or None
        if payload.effectiveAt is not None: agreement.effective_at = payload.effectiveAt
        if payload.expiresAt is not None: agreement.expires_at = payload.expiresAt
        if payload.notes is not None: agreement.notes = payload.notes.strip() or None
        agreement.updated_by_admin_id = admin.id
    db.flush()
    after = {"isActive": supplier.is_active, "agreement": _agreement_payload(agreement)}
    if before == after:
        db.rollback()
        raise HTTPException(status_code=422, detail="Aucune modification de gouvernance demandée")
    _audit(db, admin, supplier, before, after)
    db.commit()
    return {"supplierId": supplier.id, **after}


@router.get("/audit")
def governance_audit(
    employerId: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(require_superadmin),
):
    query = db.query(MarketplaceGovernanceEvent)
    if employerId is not None:
        query = query.filter(MarketplaceGovernanceEvent.employer_id == employerId)
    events = query.order_by(MarketplaceGovernanceEvent.id.desc()).limit(limit).all()
    return [{
        "id": x.id, "adminUserId": x.admin_user_id, "employerId": x.employer_id,
        "entityType": x.entity_type, "entityId": x.entity_id, "action": x.action,
        "payload": x.payload_json, "createdAt": x.created_at.isoformat() if x.created_at else None,
    } for x in events]
