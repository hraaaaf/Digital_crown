"""LOT06-C05B-02B: isolated LAB server-owned approval + AES media evidence.

Read-only cross-check of existing staff/device approval against the verified
ClinicalAsset. NOT a product authorization, not wired to PostgreSQL receipts.
It only operates under the existing test-only in-memory transfer guard.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend import models
from backend.routers.auth import has_permission
from backend.services import imaging_acquisition_transfer_lab_v15 as lab
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected, resolve_acquisition_preflight,
)
from backend.services.clinical_asset_service import get_clinical_asset_for_patient
from backend.services.imaging_clinical_asset_verifier_v15 import (
    MediaBindingRejected, VerifiedCaptureMedia,
    verify_device_capture_media_binding,
)


class CaptureAuthorityRejected(ValueError):
    """Only a test-LAB non-PHI reason, never a clinical approval."""


def verify_lab_approved_capture_and_media(
    db: Session, *, tenant: int, device: str, token: str, capture: str,
    patient: int, staff_id: int, workstation_id: str,
    appointment: int | None, reason: str | None,
    asset_id: int, digest: str, byte_size: int,
    media_root: Path | None = None,
) -> VerifiedCaptureMedia:
    """Fail closed if LAB device/staff/station/approval/media disagree.

    No trust from caller-provided staff_id, patient, device or digest: all are
    cross-checked with already-approved server-owned LAB capture rows and
    current staff/workstation/patient records, then actual AES-GCM readback.
    This *does not* issue or approve a receipt or certify production identity.
    """
    lab.guard(db)
    try:
        lab._device(db, tenant=tenant, device=device, token=token)
    except lab.TransferLabRejected as exc:
        raise CaptureAuthorityRejected("LAB_DEVICE_AUTH_FAILED") from exc

    where = (
        (lab.captures.c.tenant == tenant)
        & (lab.captures.c.device == device)
        & (lab.captures.c.capture == capture)
    )
    row = db.execute(select(lab.captures).where(where)).mappings().first()
    if (
        row is None
        or row["staff"] is None
        or row["patient"] != patient
        or row["staff"] != staff_id
        or row["workstation"] != workstation_id
        or row["appointment"] != appointment
        or row["patient_only_reason"] != reason
        or row["digest"] != digest
        or row["size"] != byte_size
    ):
        raise CaptureAuthorityRejected("LAB_APPROVED_CAPTURE_BINDING_MISMATCH")

    staff = db.query(models.User).filter(
        models.User.id == staff_id, models.User.is_active.is_(True),
    ).first()
    if (
        staff is None or int(staff.get_employer_id()) != tenant
        or not has_permission(staff, "patients")
    ):
        raise CaptureAuthorityRejected("LAB_STAFF_NOT_AUTHORIZED")
    station = db.query(models.WorkstationMode).filter(
        models.WorkstationMode.id == workstation_id,
        models.WorkstationMode.employer_id == tenant,
        models.WorkstationMode.revoked_at.is_(None),
    ).first()
    if station is None:
        raise CaptureAuthorityRejected("LAB_WORKSTATION_REVOKED")
    try:
        lab._reason(appointment, reason)
        resolution = resolve_acquisition_preflight(
            db, employer_id=tenant, patient_id=patient,
            appointment_id=appointment,
        )
    except (lab.TransferLabRejected, PreflightRejected) as exc:
        raise CaptureAuthorityRejected("LAB_PATIENT_REVIEW_STALE") from exc
    if (
        resolution.status != "STAFF_CONFIRMATION_REQUIRED"
        or resolution.patient_id != patient
        or resolution.appointment_id != appointment
    ):
        raise CaptureAuthorityRejected("LAB_PATIENT_REVIEW_STALE")

    asset = get_clinical_asset_for_patient(
        db, employer_id=tenant, patient_id=patient, asset_id=asset_id,
    )
    provenance = asset.provenance_json if asset is not None else None
    if (
        not isinstance(provenance, dict)
        or provenance.get("ingestion_channel") != "LOT06B_LAB_ONLY"
        or provenance.get("capture_id") != capture
        or provenance.get("device_proof") != "ISOLATED_FIXTURE_TOKEN"
    ):
        raise CaptureAuthorityRejected("LAB_CAPTURE_ASSET_PROVENANCE_MISMATCH")
    try:
        proof = verify_device_capture_media_binding(
            db, tenant=tenant, patient=patient, asset_id=asset_id,
            staff_id=staff_id, digest=digest, byte_size=byte_size,
            media_root=media_root,
        )
    except MediaBindingRejected as exc:
        raise CaptureAuthorityRejected("LAB_ENCRYPTED_MEDIA_INTEGRITY_BLOCKED") from exc
    assert proof.clinical_receipt_authorized is False
    return proof
