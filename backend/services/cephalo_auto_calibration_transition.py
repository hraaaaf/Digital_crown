"""Audited calibration-only transition for an AUTO_VERIFIED fiducial decision.

The transition preserves the current landmark/construction evidence exactly. It
replaces only calibration provenance and calibration-dependent measurements.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Mapping, Sequence

from backend.schemas.cephalo_evidence import (
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.schemas.clinical import CephaloAnalysisResult
from backend.services.cephalo_auto_calibration_evidence import (
    AutoCalibrationEvidenceError,
    source_evidence_from_auto_decision,
)
from backend.services.cephalo_auto_calibration_gate import AutoCalibrationDecision, AutoCalibrationState
from backend.services.cephalo_calibration_evidence import (
    _assert_runtime_points_match_evidence,
    _current_geometry_landmarks,
    _explicit_current_landmarks,
    _history,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_measurement_adapter import adapt_craniom_linear_measurements
from backend.services.cephalo_runtime_evidence import EVIDENCE_SCHEMA_VERSION

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
    if (
        decision.mm_per_pixel is None
        or not math.isfinite(decision.mm_per_pixel)
        or decision.mm_per_pixel <= 0
        or not isinstance(decision.provenance, Mapping)
    ):
        raise AutoCalibrationTransitionError("AUTO_VERIFIED decision requires ratio and provenance")
    if not isinstance(decision.reason, str) or not decision.reason.strip():
        raise AutoCalibrationTransitionError("AUTO_VERIFIED decision requires a gate reason")
    return {
        "schema_version": "CEPHALO_AUTO_CALIBRATION_V1",
        "method": "AUTO_FIDUCIAL_PROFILE",
        "state": AutoCalibrationState.AUTO_VERIFIED.value,
        "reason": decision.reason.strip(),
        "mm_per_pixel": float(decision.mm_per_pixel),
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
    decision: AutoCalibrationDecision,
    calibrated_at: dt.datetime,
) -> dict[str, Any]:
    """Create one calibration-only evidence revision from a pre-gated decision."""
    _assert_transition_allowed(previous_payload)
    if calibrated_at.tzinfo is None or calibrated_at.utcoffset() is None:
        raise AutoCalibrationTransitionError("calibrated_at must be timezone-aware")
    auto_calibration_data_from_decision(decision)

    revision = previous_payload.get("revision")
    case_id = previous_payload.get("case_id")
    if not isinstance(revision, int) or revision < 1:
        raise AutoCalibrationTransitionError("invalid persisted revision")
    if not isinstance(case_id, str) or not case_id.strip():
        raise AutoCalibrationTransitionError("invalid persisted case_id")

    try:
        sources = [SourceEvidence.model_validate(raw) for raw in previous_payload.get("sources", [])]
        landmarks = [LandmarkEvidence.model_validate(raw) for raw in previous_payload.get("landmarks", [])]
        constructions = [
            ConstructionEvidence.model_validate(raw)
            for raw in previous_payload.get("constructions", [])
        ]
        old_measurements = [
            MeasurementEvidence.model_validate(raw)
            for raw in previous_payload.get("measurements", [])
        ]
        validate_case_evidence_graph(
            EvidenceGraphSnapshot(
                sources=sources,
                landmarks=landmarks,
                constructions=constructions,
                measurements=old_measurements,
            ),
            patient_id=patient_id,
            case_id=case_id,
        )

        ceph_sources = [source for source in sources if source.kind == "lateral_ceph"]
        if len(ceph_sources) != 1:
            raise AutoCalibrationTransitionError(
                "evidence snapshot requires exactly one cephalogram source"
            )
        if ceph_sources[0].source_record_id != image_record_id:
            raise AutoCalibrationTransitionError("persisted cephalogram source record mismatch")

        explicit_current = _explicit_current_landmarks(previous_payload, landmarks)
        if explicit_current is not None:
            current_ref_set = {item.evidence_id for item in explicit_current.values()}
            stale_construction_refs = sorted(
                {
                    ref
                    for construction in constructions
                    for ref in construction.landmark_refs
                    if ref not in current_ref_set
                }
            )
            if stale_construction_refs:
                raise AutoCalibrationTransitionError(
                    "construction references non-current landmark evidence: "
                    + ", ".join(stale_construction_refs)
                )
            _assert_runtime_points_match_evidence(
                runtime_landmarks,
                explicit_current,
                require_exact_set=True,
            )
        else:
            geometry_landmarks = _current_geometry_landmarks(landmarks, constructions)
            _assert_runtime_points_match_evidence(runtime_landmarks, geometry_landmarks)

        runtime_ratio = result.analysis_metadata.pixel_ratio
        if (
            runtime_ratio is None
            or not math.isfinite(runtime_ratio)
            or decision.mm_per_pixel is None
            or not math.isclose(
                float(runtime_ratio),
                float(decision.mm_per_pixel),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise AutoCalibrationTransitionError(
                "runtime ratio does not match AUTO_VERIFIED calibration decision"
            )

        next_revision = revision + 1
        calibration = source_evidence_from_auto_decision(
            patient_id=patient_id,
            case_id=case_id,
            image_record_id=image_record_id,
            decision=decision,
            recorded_at=calibrated_at,
        )
        metadata = dict(calibration.metadata)
        metadata.update(
            {
                "revision": next_revision,
                "calibrated_at": calibrated_at.isoformat(),
            }
        )
        calibration = calibration.model_copy(
            update={
                "evidence_id": f"source:{case_id}:calibration:r{next_revision}",
                "source_record_id": f"calibration:{case_id}:r{next_revision}",
                "metadata": metadata,
            }
        )

        construction_map = {item.definition_id: item for item in constructions}
        measurements = adapt_craniom_linear_measurements(
            result,
            measurement_namespace=f"measurement:{case_id}:r{next_revision}",
            constructions=construction_map,
            calibration_ref=calibration.evidence_id,
        )
        current_sources = [source for source in sources if source.kind != "calibration"] + [calibration]
        graph = EvidenceGraphSnapshot(
            sources=current_sources,
            landmarks=landmarks,
            constructions=constructions,
            measurements=measurements,
        )
        validate_case_evidence_graph(graph, patient_id=patient_id, case_id=case_id)
    except AutoCalibrationTransitionError:
        raise
    except AutoCalibrationEvidenceError as exc:
        raise AutoCalibrationTransitionError(str(exc)) from exc
    except ValueError as exc:
        raise AutoCalibrationTransitionError(str(exc)) from exc

    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "case_id": case_id,
        "revision": next_revision,
        "revision_reason": "AUTO_CALIBRATION",
        "legacy_angles_data_role": "COMPATIBILITY_OUTPUT",
        "history": _history(previous_payload),
        "sources": [item.model_dump(mode="json") for item in current_sources],
        "landmarks": [item.model_dump(mode="json") for item in landmarks],
        "constructions": [item.model_dump(mode="json") for item in constructions],
        "measurements": [item.model_dump(mode="json") for item in measurements],
        "normative_evaluations": [],
        "findings": [],
        "diagnoses": [],
        "problems": [],
        "objectives": [],
        "treatment_options": [],
        "validations": [],
        "final_plans": [],
    }
    if explicit_current is not None:
        payload["current_landmark_refs"] = [
            item.evidence_id for item in explicit_current.values()
        ]
    return payload
