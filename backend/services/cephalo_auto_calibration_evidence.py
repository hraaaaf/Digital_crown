"""Materialize verified automatic calibration as typed SourceEvidence.

This adapter accepts only a decision that has already passed the objective
AUTO_VERIFIED gate. Candidate-only geometry cannot become scientific calibration
through this module.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Mapping

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    SourceEvidence,
)
from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationDecision,
    AutoCalibrationState,
)


class AutoCalibrationEvidenceError(ValueError):
    """Raised when automatic calibration provenance is incomplete or forged."""


def _required_text(provenance: Mapping[str, Any], key: str) -> str:
    value = provenance.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AutoCalibrationEvidenceError(f"{key} is required for AUTO_VERIFIED provenance")
    return value.strip()


def _required_number(provenance: Mapping[str, Any], key: str) -> float:
    value = provenance.get(key)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise AutoCalibrationEvidenceError(f"{key} must be numeric") from exc
    if not math.isfinite(number):
        raise AutoCalibrationEvidenceError(f"{key} must be finite")
    return number


def _required_positive_number(provenance: Mapping[str, Any], key: str) -> float:
    number = _required_number(provenance, key)
    if number <= 0:
        raise AutoCalibrationEvidenceError(f"{key} must be positive")
    return number


def source_evidence_from_auto_decision(
    *,
    patient_id: int,
    case_id: str,
    image_record_id: str,
    decision: AutoCalibrationDecision,
    recorded_at: dt.datetime,
) -> SourceEvidence:
    """Create typed calibration evidence from an objective AUTO_VERIFIED decision."""
    if decision.state is not AutoCalibrationState.AUTO_VERIFIED:
        raise AutoCalibrationEvidenceError("only AUTO_VERIFIED decisions may create calibration evidence")
    if decision.mm_per_pixel is None or not math.isfinite(decision.mm_per_pixel) or decision.mm_per_pixel <= 0:
        raise AutoCalibrationEvidenceError("AUTO_VERIFIED decision requires a positive finite mm_per_pixel")
    if not isinstance(decision.provenance, Mapping):
        raise AutoCalibrationEvidenceError("AUTO_VERIFIED decision requires structured provenance")
    if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        raise AutoCalibrationEvidenceError("recorded_at must be timezone-aware")
    if not isinstance(case_id, str) or not case_id.strip():
        raise AutoCalibrationEvidenceError("case_id is required")
    if not isinstance(image_record_id, str) or not image_record_id.strip():
        raise AutoCalibrationEvidenceError("image_record_id is required")

    provenance = decision.provenance
    if provenance.get("state") != AutoCalibrationState.AUTO_VERIFIED.value:
        raise AutoCalibrationEvidenceError("provenance state must be AUTO_VERIFIED")
    if provenance.get("clinician_confirmed") is not False:
        raise AutoCalibrationEvidenceError("automatic provenance cannot claim clinician confirmation")

    schema_version = _required_text(provenance, "schema_version")
    detector_method = _required_text(provenance, "detector_method")
    profile_id = _required_text(provenance, "profile_id")
    profile_version = _required_text(provenance, "profile_version")
    validation_reference = _required_text(provenance, "validation_reference")
    known_tick_spacing_mm = _required_positive_number(provenance, "known_tick_spacing_mm")
    median_tick_spacing_px = _required_positive_number(provenance, "median_tick_spacing_px")
    max_spacing_deviation_ratio = _required_number(provenance, "max_spacing_deviation_ratio")
    profile_max_spacing_deviation_ratio = _required_number(
        provenance, "profile_max_spacing_deviation_ratio"
    )
    if max_spacing_deviation_ratio < 0 or profile_max_spacing_deviation_ratio < 0:
        raise AutoCalibrationEvidenceError("spacing deviation ratios cannot be negative")
    if max_spacing_deviation_ratio > profile_max_spacing_deviation_ratio:
        raise AutoCalibrationEvidenceError("candidate spacing exceeds validated profile tolerance")

    candidate_tick_count = provenance.get("candidate_tick_count")
    if type(candidate_tick_count) is not int or candidate_tick_count < 2:
        raise AutoCalibrationEvidenceError("candidate_tick_count must be an integer >= 2")

    expected_ratio = known_tick_spacing_mm / median_tick_spacing_px
    if not math.isclose(expected_ratio, decision.mm_per_pixel, rel_tol=0.0, abs_tol=1e-12):
        raise AutoCalibrationEvidenceError("AUTO_VERIFIED ratio does not match physical/profile geometry")

    provenance_ratio = _required_positive_number(provenance, "mm_per_pixel")
    if not math.isclose(provenance_ratio, decision.mm_per_pixel, rel_tol=0.0, abs_tol=1e-12):
        raise AutoCalibrationEvidenceError("decision and provenance mm_per_pixel disagree")

    resolved_case_id = case_id.strip()
    return SourceEvidence(
        evidence_id=f"source:{resolved_case_id}:calibration",
        patient_id=patient_id,
        kind="calibration",
        source_record_id=f"calibration:{resolved_case_id}",
        recorded_at=recorded_at,
        operator_id=None,
        evidence_status=EvidenceStatus.COMPUTED,
        availability_status=AvailabilityStatus.AVAILABLE,
        quality_status="AUTO_VERIFIED_FIDUCIAL_PROFILE",
        metadata={
            "case_id": resolved_case_id,
            "image_record_id": image_record_id.strip(),
            "method": "AUTO_FIDUCIAL_PROFILE",
            "schema_version": schema_version,
            "detector_method": detector_method,
            "profile_id": profile_id,
            "profile_version": profile_version,
            "validation_reference": validation_reference,
            "known_tick_spacing_mm": known_tick_spacing_mm,
            "candidate_tick_count": candidate_tick_count,
            "median_tick_spacing_px": median_tick_spacing_px,
            "max_spacing_deviation_ratio": max_spacing_deviation_ratio,
            "profile_max_spacing_deviation_ratio": profile_max_spacing_deviation_ratio,
            "mm_per_pixel": decision.mm_per_pixel,
            "clinician_confirmed": False,
        },
    )
