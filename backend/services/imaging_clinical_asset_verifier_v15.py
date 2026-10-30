"""LOT06-C05B-02A: read-only ClinicalAsset/AES-GCM receipt precondition.

This module does NOT authorize staff/devices, create an approval or receipt,
change a persistent database, or enable the guarded imaging LAB service.
A future server-side PostgreSQL authority must bind the result to its own
immutable approval/version and transaction before declaring any clinical ACK.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

from sqlalchemy.orm import Session

from backend.models_media_core import CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1
from backend.services.clinical_asset_service import get_clinical_asset_for_patient
from backend.services.clinical_asset_storage import (
    ClinicalAssetStorageError,
    read_clinical_asset_bytes,
)


class MediaBindingRejected(ValueError):
    """Fail-closed non-PHI internal reason for a clinical media prerequisite."""


@dataclass(frozen=True)
class VerifiedCaptureMedia:
    tenant: int
    patient: int
    asset_id: int
    staff_id: int
    digest: str
    byte_size: int
    # Deliberately not a clinical receipt, a permission grant or an approval.
    clinical_receipt_authorized: bool = False


def verify_device_capture_media_binding(
    db: Session, *, tenant: int, patient: int, asset_id: int,
    staff_id: int, digest: str, byte_size: int,
    media_root: Path | None = None,
) -> VerifiedCaptureMedia:
    """Read actual encrypted ClinicalAsset and verify all claimed media identity.

    No approval-version logic is implemented here: the future server-owned
    approval ledger must verify its own immutability and authorization.
    """
    if (
        any(not isinstance(v, int) or isinstance(v, bool) or v <= 0
            for v in (tenant, patient, asset_id, staff_id, byte_size))
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise MediaBindingRejected("MEDIA_BINDING_INVALID_CLAIM")

    asset = get_clinical_asset_for_patient(
        db, employer_id=tenant, patient_id=patient, asset_id=asset_id,
    )
    if (
        asset is None
        or asset.source_kind != "DEVICE_CAPTURE"
        or asset.asset_type not in ("PHOTO", "RADIOGRAPH")
        or asset.created_by != staff_id
        or asset.sha256 != digest
        or asset.byte_size != byte_size
        or asset.storage_format != CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1
        or not asset.storage_key
        or asset.stored_at is None
    ):
        raise MediaBindingRejected("MEDIA_BINDING_CONFLICT")

    try:
        plaintext = read_clinical_asset_bytes(
            db, employer_id=tenant, patient_id=patient,
            asset_id=asset_id, media_root=media_root,
        )
    except ClinicalAssetStorageError as exc:
        raise MediaBindingRejected("MEDIA_INTEGRITY_BLOCKED") from exc
    if len(plaintext) != byte_size or hashlib.sha256(plaintext).hexdigest() != digest:
        raise MediaBindingRejected("MEDIA_INTEGRITY_BLOCKED")

    return VerifiedCaptureMedia(
        tenant=tenant, patient=patient, asset_id=asset_id, staff_id=staff_id,
        digest=digest, byte_size=byte_size,
    )
