from __future__ import annotations

from datetime import datetime
from typing import Final

from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset


ORTHO_MEDIA_SCHEMA_VERSION: Final = "ORTHO_MEDIA_RECORD_V1"
ORTHO_PHOTO_SOURCE_PREFIX: Final = "ORTHO_PHOTO_V1:"
ORTHO_TIMEPOINTS: Final = ("T0", "T1", "T2", "T3", "OTHER")
ORTHO_PHOTO_SLOTS: Final = (
    "EXTRA_FRONTAL_REPOSE",
    "EXTRA_PROFILE",
    "EXTRA_SMILE",
    "INTRA_FRONTAL",
    "INTRA_RIGHT",
    "INTRA_LEFT",
    "INTRA_OCCLUSAL_MAXILLARY",
    "INTRA_OCCLUSAL_MANDIBULAR",
)
ORTHO_MODEL_HOOKS: Final = (
    {"hook_id": "MAXILLARY_ARCH", "accepted_formats": ["STL", "PLY", "OBJ"]},
    {"hook_id": "MANDIBULAR_ARCH", "accepted_formats": ["STL", "PLY", "OBJ"]},
    {"hook_id": "OCCLUSION_RELATION", "accepted_formats": ["STL", "PLY", "OBJ"]},
)


class OrthoMediaRecordError(ValueError):
    pass


def validate_ortho_timepoint(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in ORTHO_TIMEPOINTS:
        raise OrthoMediaRecordError("Unsupported orthodontic timepoint")
    return normalized


def validate_ortho_photo_slot(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in ORTHO_PHOTO_SLOTS:
        raise OrthoMediaRecordError("Unsupported orthodontic photo slot")
    return normalized


def ortho_photo_source_ref(slot: str) -> str:
    return f"{ORTHO_PHOTO_SOURCE_PREFIX}{validate_ortho_photo_slot(slot)}"


def _has_canonical_ortho_provenance(asset: ClinicalAsset, *, slot: str, patient_id: int, timepoint: str) -> bool:
    provenance = asset.provenance_json if isinstance(asset.provenance_json, dict) else {}
    return (
        asset.source_kind == "UPLOAD"
        and asset.created_by is not None
        and provenance.get("schema_version") == ORTHO_MEDIA_SCHEMA_VERSION
        and provenance.get("slot_id") == slot
        and provenance.get("source_type") == "CLINICIAN_UPLOAD"
        and bool(provenance.get("acquired_at"))
        and provenance.get("operator_or_device") == f"user:{asset.created_by}"
        and provenance.get("patient_record_id") == str(patient_id)
        and provenance.get("timepoint_id") == timepoint
        and asset.captured_at is not None
    )


def _serialize(asset: ClinicalAsset, slot: str) -> dict:
    return {
        "slot_id": slot,
        "asset_id": int(asset.id),
        "mime_type": asset.mime_type,
        "captured_at": asset.captured_at,
        "created_at": asset.created_at,
        "source_kind": asset.source_kind,
        "timepoint": asset.timepoint,
    }


def build_ortho_media_record(
    db: Session, *, employer_id: int, patient_id: int, timepoint: str
) -> dict:
    timepoint = validate_ortho_timepoint(timepoint)
    rows = (
        db.query(ClinicalAsset)
        .filter(
            ClinicalAsset.employer_id == employer_id,
            ClinicalAsset.patient_id == patient_id,
            ClinicalAsset.asset_type == "PHOTO",
            ClinicalAsset.source_kind != "DERIVED",
            ClinicalAsset.timepoint == timepoint,
            ClinicalAsset.source_ref.like(f"{ORTHO_PHOTO_SOURCE_PREFIX}%"),
            ClinicalAsset.storage_key.isnot(None),
            ClinicalAsset.storage_format.isnot(None),
            ClinicalAsset.stored_at.isnot(None),
            ClinicalAsset.sha256.isnot(None),
            ClinicalAsset.byte_size.isnot(None),
        )
        .order_by(ClinicalAsset.created_at.desc(), ClinicalAsset.id.desc())
        .all()
    )
    latest: dict[str, ClinicalAsset] = {}
    for asset in rows:
        ref = str(asset.source_ref or "")
        slot = ref[len(ORTHO_PHOTO_SOURCE_PREFIX):] if ref.startswith(ORTHO_PHOTO_SOURCE_PREFIX) else ""
        if (
            slot in ORTHO_PHOTO_SLOTS
            and slot not in latest
            and _has_canonical_ortho_provenance(
                asset, slot=slot, patient_id=patient_id, timepoint=timepoint
            )
        ):
            latest[slot] = asset

    photos = [
        {"slot_id": slot, "state": "FILLED", "asset": _serialize(latest[slot], slot)}
        if slot in latest
        else {"slot_id": slot, "state": "EMPTY", "asset": None}
        for slot in ORTHO_PHOTO_SLOTS
    ]
    return {
        "schema_version": ORTHO_MEDIA_SCHEMA_VERSION,
        "patient_id": patient_id,
        "timepoint": timepoint,
        "photo_slots": photos,
        "photo_complete": len(latest) == len(ORTHO_PHOTO_SLOTS),
        "model_hooks": [
            {**hook, "state": "VALIDATOR_NOT_IMPLEMENTED", "measurement_authority": "NONE"}
            for hook in ORTHO_MODEL_HOOKS
        ],
    }
