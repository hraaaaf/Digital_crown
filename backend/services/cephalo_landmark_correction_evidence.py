"""Audited landmark-edit transition for persisted cephalometric evidence.

The transition distinguishes unchanged points from clinician edits, preserves the
original SRPose38 coordinates, rematerializes geometry, and keeps an explicit set of
current landmark evidence refs so omitted points can never resurrect from history.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Mapping, Sequence

from backend.schemas.cephalo_evidence import (
    ConstructionEvidence,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.schemas.clinical import CephaloAnalysisResult
from backend.services.cephalo_construction_evidence_adapter import materialize_craniom_linear_constructions
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_measurement_adapter import adapt_craniom_linear_measurements
from backend.services.cephalo_runtime_evidence import EVIDENCE_SCHEMA_VERSION, CephaloRuntimeEvidenceError

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


def _current_landmark_map(
    landmarks: Sequence[LandmarkEvidence],
    current_refs: Sequence[str] | None = None,
) -> dict[str, LandmarkEvidence]:
    by_ref = {item.evidence_id: item for item in landmarks}
    if current_refs is not None:
        if not isinstance(current_refs, (list, tuple)):
            raise CephaloRuntimeEvidenceError("current_landmark_refs must be a list")
        selected: dict[str, LandmarkEvidence] = {}
        seen_refs: set[str] = set()
        for ref in current_refs:
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

    # Backward-compatible inference for snapshots created before current_landmark_refs.
    grouped: dict[str, list[LandmarkEvidence]] = {}
    for item in landmarks:
        grouped.setdefault(item.landmark_id, []).append(item)

    current: dict[str, LandmarkEvidence] = {}
    for landmark_id, candidates in grouped.items():
        manual = [item for item in candidates if item.origin != LandmarkOrigin.SRPOSE38_AUTO]
        if len(manual) > 1:
            raise CephaloRuntimeEvidenceError(
                f"Multiple current manual evidence objects for landmark {landmark_id}"
            )
        if manual:
            current[landmark_id] = manual[0]
            continue
        auto = [item for item in candidates if item.origin == LandmarkOrigin.SRPOSE38_AUTO]
        if len(auto) != 1:
            raise CephaloRuntimeEvidenceError(
                f"Ambiguous automatic evidence for landmark {landmark_id}"
            )
        current[landmark_id] = auto[0]
    return current


def _raw_map(raw_landmarks: Sequence[Mapping[str, Any]]) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    for raw in raw_landmarks:
        landmark_id = raw.get("id")
        if not isinstance(landmark_id, str) or not landmark_id.strip():
            raise CephaloRuntimeEvidenceError("Runtime landmark id must be non-empty")
        if landmark_id in result:
            raise CephaloRuntimeEvidenceError(f"Duplicate runtime landmark id: {landmark_id}")
        result[landmark_id] = (
            _finite(raw.get("x"), f"{landmark_id}.x"),
            _finite(raw.get("y"), f"{landmark_id}.y"),
        )
    return result


def landmark_submission_changed(
    previous_payload: Mapping[str, Any],
    runtime_landmarks: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether the submitted point set/coordinates differ from current evidence."""
    if previous_payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise CephaloRuntimeEvidenceError("Unsupported persisted evidence schema version")
    landmarks = [LandmarkEvidence.model_validate(raw) for raw in previous_payload.get("landmarks", [])]
    current = _current_landmark_map(landmarks, previous_payload.get("current_landmark_refs"))
    raw = _raw_map(runtime_landmarks)
    if set(raw) != set(current):
        return True
    return any(raw[key] != (current[key].x, current[key].y) for key in raw)


def _edited_landmark(
    *,
    previous: LandmarkEvidence | None,
    landmark_id: str,
    coords: tuple[float, float],
    source_ref: str,
    case_id: str,
    revision: int,
    clinician_id: str,
    validated_at: dt.datetime,
) -> LandmarkEvidence:
    common = dict(
        evidence_id=f"landmark:{case_id}:r{revision}:{landmark_id}",
        landmark_id=landmark_id,
        x=coords[0],
        y=coords[1],
        source_image_ref=source_ref,
        evidence_refs=[source_ref],
        validated_by=clinician_id,
        validated_at=validated_at,
        evidence_status=EvidenceStatus.CLINICIAN_VALIDATED,
    )
    if previous is None or previous.origin == LandmarkOrigin.MANUAL:
        return LandmarkEvidence(origin=LandmarkOrigin.MANUAL, **common)

    if previous.origin == LandmarkOrigin.SRPOSE38_AUTO:
        original_x, original_y = previous.x, previous.y
    else:
        original_x, original_y = previous.original_auto_x, previous.original_auto_y
        if original_x is None or original_y is None:
            raise CephaloRuntimeEvidenceError(
                f"Corrected landmark {landmark_id} lost original automatic coordinates"
            )

    return LandmarkEvidence(
        origin=LandmarkOrigin.MANUAL_CORRECTED,
        original_auto_x=original_x,
        original_auto_y=original_y,
        **common,
    )


def rebuild_evidence_after_landmark_edit(
    *,
    previous_payload: Mapping[str, Any],
    patient_id: int,
    image_record_id: str,
    result: CephaloAnalysisResult,
    runtime_landmarks: Sequence[Mapping[str, Any]],
    clinician_id: str,
    validated_at: dt.datetime,
) -> dict[str, Any]:
    """Create one clinician-audited landmark revision; unchanged submissions are no-ops."""
    if previous_payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise CephaloRuntimeEvidenceError("Unsupported persisted evidence schema version")
    if not clinician_id.strip():
        raise CephaloRuntimeEvidenceError("Landmark edit requires clinician_id")
    if validated_at.tzinfo is None or validated_at.utcoffset() is None:
        raise CephaloRuntimeEvidenceError("Landmark edit timestamp must be timezone-aware")

    revision = previous_payload.get("revision")
    case_id = previous_payload.get("case_id")
    if not isinstance(revision, int) or revision < 1:
        raise CephaloRuntimeEvidenceError("Invalid persisted revision")
    if not isinstance(case_id, str) or not case_id.strip():
        raise CephaloRuntimeEvidenceError("Invalid persisted case_id")

    sources = [SourceEvidence.model_validate(raw) for raw in previous_payload.get("sources", [])]
    landmarks = [LandmarkEvidence.model_validate(raw) for raw in previous_payload.get("landmarks", [])]
    constructions = [ConstructionEvidence.model_validate(raw) for raw in previous_payload.get("constructions", [])]
    measurements = [MeasurementEvidence.model_validate(raw) for raw in previous_payload.get("measurements", [])]
    validate_case_evidence_graph(
        EvidenceGraphSnapshot(
            sources=sources,
            landmarks=landmarks,
            constructions=constructions,
            measurements=measurements,
        ),
        patient_id=patient_id,
        case_id=case_id,
    )

    ceph_sources = [source for source in sources if source.kind == "lateral_ceph"]
    if len(ceph_sources) != 1 or ceph_sources[0].source_record_id != image_record_id:
        raise CephaloRuntimeEvidenceError("Persisted cephalogram source record mismatch")
    source_ref = ceph_sources[0].evidence_id

    previous_current = _current_landmark_map(
        landmarks, previous_payload.get("current_landmark_refs")
    )
    raw = _raw_map(runtime_landmarks)
    changed = set(raw) != set(previous_current) or any(
        raw[key] != (previous_current[key].x, previous_current[key].y)
        for key in raw.keys() & previous_current.keys()
    )
    if not changed:
        return dict(previous_payload)

    for key in _DOWNSTREAM_KEYS:
        if previous_payload.get(key):
            raise CephaloRuntimeEvidenceError(
                f"Landmark edit cannot silently preserve downstream clinical evidence: {key}"
            )

    # Preserve the immutable SRPose anchor independently from the current point set.
    # If a previously omitted SRPose point is manually reintroduced, that is an audited
    # correction event, not a fresh MANUAL point and not an automatic resurrection.
    original_auto = {
        item.landmark_id: item
        for item in landmarks
        if item.origin == LandmarkOrigin.SRPOSE38_AUTO
    }

    next_revision = revision + 1
    next_current: dict[str, LandmarkEvidence] = {}
    for landmark_id, coords in raw.items():
        old_current = previous_current.get(landmark_id)
        if old_current is not None and coords == (old_current.x, old_current.y):
            next_current[landmark_id] = old_current
        else:
            lineage = old_current or original_auto.get(landmark_id)
            next_current[landmark_id] = _edited_landmark(
                previous=lineage,
                landmark_id=landmark_id,
                coords=coords,
                source_ref=source_ref,
                case_id=case_id,
                revision=next_revision,
                clinician_id=clinician_id,
                validated_at=validated_at,
            )

    # Keep immutable machine evidence for audit, but mark the current point set
    # explicitly. This prevents an omitted point from becoming current again later.
    graph_landmarks_by_ref: dict[str, LandmarkEvidence] = {
        item.evidence_id: item for item in original_auto.values()
    }
    for item in next_current.values():
        graph_landmarks_by_ref[item.evidence_id] = item
    graph_landmarks = list(graph_landmarks_by_ref.values())

    new_constructions = materialize_craniom_linear_constructions(
        next_current,
        construction_namespace=f"construction:{case_id}:r{next_revision}",
    )
    calibration_sources = [source for source in sources if source.kind == "calibration"]
    if len(calibration_sources) > 1:
        raise CephaloRuntimeEvidenceError("Multiple current calibration sources")
    calibration_ref = calibration_sources[0].evidence_id if calibration_sources else None
    new_measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace=f"measurement:{case_id}:r{next_revision}",
        constructions=new_constructions,
        calibration_ref=calibration_ref,
    )

    graph = EvidenceGraphSnapshot(
        sources=sources,
        landmarks=graph_landmarks,
        constructions=list(new_constructions.values()),
        measurements=new_measurements,
    )
    validate_case_evidence_graph(graph, patient_id=patient_id, case_id=case_id)

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "case_id": case_id,
        "revision": next_revision,
        "revision_reason": "LANDMARK_EDIT",
        "authority_status": "PERSISTED_NOT_YET_READ_PATH",
        "legacy_angles_data_role": "COMPATIBILITY_OUTPUT",
        "history": _history(previous_payload),
        "sources": [item.model_dump(mode="json") for item in sources],
        "landmarks": [item.model_dump(mode="json") for item in graph_landmarks],
        "current_landmark_refs": [item.evidence_id for item in next_current.values()],
        "constructions": [item.model_dump(mode="json") for item in new_constructions.values()],
        "measurements": [item.model_dump(mode="json") for item in new_measurements],
        "normative_evaluations": [],
        "findings": [],
        "diagnoses": [],
        "problems": [],
        "objectives": [],
        "treatment_options": [],
        "validations": [],
        "final_plans": [],
    }
