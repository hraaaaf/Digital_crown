"""Invariant layer for Media Core ClinicalAsset creation/read access."""
from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Patient, User
from backend.models_media_core import (
    CLINICAL_ASSET_SOURCE_KINDS,
    CLINICAL_ASSET_TYPES,
    ClinicalAsset,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMEPOINT_RE = re.compile(r"^T(?:0|[1-9][0-9]{0,2})$")
_FORBIDDEN_PROVENANCE_KEYS = {
    "patient_name",
    "patient_email",
    "patient_phone",
    "email",
    "phone",
    "telephone",
    "nom",
    "prenom",
}


class ClinicalAssetInvariantError(ValueError):
    """Raised when a ClinicalAsset would violate a tenant/data-safety invariant."""


def _validate_display_filename(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > 255 or "\x00" in value or "/" in value or "\\" in value:
        raise ClinicalAssetInvariantError("original_filename must be display metadata, not a path")
    return value


def _contains_forbidden_provenance_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in _FORBIDDEN_PROVENANCE_KEYS:
                return True
            if _contains_forbidden_provenance_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_provenance_key(item) for item in value)
    return False


def _validate_provenance(value: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ClinicalAssetInvariantError("provenance_json must be an object")
    if _contains_forbidden_provenance_key(value):
        raise ClinicalAssetInvariantError("provenance_json must not duplicate patient-identifying fields")
    return value


def _validate_cabinet_user(db: Session, employer_id: int, user_id: Optional[int]) -> None:
    if user_id is None:
        return
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or int(user.get_employer_id()) != int(employer_id):
        raise ClinicalAssetInvariantError("created_by user does not belong to the asset tenant")


def _require_patient_in_tenant(db: Session, employer_id: int, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(
        Patient.id == int(patient_id),
        Patient.employer_id == int(employer_id),
    ).first()
    if patient is None:
        raise ClinicalAssetInvariantError("patient does not belong to the asset tenant")
    return patient


def create_clinical_asset(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    asset_type: str,
    source_kind: str,
    source_ref: Optional[str] = None,
    original_filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    byte_size: Optional[int] = None,
    sha256: Optional[str] = None,
    timepoint: Optional[str] = None,
    captured_at=None,
    created_by: Optional[int] = None,
    parent_asset_id: Optional[int] = None,
    provenance_json: Optional[dict[str, Any]] = None,
) -> ClinicalAsset:
    """Create a metadata-only asset after all C1 tenant/provenance guards pass.

    The caller owns the transaction. This function flushes to obtain the id but never commits.
    """
    employer_id = int(employer_id)
    patient_id = int(patient_id)
    asset_type = str(asset_type).upper()
    source_kind = str(source_kind).upper()

    if asset_type not in CLINICAL_ASSET_TYPES:
        raise ClinicalAssetInvariantError(f"unsupported asset_type: {asset_type}")
    if source_kind not in CLINICAL_ASSET_SOURCE_KINDS:
        raise ClinicalAssetInvariantError(f"unsupported source_kind: {source_kind}")

    _require_patient_in_tenant(db, employer_id, patient_id)
    _validate_cabinet_user(db, employer_id, created_by)

    if source_ref is not None:
        source_ref = source_ref.strip()
        if not source_ref:
            source_ref = None
        elif len(source_ref) > 255 or "\x00" in source_ref:
            raise ClinicalAssetInvariantError("source_ref is invalid")

    original_filename = _validate_display_filename(original_filename)

    if mime_type is not None:
        mime_type = mime_type.strip().lower()
        if not mime_type or len(mime_type) > 127 or "/" not in mime_type or "\x00" in mime_type:
            raise ClinicalAssetInvariantError("mime_type is invalid")

    if byte_size is not None:
        byte_size = int(byte_size)
        if byte_size < 0:
            raise ClinicalAssetInvariantError("byte_size cannot be negative")

    if sha256 is not None:
        sha256 = sha256.strip().lower()
        if not _SHA256_RE.fullmatch(sha256):
            raise ClinicalAssetInvariantError("sha256 must contain exactly 64 hexadecimal characters")

    if timepoint is not None:
        timepoint = timepoint.strip().upper()
        if not _TIMEPOINT_RE.fullmatch(timepoint):
            raise ClinicalAssetInvariantError("timepoint must be T0..T999")

    provenance_json = _validate_provenance(provenance_json)

    if parent_asset_id is not None:
        parent = db.query(ClinicalAsset).filter(
            ClinicalAsset.id == int(parent_asset_id),
            ClinicalAsset.employer_id == employer_id,
            ClinicalAsset.patient_id == patient_id,
        ).first()
        if parent is None:
            raise ClinicalAssetInvariantError("parent asset must belong to the same tenant and patient")

    asset = ClinicalAsset(
        employer_id=employer_id,
        patient_id=patient_id,
        asset_type=asset_type,
        source_kind=source_kind,
        source_ref=source_ref,
        original_filename=original_filename,
        mime_type=mime_type,
        byte_size=byte_size,
        sha256=sha256,
        timepoint=timepoint,
        captured_at=captured_at,
        created_by=created_by,
        parent_asset_id=parent_asset_id,
        provenance_json=provenance_json,
    )
    db.add(asset)
    db.flush()
    return asset


def get_clinical_asset_for_patient(
    db: Session, *, employer_id: int, patient_id: int, asset_id: int
) -> Optional[ClinicalAsset]:
    """Tenant + patient scoped read primitive for Media Core APIs."""
    return db.query(ClinicalAsset).filter(
        ClinicalAsset.id == int(asset_id),
        ClinicalAsset.employer_id == int(employer_id),
        ClinicalAsset.patient_id == int(patient_id),
    ).first()


def list_clinical_assets_for_patient(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    include_derived: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> list[ClinicalAsset]:
    """Return a bounded tenant-scoped timeline slice for one patient.

    C4 hides DERIVED assets by default so thumbnails never appear as independent clinical
    events. Only assets with a complete C2 storage binding are timeline-visible. Ordering uses
    acquisition time when available, then creation time, newest first.
    """
    employer_id = int(employer_id)
    patient_id = int(patient_id)
    _require_patient_in_tenant(db, employer_id, patient_id)

    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    query = db.query(ClinicalAsset).filter(
        ClinicalAsset.employer_id == employer_id,
        ClinicalAsset.patient_id == patient_id,
        ClinicalAsset.storage_key.isnot(None),
        ClinicalAsset.storage_format.isnot(None),
        ClinicalAsset.stored_at.isnot(None),
        ClinicalAsset.sha256.isnot(None),
        ClinicalAsset.byte_size.isnot(None),
    )
    if not include_derived:
        query = query.filter(ClinicalAsset.source_kind != "DERIVED")

    return (
        query.order_by(
            func.coalesce(ClinicalAsset.captured_at, ClinicalAsset.created_at).desc(),
            ClinicalAsset.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
