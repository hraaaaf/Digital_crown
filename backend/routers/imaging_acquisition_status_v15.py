"""LOT06 Phase2 B01: product-facing read-only boundary, NOT device ingress.

This cannot enumerate captures, grant patient association, transfer media
or issue a receipt. Native Win32 SCM/SID/IPC and hardware TPM remain OPEN.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend import database, models
from backend.routers.auth import require_permission
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected, resolve_acquisition_preflight,
)
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Imaging acquisition — disabled product boundary"])


@router.get("/{patient_id}/acquisition/status")
def get_product_acquisition_status(
    patient_id: int,
    response: Response,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Authenticated patient-scoped GET; no writable device operation exists."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    assert_patient_access(patient_id, current_user, db)
    try:
        decision = resolve_acquisition_preflight(
            db, employer_id=int(current_user.get_employer_id()), patient_id=patient_id,
        )
    except PreflightRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    if decision.patient_id != patient_id or decision.status != "STAFF_CONFIRMATION_REQUIRED":
        raise HTTPException(status_code=409, detail="ACQUISITION_PATIENT_CONTEXT_UNAVAILABLE")
    # Never infer device readiness from a frontend flag, LAB HTTP response,
    # patient dossier, filename, appointment or a software key provider.
    return {
        "schema_version": "dc06-product-status-v1",
        "state": "NATIVE_IPC_NOT_CONNECTED",
        "read_only": True,
        "acquisition_enabled": False,
        "clinical_receipt_authorized": False,
        "pending_captures": None,
        "reason": "WINDOWS_IPC_AND_TPM_PRODUCT_GATE_NOT_VERIFIED",
    }
