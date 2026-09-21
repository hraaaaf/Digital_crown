from __future__ import annotations

import base64
import binascii
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models_patient_companion import PatientCompanionAccess
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError,
    ingest_clinical_asset_bytes,
)
from backend.services.clinical_asset_service import ClinicalAssetInvariantError
from backend.services.clinical_asset_storage import ClinicalAssetStorageError
from backend.services.clinical_photo_normalization import (
    CLINICAL_PHOTO_MAX_BYTES,
    normalize_clinical_photo,
)
from backend.services.patient_companion_remote_worker import RemoteDomainResult


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def _captured_at(raw) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed


def submit_emergency_photo(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict,
) -> RemoteDomainResult:
    allowed = {"image_b64", "captured_at"}
    if not isinstance(payload, dict) or "image_b64" not in payload or set(payload) - allowed:
        return _reject("INVALID_REQUEST")

    encoded = payload.get("image_b64")
    if not isinstance(encoded, str) or not encoded:
        return _reject("INVALID_REQUEST")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return _reject("INVALID_IMAGE_ENCODING")
    if not raw or len(raw) > CLINICAL_PHOTO_MAX_BYTES:
        return _reject("IMAGE_TOO_LARGE")

    captured_at = _captured_at(payload.get("captured_at"))
    if payload.get("captured_at") not in (None, "") and captured_at is None:
        return _reject("INVALID_CAPTURED_AT")

    try:
        normalized = normalize_clinical_photo(raw)
        result = ingest_clinical_asset_bytes(
            db,
            employer_id=int(access.employer_id),
            patient_id=int(access.patient_id),
            asset_type="PHOTO",
            source_kind="DEVICE_CAPTURE",
            content=normalized,
            original_filename=f"patient-emergency-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.jpg",
            claimed_mime_type="image/jpeg",
            source_ref="PATIENT_COMPANION_EMERGENCY_PHOTO",
            captured_at=captured_at,
            created_by=None,
            provenance_json={
                "ingestion_channel": "PATIENT_COMPANION",
                "capture_kind": "EMERGENCY_PHOTO",
                "access_public_id": str(access.public_id),
            },
        )
    except HTTPException as exc:
        if exc.status_code == 413:
            return _reject("IMAGE_TOO_LARGE")
        return _reject("INVALID_IMAGE")
    except (ClinicalAssetIngestionError, ClinicalAssetInvariantError):
        return _reject("INVALID_IMAGE")
    except (ClinicalAssetStorageError, OSError):
        return _reject("STORAGE_UNAVAILABLE")

    db.flush()
    received_at = datetime.utcnow()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "asset_id": int(result.asset.id),
            "state": "received",
            "received_at": received_at.isoformat(),
        },
    )


PC07_REMOTE_HANDLERS = {
    "emergency_photo.submit": submit_emergency_photo,
}
