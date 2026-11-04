"""LOT06 B06-1 product route: authenticated read-only unassigned inventory.

This is NOT a clinical capture/preview/upload/confirm endpoint. The trusted
Windows provider is intentionally absent on startup; never take pipe names,
patient identities or device keys from an HTTP caller.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from backend.services.imaging_acquisition_durable_v15 import (
    DurableCaptureDenied, commit_capture, receipt_for, is_committed,
)
from backend.routers.auth import has_permission
from backend.services.imaging_acquisition_product_review_v15 import (
    ProductReviewStore, ProductReviewDenied,
)
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected, resolve_acquisition_preflight,
)
from backend.utils.access_control import assert_patient_access
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.routers.workstation_mode import _find_workstation
from backend.services.imaging_acquisition_native_bridge_v15 import LocalNativeCaptureBridge
from tools.imaging_gateway.native_inventory_protocol_v15 import NativeInventoryDenied

router = APIRouter(tags=["Imaging acquisition — unassigned inventory"])


@router.get("/unassigned")
def get_unassigned_capture_inventory(
    request: Request,
    response: Response,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    """Staff-only inventory, explicitly UNASSIGNED; never leaks raw media."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    if (request.client is None or request.client.host not in ("127.0.0.1", "::1")
            or not staff.is_active or staff.is_archived or staff.is_suspended
            or staff.approval_status != "approved"):
        raise HTTPException(403, "NATIVE_CAPTURE_LOCAL_STAFF_ONLY")
    tenant = int(staff.get_employer_id())
    workstation = _find_workstation(request, db, employer_id=tenant)
    if workstation is None or workstation.default_experience == "station":
        raise HTTPException(423, "NATIVE_CAPTURE_WORKSTATION_REQUIRED")

    bridge = getattr(request.app.state, "dc06_unassigned_bridge", None)
    if not isinstance(bridge, LocalNativeCaptureBridge):
        return {
            "schema_version": "dc06-product-unassigned-v1",
            "state": "NATIVE_IPC_NOT_CONNECTED",
            "read_only": True, "clinical_receipt_authorized": False,
            "patient_assigned": False, "captures": [],
        }
    try:
        capture = bridge.inventory(
            tenant_id=tenant, workstation_id=workstation.id,
        )
    except NativeInventoryDenied:
        # Never misrepresent an unreadable/refused service as an empty queue.
        raise HTTPException(503, "NATIVE_CAPTURE_INVENTORY_UNAVAILABLE") from None
    return {
        "schema_version": "dc06-product-unassigned-v1",
        "state": "UNASSIGNED_INVENTORY_READ_ONLY",
        "read_only": True, "clinical_receipt_authorized": False,
        "patient_assigned": False,
        "captures": [] if capture is None else [{
            "id": capture.id, "digest": capture.digest, "size": capture.size,
            "mime": capture.mime, "category": capture.category,
        }],
    }


# Product review is deliberately transient and does not write ClinicalAsset,
# approval, receipt or patient binding. Durable workflow begins only in B06-3.
class StartReview(BaseModel):
    capture_id: int = Field(ge=1)
    capture_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_patient_id: int = Field(ge=1)


class ConfirmReview(BaseModel):
    challenge: str = Field(min_length=16, max_length=128)
    selected_patient_id: int = Field(ge=1)
    dossier: str = Field(min_length=1, max_length=20)
    date_naissance: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    capture_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    explicit_confirmation: bool


def _review_context(request: Request, db: Session, staff: models.User):
    # Same-machine only; never trust client-controlled X-Forwarded-For or pipe
    # selection. Stateful requests require an actual bearer token, not a
    # cookie-only request susceptible to CSRF.
    if (request.client is None or request.client.host not in ("127.0.0.1", "::1")
            or request.headers.get("sec-fetch-site", "same-origin") == "cross-site"
            or not staff.is_active or staff.is_archived or staff.is_suspended
            or staff.approval_status != "approved"):
        raise HTTPException(403, "REVIEW_LOCAL_STAFF_REQUIRED")
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer ") or len(auth) <= 20:
        raise HTTPException(403, "REVIEW_BEARER_SESSION_REQUIRED")
    raw = auth[7:]
    if request.cookies.get("access_token") not in (None, raw):
        raise HTTPException(403, "REVIEW_SESSION_TOKEN_CONFLICT")
    tenant = int(staff.get_employer_id())
    station = _find_workstation(request, db, employer_id=tenant)
    if station is None or station.default_experience == "station":
        raise HTTPException(423, "REVIEW_WORKSTATION_REQUIRED")
    bridge = getattr(request.app.state, "dc06_unassigned_bridge", None)
    store = getattr(request.app.state, "dc06_review_store", None)
    if not isinstance(bridge, LocalNativeCaptureBridge) or not isinstance(store, ProductReviewStore):
        raise HTTPException(503, "REVIEW_NATIVE_BRIDGE_UNAVAILABLE")
    return tenant, station.id, raw, bridge, store


def _selected_patient(db: Session, *, patient_id: int,
                      tenant: int, staff: models.User):
    assert_patient_access(patient_id, staff, db)
    try:
        preflight = resolve_acquisition_preflight(
            db, employer_id=tenant, patient_id=patient_id,
        )
    except PreflightRejected:
        raise HTTPException(409, "REVIEW_PATIENT_PREFLIGHT_DENIED") from None
    if preflight.patient_id != patient_id or preflight.status != "STAFF_CONFIRMATION_REQUIRED":
        raise HTTPException(409, "REVIEW_PATIENT_NOT_SELECTABLE")
    patient = db.get(models.Patient, patient_id)
    if (patient is None or patient.employer_id != tenant
            or patient.deleted_at is not None or not patient.numero_dossier
            or patient.date_naissance is None):
        raise HTTPException(409, "REVIEW_TWO_IDENTIFIERS_REQUIRED")
    return patient


def _review_candidate(store: ProductReviewStore, *, review_id: str, challenge: str,
                      tenant: int, station: str, staff: int, session: str):
    try:
        return store.require(
            review_id=review_id, challenge=challenge,
            tenant=tenant, workstation=station,
            staff=staff, session=session,
        )
    except ProductReviewDenied:
        raise HTTPException(409, "REVIEW_CHALLENGE_NOT_ACTIVE") from None


@router.post("/review")
def start_product_review(
    request: Request, data: StartReview, response: Response,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    response.headers["Cache-Control"] = "no-store"
    tenant, station, session, bridge, store = _review_context(request, db, staff)
    patient = _selected_patient(
        db, patient_id=data.selected_patient_id, tenant=tenant, staff=staff,
    )
    try:
        capture = bridge.inventory(tenant_id=tenant, workstation_id=station)
        if (capture is None or capture.id != data.capture_id
                or capture.digest != data.capture_digest
                or capture.mime != "image/png"):
            raise HTTPException(409, "REVIEW_CAPTURE_NOT_AVAILABLE")
        # Read AND validate the exact binary server-side before granting a
        # preview capability. No bytes are sent to the client at this stage.
        bridge.read_verified_media(capture, tenant_id=tenant, workstation_id=station)
        review, challenge = store.start(
            tenant=tenant, workstation=station, staff=staff.id,
            session=session, capture=capture, patient=patient.id,
        )
    except NativeInventoryDenied:
        raise HTTPException(503, "REVIEW_NATIVE_CAPTURE_DENIED") from None
    except ProductReviewDenied:
        raise HTTPException(409, "REVIEW_CAPTURE_ALREADY_CLAIMED") from None
    return {
        "schema_version": "dc06-product-review-v1",
        "status": "STAFF_REVIEW_REQUIRED",
        "clinical_receipt_authorized": False,
        "capture_id": capture.id,
        "capture_digest": capture.digest,
        "capture_size": capture.size,
        "challenge": challenge,
        "review_id": review.review_id,
        "expires_at": review.expires_at,
        "patient_id": patient.id, "nom": patient.nom,
        "prenom": patient.prenom,
        "numero_dossier": patient.numero_dossier,
        "date_naissance": patient.date_naissance.date().isoformat(),
        "preview_url": "/imaging/acquisition/review/" + review.review_id + "/preview",
    }


@router.get("/review/{review_id}/preview")
def preview_product_review(
    request: Request, review_id: str, response: Response,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    tenant, station, session, bridge, store = _review_context(request, db, staff)
    review = _review_candidate(
        store, review_id=review_id,
        challenge=request.headers.get("x-dc-review-challenge", ""),
        tenant=tenant, station=station, staff=staff.id, session=session,
    )
    _selected_patient(db, patient_id=review.patient, tenant=tenant, staff=staff)
    try:
        media = bridge.read_verified_media(
            review.capture, tenant_id=tenant, workstation_id=station,
        )
    except NativeInventoryDenied:
        raise HTTPException(409, "REVIEW_PREVIEW_MEDIA_CHANGED") from None
    # Invalidate a race where the lease expired while the bytes were read.
    _review_candidate(
        store, review_id=review_id,
        challenge=request.headers.get("x-dc-review-challenge", ""),
        tenant=tenant, station=station, staff=staff.id, session=session,
    )
    return Response(content=media, media_type="image/png", headers={
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox",
    })


@router.post("/review/{review_id}/confirm")
def confirm_product_review(
    request: Request, review_id: str, data: ConfirmReview,
    response: Response,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    response.headers["Cache-Control"] = "no-store"
    tenant, station, session, bridge, store = _review_context(request, db, staff)
    review = _review_candidate(
        store, review_id=review_id, challenge=data.challenge,
        tenant=tenant, station=station, staff=staff.id, session=session,
    )
    patient = _selected_patient(
        db, patient_id=review.patient, tenant=tenant, staff=staff,
    )
    if (data.explicit_confirmation is not True
            or data.selected_patient_id != review.patient
            or data.capture_digest != review.capture.digest
            or data.dossier != patient.numero_dossier
            or data.date_naissance != patient.date_naissance.date().isoformat()):
        raise HTTPException(409, "REVIEW_TWO_IDENTIFIERS_MISMATCH")
    try:
        bridge.read_verified_media(
            review.capture, tenant_id=tenant, workstation_id=station,
        )
    except NativeInventoryDenied:
        raise HTTPException(409, "REVIEW_MEDIA_CHANGED") from None
    try:
        store.consume(
            review_id=review_id, tenant=tenant, workstation=station,
            staff=staff.id, session=session, challenge=data.challenge,
        )
    except ProductReviewDenied:
        raise HTTPException(409, "REVIEW_REPLAY_DENIED") from None
    # B06-2 cannot persist an approval or create a receipt. B06-3 must
    # re-validate a fresh explicit staff decision inside a durable transaction.
    return {
        "status": "STAFF_REVIEW_VERIFIED_TRANSIENT_ONLY",
        "clinical_receipt_authorized": False,
        "patient_assigned": False,
        "media_published": False,
    }


@router.delete("/review/{review_id}")
def cancel_product_review(
    request: Request, review_id: str,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    tenant, station, session, _bridge, store = _review_context(request, db, staff)
    try:
        store.cancel(
            review_id=review_id, tenant=tenant, workstation=station,
            staff=staff.id, session=session,
            challenge=request.headers.get("x-dc-review-challenge", ""),
        )
    except ProductReviewDenied:
        raise HTTPException(409, "REVIEW_CANCELLATION_DENIED") from None
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


# B06-3 candidate is disabled on the real product until the additive SQLCipher
# schema and cabinet-side trust/bootstrap contract receive explicit approval.
# No DDL/migration occurs in HTTP handlers or normal startup.
@router.post("/review/{review_id}/commit")
def commit_product_media(
    request: Request, review_id: str, data: ConfirmReview,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    tenant, station, session, bridge, store = _review_context(request, db, staff)
    if getattr(request.app.state, "dc06_b06_durable_enabled", False) is not True:
        raise HTTPException(503, "DURABLE_SCHEMA_APPROVAL_REQUIRED")
    root = getattr(request.app.state, "dc06_b06_media_root", None)
    if root is not None:
        from pathlib import Path
        root = Path(root)
    # Unlike transient B06-2 confirmation, keep the challenge lease locked
    # across the complete SQLCipher commit. Cancellation cannot race a write.
    try:
        with store.durable_attempt(
            review_id=review_id, tenant=tenant, workstation=station,
            staff=staff.id, session=session, challenge=data.challenge,
        ) as review:
            patient = _selected_patient(
                db, patient_id=review.patient, tenant=tenant, staff=staff,
            )
            if (data.explicit_confirmation is not True
                    or data.selected_patient_id != review.patient
                    or data.capture_digest != review.capture.digest
                    or data.dossier != patient.numero_dossier
                    or data.date_naissance != patient.date_naissance.date().isoformat()):
                raise HTTPException(409, "DURABLE_TWO_IDENTIFIERS_MISMATCH")
            try:
                media = bridge.read_verified_media(
                    review.capture, tenant_id=tenant, workstation_id=station,
                )
            except NativeInventoryDenied:
                raise HTTPException(409, "DURABLE_NATIVE_CAPTURE_CHANGED") from None

            def locked_authority(writer: Session):
                current_staff = writer.get(models.User, staff.id)
                if (current_staff is None or current_staff.get_employer_id() != tenant
                        or not current_staff.is_active or current_staff.is_archived
                        or current_staff.is_suspended
                        or current_staff.approval_status != "approved"
                        or not has_permission(current_staff, "patients")):
                    raise DurableCaptureDenied("DURABLE_STAFF_REVOKED")
                current_station = _find_workstation(request, writer, employer_id=tenant)
                if (current_station is None or current_station.id != station
                        or current_station.default_experience == "station"):
                    raise DurableCaptureDenied("DURABLE_STATION_REVOKED")
                current_patient = _selected_patient(
                    writer, patient_id=review.patient, tenant=tenant,
                    staff=current_staff,
                )
                if (data.dossier != current_patient.numero_dossier
                        or data.date_naissance != current_patient.date_naissance.date().isoformat()):
                    raise DurableCaptureDenied("DURABLE_PATIENT_MARKERS_CHANGED")

            fail_at = None
            if (getattr(request.app.state, "dc06_b06_lab_failpoint", None)
                    and __import__("os").environ.get("ENVIRONMENT") == "test"
                    and __import__("os").environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"):
                fail_at = request.app.state.dc06_b06_lab_failpoint
            result = commit_capture(
                db.get_bind(), tenant=tenant, station=station,
                capture=review.capture.id, patient=review.patient,
                staff=staff.id, digest=review.capture.digest, media=media,
                category=review.capture.category,
                validate_locked=locked_authority, media_root=root,
                fail_at=fail_at,
            )
        return Response(
            content=__import__("json").dumps(result), media_type="application/json",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
    except ProductReviewDenied:
        raise HTTPException(409, "DURABLE_REVIEW_CHALLENGE_DENIED") from None
    except DurableCaptureDenied:
        raise HTTPException(503, "DURABLE_CAPTURE_NOT_COMMITTED") from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "DURABLE_COMMIT_UNAVAILABLE") from None


@router.get("/receipts/{capture_id}")
def recover_product_media_ack(
    request: Request, capture_id: int, selected_patient_id: int,
    capture_digest: str, db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    tenant, station, _session, _bridge, _store = _review_context(request, db, staff)
    if getattr(request.app.state, "dc06_b06_durable_enabled", False) is not True:
        raise HTTPException(503, "DURABLE_SCHEMA_APPROVAL_REQUIRED")
    if (capture_id < 1 or not __import__("re").fullmatch(r"[a-f0-9]{64}", capture_digest)):
        raise HTTPException(422, "DURABLE_RECEIPT_ARGUMENTS_DENIED")
    _selected_patient(db, patient_id=selected_patient_id, tenant=tenant, staff=staff)
    root = getattr(request.app.state, "dc06_b06_media_root", None)
    try:
        receipt = receipt_for(
            db.get_bind(), tenant=tenant, station=station,
            capture=capture_id, patient=selected_patient_id,
            staff=staff.id, digest=capture_digest, media_root=root,
        )
    except DurableCaptureDenied:
        raise HTTPException(409, "DURABLE_RECEIPT_NOT_VERIFIED") from None
    except Exception:
        raise HTTPException(503, "DURABLE_RECEIPT_UNAVAILABLE") from None
    return Response(
        content=__import__("json").dumps(receipt), media_type="application/json",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
