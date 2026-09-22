"""Application service for F5 engineering-preview superimposition.

Routes remain disabled by default. Set DIGITAL_CROWN_F5_ENGINEERING_PREVIEW=1
only in an explicit engineering environment.
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
from sqlalchemy.orm import Session

from backend.services.cephalo_superimposition import (
    ImageROI,
    METHOD_ID,
    METHOD_VERSION,
    QUALITY_STATUS,
    RegistrationConfig,
    SuperimpositionError,
    register_acb_similarity,
)
from backend.services.cephalo_superimposition_source import (
    ResolvedSuperimpositionPair,
    SuperimpositionSourceError,
    resolve_superimposition_pair,
)


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_STATIC_ROOT = (_BACKEND_ROOT / "static").resolve()
_DB_STATIC_PREFIX = "api/static/"
_DB_RADIO_PREFIX = "api/static/uploads/radios/"


def engineering_preview_enabled() -> bool:
    runtime_environment = os.getenv("ENVIRONMENT", "").strip().lower()
    return (
        runtime_environment in {"development", "local", "test"}
        and os.getenv("DIGITAL_CROWN_F5_ENGINEERING_PREVIEW", "0") == "1"
    )


def _public_source(source) -> dict:
    return {
        "timepoint_id": source.timepoint_id,
        "timepoint_ordinal": source.timepoint_ordinal,
        "occurred_at": source.occurred_at,
        "cephalo_analysis_id": source.cephalo_analysis_id,
        "is_calibrated": source.is_calibrated,
        "mm_per_pixel": source.mm_per_pixel,
    }


def context_from_pair(pair: ResolvedSuperimpositionPair) -> dict:
    return {
        "patient_id": pair.patient_id,
        "ortho_case_id": pair.ortho_case_id,
        "from_source": _public_source(pair.from_source),
        "to_source": _public_source(pair.to_source),
        "quantitative_mm_allowed": pair.quantitative_mm_allowed,
        "applicability_status": pair.applicability_status,
        "acquisition_protocol_status": "UNVERIFIED",
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "quality_status": QUALITY_STATUS,
        "clinically_validated": False,
    }


def build_context(
    db: Session,
    *,
    patient_id: int,
    case_id: int,
    employer_id: int,
    from_timepoint_id: int,
    to_timepoint_id: int,
) -> dict:
    pair = resolve_superimposition_pair(
        db,
        patient_id=patient_id,
        case_id=case_id,
        employer_id=employer_id,
        from_timepoint_id=from_timepoint_id,
        to_timepoint_id=to_timepoint_id,
    )
    # Context is consumed by the browser before estimation. Validate both
    # source paths here so a forged/legacy external URL can never trigger
    # browser egress from the F5 viewer.
    _canonical_local_path(pair.from_source.image_original_path)
    _canonical_local_path(pair.to_source.image_original_path)
    return context_from_pair(pair)


def _canonical_local_path(db_path: str) -> Path:
    normalized = str(db_path or "").replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise SuperimpositionSourceError(
            "SOURCE_PATH_INVALID",
            "Canonical cephalogram path contains traversal segments.",
        )
    if not normalized.startswith(_DB_RADIO_PREFIX):
        raise SuperimpositionSourceError(
            "SOURCE_PATH_UNSUPPORTED",
            "F5 only reads canonical cephalograms stored under api/static/uploads/radios/.",
        )
    relative = normalized[len(_DB_STATIC_PREFIX):]
    candidate = (_STATIC_ROOT / relative).resolve()
    try:
        candidate.relative_to(_STATIC_ROOT)
    except ValueError as exc:
        raise SuperimpositionSourceError(
            "SOURCE_PATH_INVALID",
            "Canonical cephalogram path escapes the static media root.",
        ) from exc
    if not candidate.is_file():
        raise SuperimpositionSourceError(
            "SOURCE_FILE_MISSING",
            "Canonical cephalogram file is missing from local storage.",
        )
    return candidate


def _load_canonical_image(db_path: str):
    path = _canonical_local_path(db_path)
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SuperimpositionSourceError(
            "SOURCE_IMAGE_UNREADABLE",
            "Canonical cephalogram cannot be decoded.",
        )
    return image


def estimate_pair(
    db: Session,
    *,
    patient_id: int,
    case_id: int,
    employer_id: int,
    from_timepoint_id: int,
    to_timepoint_id: int,
    reference_roi: ImageROI,
    moving_roi: ImageROI,
    config: RegistrationConfig | None = None,
) -> dict:
    pair = resolve_superimposition_pair(
        db,
        patient_id=patient_id,
        case_id=case_id,
        employer_id=employer_id,
        from_timepoint_id=from_timepoint_id,
        to_timepoint_id=to_timepoint_id,
    )
    reference = _load_canonical_image(pair.from_source.image_original_path)
    moving = _load_canonical_image(pair.to_source.image_original_path)
    result = register_acb_similarity(
        reference,
        moving,
        reference_roi=reference_roi,
        moving_roi=moving_roi,
        config=config,
    )
    return {
        "context": context_from_pair(pair),
        "registration": result.to_metadata(),
    }
