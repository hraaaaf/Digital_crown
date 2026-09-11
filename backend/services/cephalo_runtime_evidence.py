"""Persist typed cephalometric evidence inside legacy angles_data JSON.

No norms, diagnosis, interpretation or treatment logic is created here.
"""
from __future__ import annotations

import datetime as dt
import math
import uuid
from typing import Any, Mapping, Optional, Sequence

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin, SourceEvidence
from backend.schemas.clinical import CephaloAnalysisResult
from backend.services.cephalo_auto_calibration_evidence import (
    AutoCalibrationEvidenceError,
    source_evidence_from_auto_decision,
)
from backend.services.cephalo_auto_calibration_gate import AutoCalibrationDecision, AutoCalibrationState
from backend.services.cephalo_construction_evidence_adapter import materialize_craniom_linear_constructions
from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_measurement_adapter import adapt_craniom_linear_measurements
from backend.services.cephalo_steiner_dental_evidence import (
    adapt_steiner_dental_measurements,
    materialize_steiner_dental_constructions,
)
from backend.services.cephalo_steiner_evidence_adapter import (
    adapt_steiner_skeletal_measurements,
    materialize_steiner_skeletal_constructions,
)
from backend.services.sota_vision_service import (
    SOTA_LANDMARKS_MAPPING,
    SRPOSE38_MODEL_NAME,
    SRPOSE38_MODEL_SHA256,
)

EVIDENCE_GRAPH_KEY = "_evidence_graph_v1"
EVIDENCE_SCHEMA_VERSION = "CEPHALO_EVIDENCE_V1"
SRPOSE38_PIPELINE_VERSION = "SRPOSE38_TTA_1024_V1"
_SRPOSE38_IDS = frozenset(SOTA_LANDMARKS_MAPPING.values())

class CephaloRuntimeEvidenceError(ValueError):
    pass

def _num(value: Any, label: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise CephaloRuntimeEvidenceError(f"{label} must be numeric") from exc
    if not math.isfinite(out):
        raise CephaloRuntimeEvidenceError(f"{label} must be finite")
    return out

def _validate_previous(previous: Optional[Mapping[str, Any]]) -> None:
    if previous and previous.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise CephaloRuntimeEvidenceError("Unsupported persisted evidence schema version")

def _case(previous: Optional[Mapping[str, Any]], requested: Optional[str]) -> str:
    old = previous.get("case_id") if previous else None
    if old is not None and (not isinstance(old, str) or not old.strip()):
        raise CephaloRuntimeEvidenceError("Invalid persisted case_id")
    if requested and old and requested != old:
        raise CephaloRuntimeEvidenceError("case_id mismatch")
    return requested or old or f"cephalo:{uuid.uuid4()}"

def _revision(previous: Optional[Mapping[str, Any]]) -> int:
    if not previous:
        return 1
    value = previous.get("revision")
    if not isinstance(value, int) or value < 1:
        raise CephaloRuntimeEvidenceError("Invalid persisted revision")
    return value + 1

def _history(previous: Optional[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not previous:
        return []
    old_history = previous.get("history", [])
    if not isinstance(old_history, list):
        raise CephaloRuntimeEvidenceError("Persisted evidence history must be a list")
    return [*old_history, {
        "revision": previous.get("revision"),
        "sources": previous.get("sources", []),
        "landmarks": previous.get("landmarks", []),
        "constructions": previous.get("constructions", []),
        "measurements": previous.get("measurements", []),
    }]

def _old_auto(previous: Optional[Mapping[str, Any]]) -> list[LandmarkEvidence]:
    if not previous:
        return []
    return [
        item for raw in previous.get("landmarks", [])
        if (item := LandmarkEvidence.model_validate(raw)).origin == LandmarkOrigin.SRPOSE38_AUTO
    ]

def _current_landmarks(
    raw_points: Sequence[Mapping[str, Any]], *, case_id: str, revision: int,
    source_ref: str, inference_mode: Optional[str], manual: bool,
) -> list[LandmarkEvidence]:
    if not manual and inference_mode != "SOTA_ONNX_38":
        return []
    out: list[LandmarkEvidence] = []
    seen: set[str] = set()
    for raw in raw_points:
        landmark_id = raw.get("id")
        if not isinstance(landmark_id, str) or not landmark_id.strip():
            raise CephaloRuntimeEvidenceError("Landmark id must be non-empty")
        if landmark_id in seen:
            raise CephaloRuntimeEvidenceError(f"Duplicate landmark id: {landmark_id}")
        seen.add(landmark_id)
        common = dict(
            landmark_id=landmark_id, x=_num(raw.get("x"), f"{landmark_id}.x"),
            y=_num(raw.get("y"), f"{landmark_id}.y"), source_image_ref=source_ref,
            evidence_refs=[source_ref],
        )
        if manual:
            out.append(LandmarkEvidence(
                evidence_id=f"landmark:{case_id}:r{revision}:{landmark_id}",
                origin=LandmarkOrigin.MANUAL, evidence_status=EvidenceStatus.OBSERVED, **common,
            ))
        else:
            out.append(LandmarkEvidence(
                evidence_id=f"landmark:{case_id}:auto:{landmark_id}",
                origin=LandmarkOrigin.SRPOSE38_AUTO,
                model_id=SRPOSE38_MODEL_NAME, model_sha256=SRPOSE38_MODEL_SHA256,
                pipeline_version=SRPOSE38_PIPELINE_VERSION,
                evidence_status=EvidenceStatus.COMPUTED, **common,
            ))
    if not manual and seen != _SRPOSE38_IDS:
        missing = sorted(_SRPOSE38_IDS - seen)
        extra = sorted(seen - _SRPOSE38_IDS)
        raise CephaloRuntimeEvidenceError(
            f"SOTA_ONNX_38 evidence requires exact 38-landmark contract; missing={missing}, extra={extra}"
        )
    return out

def _assert_runtime_geometry_matches(
    result: CephaloAnalysisResult,
    current: Mapping[str, LandmarkEvidence],
) -> None:
    required = {"S", "N", "Po", "Or", "A", "B"}
    if not required.issubset(current):
        return
    point = lambda key: (current[key].x, current[key].y)
    ratio = result.analysis_metadata.pixel_ratio
    expected = {
        "Situation_A": nasion_vertical_offset_mm_v1(point("A"), point("N"), point("Po"), point("Or"), ratio),
        "Situation_B": nasion_vertical_offset_mm_v1(point("B"), point("N"), point("Po"), point("Or"), ratio),
        "Decalage_A_B": craniom_ab_prime_mm_v1(point("A"), point("B"), point("Po"), point("Or"), ratio),
        "Profondeur_Faciale": craniom_facial_depth_mm_v1(point("S"), point("N"), point("Po"), point("Or"), ratio),
    }
    skeletal = result.metrics.analyse_osseuse
    for field, expected_value in expected.items():
        runtime_value = getattr(skeletal, field).valeur
        if expected_value is None:
            if runtime_value is not None:
                raise CephaloRuntimeEvidenceError(f"Runtime {field} exists although evidence geometry is not computable")
            continue
        expected_runtime_value = round(expected_value, 1)
        if runtime_value is None or not math.isfinite(runtime_value) or not math.isclose(runtime_value, expected_runtime_value, rel_tol=0.0, abs_tol=1e-12):
            raise CephaloRuntimeEvidenceError(f"Runtime {field} does not match persisted evidence geometry")

def _calibration_source(
    *, patient_id: int, case_id: str, image_record_id: str, result: CephaloAnalysisResult,
    is_calibrated: bool, calibration_data: Optional[Mapping[str, Any]], recorded_at: dt.datetime,
) -> Optional[SourceEvidence]:
    if not is_calibrated or not isinstance(calibration_data, Mapping):
        return None

    method = calibration_data.get("method")
    if method == "AUTO_FIDUCIAL_PROFILE":
        if calibration_data.get("state") != AutoCalibrationState.AUTO_VERIFIED.value:
            raise CephaloRuntimeEvidenceError("Automatic calibration must be AUTO_VERIFIED")
        provenance = calibration_data.get("provenance")
        if not isinstance(provenance, Mapping):
            raise CephaloRuntimeEvidenceError("AUTO_VERIFIED calibration requires provenance")
        ratio = result.analysis_metadata.pixel_ratio
        if ratio is None or not math.isfinite(ratio) or ratio <= 0:
            raise CephaloRuntimeEvidenceError("AUTO_VERIFIED calibration requires a valid runtime ratio")
        reason = calibration_data.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise CephaloRuntimeEvidenceError("AUTO_VERIFIED calibration requires a gate reason")
        decision = AutoCalibrationDecision(
            state=AutoCalibrationState.AUTO_VERIFIED,
            reason=reason.strip(),
            mm_per_pixel=float(ratio),
            provenance=dict(provenance),
        )
        try:
            return source_evidence_from_auto_decision(
                patient_id=patient_id,
                case_id=case_id,
                image_record_id=image_record_id,
                decision=decision,
                recorded_at=recorded_at,
            )
        except AutoCalibrationEvidenceError as exc:
            raise CephaloRuntimeEvidenceError(str(exc)) from exc

    if method not in {None, "MANUAL_TWO_POINT"}:
        raise CephaloRuntimeEvidenceError(f"Unsupported calibration method: {method}")
    if not {"p1", "p2", "distance_mm"}.issubset(calibration_data):
        return None
    p1, p2 = calibration_data.get("p1"), calibration_data.get("p2")
    if not isinstance(p1, Mapping) or not isinstance(p2, Mapping):
        return None
    x1, y1, x2, y2 = (_num(p1.get("x"), "p1.x"), _num(p1.get("y"), "p1.y"), _num(p2.get("x"), "p2.x"), _num(p2.get("y"), "p2.y"))
    distance_mm = _num(calibration_data.get("distance_mm"), "distance_mm")
    distance_px = math.hypot(x2 - x1, y2 - y1)
    ratio = result.analysis_metadata.pixel_ratio
    if distance_mm <= 0 or distance_px <= 0 or ratio is None or ratio <= 0 or not math.isfinite(ratio):
        raise CephaloRuntimeEvidenceError("Invalid manual calibration")
    if not math.isclose(distance_mm / distance_px, ratio, rel_tol=1e-6, abs_tol=1e-9):
        raise CephaloRuntimeEvidenceError("Calibration geometry does not match runtime ratio")
    return SourceEvidence(
        evidence_id=f"source:{case_id}:calibration", patient_id=patient_id,
        kind="calibration", source_record_id=f"calibration:{case_id}", recorded_at=recorded_at,
        quality_status="VERIFIED_MANUAL_TWO_POINT",
        metadata={"case_id": case_id, "method": "MANUAL_TWO_POINT", "p1": dict(p1), "p2": dict(p2), "distance_mm": distance_mm, "mm_per_pixel": ratio},
    )

def build_cephalo_runtime_evidence_payload(
    *, patient_id: int, image_record_id: str, result: CephaloAnalysisResult,
    landmarks: Sequence[Mapping[str, Any]], inference_mode: Optional[str],
    previous_payload: Optional[Mapping[str, Any]] = None, manual_revision: bool = False,
    is_calibrated: bool = False, calibration_data: Optional[Mapping[str, Any]] = None,
    recorded_at: Optional[dt.datetime] = None, case_id: Optional[str] = None,
) -> dict[str, Any]:
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise CephaloRuntimeEvidenceError("patient_id must be positive")
    if not isinstance(image_record_id, str) or not image_record_id.strip():
        raise CephaloRuntimeEvidenceError("image_record_id must be non-empty")
    _validate_previous(previous_payload)
    resolved_case = _case(previous_payload, case_id)
    revision = _revision(previous_payload)
    timestamp = recorded_at or dt.datetime.now(dt.timezone.utc)
    ceph_source = SourceEvidence(
        evidence_id=f"source:{resolved_case}:ceph", patient_id=patient_id, kind="lateral_ceph",
        source_record_id=image_record_id, recorded_at=timestamp, metadata={"case_id": resolved_case},
    )
    if previous_payload:
        old_sources = [SourceEvidence.model_validate(raw) for raw in previous_payload.get("sources", [])]
        old_ceph = next((src for src in old_sources if src.kind == "lateral_ceph"), None)
        if old_ceph:
            if old_ceph.patient_id != patient_id or old_ceph.metadata.get("case_id") != resolved_case:
                raise CephaloRuntimeEvidenceError("Persisted source patient/case mismatch")
            if old_ceph.source_record_id != image_record_id:
                raise CephaloRuntimeEvidenceError("Persisted cephalogram source record mismatch")
            ceph_source = old_ceph
    current = _current_landmarks(
        landmarks, case_id=resolved_case, revision=revision, source_ref=ceph_source.evidence_id,
        inference_mode=inference_mode, manual=manual_revision,
    )
    current_by_id = {lm.landmark_id: lm for lm in current}
    _assert_runtime_geometry_matches(result, current_by_id)
    graph_landmarks = (_old_auto(previous_payload) if manual_revision else []) + current

    # Preserve the historical CRANIOM evidence IDs exactly. Steiner is additive
    # and gets its own namespace; introducing R5 must not rename existing R4 evidence.
    craniom_constructions = materialize_craniom_linear_constructions(
        current_by_id, construction_namespace=f"construction:{resolved_case}:r{revision}",
    )
    steiner_constructions = materialize_steiner_skeletal_constructions(
        current_by_id, construction_namespace=f"construction:{resolved_case}:r{revision}:steiner",
    )
    steiner_dental_constructions = materialize_steiner_dental_constructions(
        current_by_id,
        construction_namespace=f"construction:{resolved_case}:r{revision}:steiner:dental",
    )

    calibration = _calibration_source(
        patient_id=patient_id, case_id=resolved_case, image_record_id=image_record_id,
        result=result, is_calibrated=is_calibrated,
        calibration_data=calibration_data, recorded_at=timestamp,
    )
    craniom_measurements = adapt_craniom_linear_measurements(
        result, measurement_namespace=f"measurement:{resolved_case}:r{revision}",
        constructions=craniom_constructions, calibration_ref=calibration.evidence_id if calibration else None,
    )
    steiner_measurements = adapt_steiner_skeletal_measurements(
        result, measurement_namespace=f"measurement:{resolved_case}:r{revision}:steiner",
        constructions=steiner_constructions,
    )
    steiner_dental_measurements = adapt_steiner_dental_measurements(
        measurement_namespace=f"measurement:{resolved_case}:r{revision}:steiner:dental",
        constructions=steiner_dental_constructions,
    )

    all_constructions = [
        *craniom_constructions.values(),
        *steiner_constructions.values(),
        *steiner_dental_constructions.values(),
    ]
    all_measurements = [
        *craniom_measurements,
        *steiner_measurements,
        *steiner_dental_measurements,
    ]
    sources = [ceph_source] + ([calibration] if calibration else [])
    graph = EvidenceGraphSnapshot(
        sources=sources, landmarks=graph_landmarks,
        constructions=all_constructions, measurements=all_measurements,
    )
    validate_case_evidence_graph(graph, patient_id=patient_id, case_id=resolved_case)
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION, "case_id": resolved_case, "revision": revision,
        "legacy_angles_data_role": "COMPATIBILITY_OUTPUT",
        "history": _history(previous_payload),
        "sources": [x.model_dump(mode="json") for x in sources],
        "landmarks": [x.model_dump(mode="json") for x in graph_landmarks],
        "constructions": [x.model_dump(mode="json") for x in all_constructions],
        "measurements": [x.model_dump(mode="json") for x in all_measurements],
        "normative_evaluations": [], "findings": [], "diagnoses": [], "problems": [],
        "objectives": [], "treatment_options": [], "validations": [], "final_plans": [],
    }