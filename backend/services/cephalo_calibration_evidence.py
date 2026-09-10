"""Audited manual-calibration transition for persisted cephalometric evidence.

This module changes calibration provenance and the four already-versioned CRANIOM
linear measurements only. It never activates norms, diagnosis or treatment.
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
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_measurement_adapter import adapt_craniom_linear_measurements
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    CephaloRuntimeEvidenceError,
)

_DOWNSTREAM_KEYS = (
    "normative_evaluations",
    "findings",
    "diagnoses",
    "problems",
    "objectives",
    "treatment_options",
    "validations",
    "final_plans",
)


def _finite(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CephaloRuntimeEvidenceError(f"{label} must be numeric") from exc
    if not math.isfinite(numeric):
        raise CephaloRuntimeEvidenceError(f"{label} must be finite")
    return numeric


def _history(previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    history = previous.get("history", [])
    if not isinstance(history, list):
        raise CephaloRuntimeEvidenceError("Persisted evidence history must be a list")
    return [
        *history,
        {
            "revision": previous.get("revision"),
            "sources": previous.get("sources", []),
            "landmarks": previous.get("landmarks", []),
            "current_landmark_refs": previous.get("current_landmark_refs"),
            "constructions": previous.get("constructions", []),
            "measurements": previous.get("measurements", []),
        },
    ]


def _explicit_current_landmarks(
    previous_payload: Mapping[str, Any],
    landmarks: Sequence[LandmarkEvidence],
) -> dict[str, LandmarkEvidence] | None:
    refs = previous_payload.get("current_landmark_refs")
    if refs is None:
        return None
    if not isinstance(refs, list):
        raise CephaloRuntimeEvidenceError("current_landmark_refs must be a list")
    by_ref = {item.evidence_id: item for item in landmarks}
    selected: dict[str, LandmarkEvidence] = {}
    seen_refs: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip() or ref in seen_refs:
            raise CephaloRuntimeEvidenceError("Invalid current landmark evidence ref")
        seen_refs.add(ref)
        item = by_ref.get(ref)
        if item is None:
            raise CephaloRuntimeEvidenceError(f"Current landmark ref does not resolve: {ref}")
        if item.landmark_id in selected:
            raise CephaloRuntimeEvidenceError(
                f"Multiple current evidence objects for landmark {item.landmark_id}"
            )
        selected[item.landmark_id] = item
    return selected


def _current_geometry_landmarks(
    landmarks: Sequence[LandmarkEvidence],
    constructions: Sequence[ConstructionEvidence],
) -> dict[str, LandmarkEvidence]:
    by_ref = {item.evidence_id: item for item in landmarks}
    selected: dict[str, LandmarkEvidence] = {}
    for construction in constructions:
        for ref in construction.landmark_refs:
            item = by_ref.get(ref)
            if item is None:
                raise CephaloRuntimeEvidenceError(
                    f"Construction {construction.construction_id} references missing landmark {ref}"
                )
            previous = selected.get(item.landmark_id)
            if previous is not None and previous.evidence_id != item.evidence_id:
                raise CephaloRuntimeEvidenceError(
                    f"Conflicting current evidence for landmark {item.landmark_id}"
                )
            selected[item.landmark_id] = item
    return selected


def _runtime_point_map(
    raw_landmarks: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[float, float]]:
    raw_by_id: dict[str, tuple[float, float]] = {}
    for raw in raw_landmarks:
        landmark_id = raw.get("id")
        if not isinstance(landmark_id, str) or not landmark_id.strip():
            raise CephaloRuntimeEvidenceError("Runtime landmark id must be non-empty")
        if landmark_id in raw_by_id:
            raise CephaloRuntimeEvidenceError(f"Duplicate runtime landmark id: {landmark_id}")
        raw_by_id[landmark_id] = (
            _finite(raw.get("x"), f"{landmark_id}.x"),
            _finite(raw.get("y"), f"{landmark_id}.y"),
        )
    return raw_by_id


def _assert_runtime_points_match_evidence(
    raw_landmarks: Sequence[Mapping[str, Any]],
    evidence_landmarks: Mapping[str, LandmarkEvidence],
    *,
    require_exact_set: bool = False,
) -> None:
    raw_by_id = _runtime_point_map(raw_landmarks)
    if require_exact_set and set(raw_by_id) != set(evidence_landmarks):
        raise CephaloRuntimeEvidenceError(
            "Runtime landmark set differs from explicit current evidence"
        )
    for landmark_id, evidence in evidence_landmarks.items():
        runtime = raw_by_id.get(landmark_id)
        if runtime is None:
            raise CephaloRuntimeEvidenceError(
                f"Runtime landmarks missing evidence landmark {landmark_id}"
            )
        if runtime != (evidence.x, evidence.y):
            raise CephaloRuntimeEvidenceError(
                f"Runtime landmark {landmark_id} differs from persisted evidence"
            )


def rebuild_evidence_after_manual_calibration(
    *,
    previous_payload: Mapping[str, Any],
    patient_id: int,
    image_record_id: str,
    result: CephaloAnalysisResult,
    runtime_landmarks: Sequence[Mapping[str, Any]],
    p1: Mapping[str, Any],
    p2: Mapping[str, Any],
    distance_mm: float,
    clinician_id: str,
    calibrated_at: dt.datetime,
) -> dict[str, Any]:
    """Create one calibration-only evidence revision from the current snapshot."""
    if previous_payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise CephaloRuntimeEvidenceError("Unsupported persisted evidence schema version")
    if not clinician_id.strip():
        raise CephaloRuntimeEvidenceError("Manual calibration requires clinician_id")
    if calibrated_at.tzinfo is None or calibrated_at.utcoffset() is None:
        raise CephaloRuntimeEvidenceError("Manual calibration timestamp must be timezone-aware")
    for key in _DOWNSTREAM_KEYS:
        if previous_payload.get(key):
            raise CephaloRuntimeEvidenceError(
                f"Calibration cannot silently preserve downstream clinical evidence: {key}"
            )

    revision = previous_payload.get("revision")
    case_id = previous_payload.get("case_id")
    if not isinstance(revision, int) or revision < 1:
        raise CephaloRuntimeEvidenceError("Invalid persisted revision")
    if not isinstance(case_id, str) or not case_id.strip():
        raise CephaloRuntimeEvidenceError("Invalid persisted case_id")

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
        raise CephaloRuntimeEvidenceError("Evidence snapshot requires exactly one cephalogram source")
    ceph_source = ceph_sources[0]
    if ceph_source.source_record_id != image_record_id:
        raise CephaloRuntimeEvidenceError("Persisted cephalogram source record mismatch")

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
            raise CephaloRuntimeEvidenceError(
                "Construction references non-current landmark evidence: "
                + ", ".join(stale_construction_refs)
            )
        _assert_runtime_points_match_evidence(
            runtime_landmarks,
            explicit_current,
            require_exact_set=True,
        )
    else:
        # Compatibility path for snapshots created before current_landmark_refs existed.
        geometry_landmarks = _current_geometry_landmarks(landmarks, constructions)
        _assert_runtime_points_match_evidence(runtime_landmarks, geometry_landmarks)

    x1 = _finite(p1.get("x"), "p1.x")
    y1 = _finite(p1.get("y"), "p1.y")
    x2 = _finite(p2.get("x"), "p2.x")
    y2 = _finite(p2.get("y"), "p2.y")
    real_mm = _finite(distance_mm, "distance_mm")
    distance_px = math.hypot(x2 - x1, y2 - y1)
    ratio = result.analysis_metadata.pixel_ratio
    if real_mm <= 0 or distance_px <= 0 or ratio is None or ratio <= 0 or not math.isfinite(ratio):
        raise CephaloRuntimeEvidenceError("Invalid manual calibration geometry")
    if not math.isclose(real_mm / distance_px, ratio, rel_tol=1e-6, abs_tol=1e-9):
        raise CephaloRuntimeEvidenceError("Calibration geometry does not match runtime ratio")

    next_revision = revision + 1
    calibration = SourceEvidence(
        evidence_id=f"source:{case_id}:calibration:r{next_revision}",
        patient_id=patient_id,
        kind="calibration",
        source_record_id=f"calibration:{case_id}:r{next_revision}",
        recorded_at=calibrated_at,
        operator_id=clinician_id,
        quality_status="VERIFIED_MANUAL_TWO_POINT",
        metadata={
            "case_id": case_id,
            "method": "MANUAL_TWO_POINT",
            "method_version": "1",
            "p1": {"x": x1, "y": y1},
            "p2": {"x": x2, "y": y2},
            "distance_mm": real_mm,
            "mm_per_pixel": ratio,
            "calibrated_by": clinician_id,
            "calibrated_at": calibrated_at.isoformat(),
        },
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

    payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "case_id": case_id,
        "revision": next_revision,
        "revision_reason": "MANUAL_CALIBRATION",
        "authority_status": "PERSISTED_NOT_YET_READ_PATH",
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
