"""Audited transition from AUTO_VERIFIED decision to a new typed evidence revision."""
from __future__ import annotations

import datetime as dt
from typing import Any, Mapping, Sequence

from backend.schemas.clinical import CephaloAnalysisResult
from backend.services.cephalo_auto_calibration_gate import AutoCalibrationDecision, AutoCalibrationState
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    CephaloRuntimeEvidenceError,
    build_cephalo_runtime_evidence_payload,
)

_DOWNSTREAM_CLINICAL_KEYS = (
    "normative_evaluations",
    "findings",
    "diagnoses",
    "problems",
    "objectives",
    "treatment_options",
    "validations",
    "final_plans",
)


class AutoCalibrationTransitionError(ValueError):
    pass


def auto_calibration_data_from_decision(decision: AutoCalibrationDecision) -> dict[str, Any]:
    if decision.state is not AutoCalibrationState.AUTO_VERIFIED:
        raise AutoCalibrationTransitionError("automatic transition requires AUTO_VERIFIED decision")
    if decision.mm_per_pixel is None or not isinstance(decision.provenance, Mapping):
        raise AutoCalibrationTransitionError("AUTO_VERIFIED decision requires ratio and provenance")
    return {
        "schema_version": "CEPHALO_AUTO_CALIBRATION_V1",
        "method": "AUTO_FIDUCIAL_PROFILE",
        "state": AutoCalibrationState.AUTO_VERIFIED.value,
        "reason": decision.reason,
        "mm_per_pixel": decision.mm_per_pixel,
        "provenance": dict(decision.provenance),
    }


def _assert_transition_allowed(previous_payload: Mapping[str, Any]) -> None:
    if previous_payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise AutoCalibrationTransitionError("typed evidence graph is required for auto calibration")
    for key in _DOWNSTREAM_CLINICAL_KEYS:
        value = previous_payload.get(key, [])
        if not isinstance(value, list):
            raise AutoCalibrationTransitionError(f"invalid downstream evidence collection: {key}")
        if value:
            raise AutoCalibrationTransitionError(
                f"auto calibration blocked because downstream clinical evidence exists: {key}"
            )


def rebuild_evidence_after_auto_calibration(
    *,
    previous_payload: Mapping[str, Any],
    patient_id: int,
    image_record_id: str,
    result: CephaloAnalysisResult,
    runtime_landmarks: Sequence[Mapping[str, Any]],
    inference_mode: str | None,
    decision: AutoCalibrationDecision,
    calibrated_at: dt.datetime,
) -> dict[str, Any]:
    """Create one new evidence revision from a pre-gated automatic calibration."""
    _assert_transition_allowed(previous_payload)
    if calibrated_at.tzinfo is None or calibrated_at.utcoffset() is None:
        raise AutoCalibrationTransitionError("calibrated_at must be timezone-aware")
    calibration_data = auto_calibration_data_from_decision(decision)
    try:
        return build_cephalo_runtime_evidence_payload(
            patient_id=patient_id,
            image_record_id=image_record_id,
            result=result,
            landmarks=runtime_landmarks,
            inference_mode=inference_mode,
            previous_payload=previous_payload,
            manual_revision=False,
            is_calibrated=True,
            calibration_data=calibration_data,
            recorded_at=calibrated_at,
            case_id=previous_payload.get("case_id"),
        )
    except CephaloRuntimeEvidenceError as exc:
        raise AutoCalibrationTransitionError(str(exc)) from exc
