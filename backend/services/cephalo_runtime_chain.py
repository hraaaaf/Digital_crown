"""Active runtime-chain validation for persisted cephalometric evidence.

The generic evidence graph intentionally preserves historical/audit objects. Runtime
science must additionally prove which landmark evidence objects are *current* before
constructions and measurements can become read authority.

No norms, diagnosis, interpretation, or treatment logic lives here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from backend.schemas.cephalo_evidence import (
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_typed_read import (
    CephaloTypedReadError,
    deserialize_evidence_snapshot,
    project_typed_craniom_read_path,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


class CephaloRuntimeChainError(ValueError):
    """Persisted evidence is referentially valid but has no safe active runtime chain."""


@dataclass(frozen=True)
class ActiveRuntimeChain:
    landmarks: Mapping[str, LandmarkEvidence]
    constructions: Mapping[str, ConstructionEvidence]
    measurements: Mapping[str, MeasurementEvidence]
    calibration: SourceEvidence | None


def _active_landmarks(
    payload: Mapping[str, Any],
    graph: EvidenceGraphSnapshot,
) -> dict[str, LandmarkEvidence]:
    by_ref = {item.evidence_id: item for item in graph.landmarks}
    refs = payload.get("current_landmark_refs")

    if refs is None:
        # Compatibility only for pre-R2 snapshots. It is safe solely while every
        # landmark id has one unambiguous evidence object.
        grouped: dict[str, list[LandmarkEvidence]] = {}
        for item in graph.landmarks:
            grouped.setdefault(item.landmark_id, []).append(item)
        ambiguous = sorted(key for key, items in grouped.items() if len(items) != 1)
        if ambiguous:
            raise CephaloRuntimeChainError(
                "Current landmark authority is ambiguous without current_landmark_refs: "
                + ", ".join(ambiguous)
            )
        return {key: items[0] for key, items in grouped.items()}

    if not isinstance(refs, list):
        raise CephaloRuntimeChainError("current_landmark_refs must be a list")

    selected: dict[str, LandmarkEvidence] = {}
    seen_refs: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip() or ref in seen_refs:
            raise CephaloRuntimeChainError("Invalid current landmark evidence ref")
        seen_refs.add(ref)
        item = by_ref.get(ref)
        if item is None:
            raise CephaloRuntimeChainError(f"Current landmark ref does not resolve: {ref}")
        if item.landmark_id in selected:
            raise CephaloRuntimeChainError(
                f"Multiple current evidence objects for landmark {item.landmark_id}"
            )
        selected[item.landmark_id] = item
    return selected


def validate_active_runtime_chain(
    payload: Mapping[str, Any],
    graph: EvidenceGraphSnapshot,
) -> ActiveRuntimeChain:
    """Resolve and validate the exact source → landmark → construction → measurement chain."""
    current = _active_landmarks(payload, graph)
    current_refs = {item.evidence_id for item in current.values()}

    construction_map: dict[str, ConstructionEvidence] = {}
    for construction in graph.constructions:
        stale = sorted(set(construction.landmark_refs) - current_refs)
        if stale:
            raise CephaloRuntimeChainError(
                f"Construction {construction.construction_id} references non-current landmark evidence: "
                + ", ".join(stale)
            )
        construction_map[construction.construction_id] = construction

    measurement_map: dict[str, MeasurementEvidence] = {}
    for measurement in graph.measurements:
        stale_landmarks = sorted(set(measurement.landmark_refs) - current_refs)
        if stale_landmarks:
            raise CephaloRuntimeChainError(
                f"Measurement {measurement.measurement_id} references non-current landmark evidence: "
                + ", ".join(stale_landmarks)
            )
        measurement_map[measurement.measurement_id] = measurement

    calibrations = [source for source in graph.sources if source.kind == "calibration"]
    if len(calibrations) > 1:
        raise CephaloRuntimeChainError("Multiple current calibration sources")
    calibration = calibrations[0] if calibrations else None
    if calibration is not None:
        for measurement in graph.measurements:
            if measurement.calibration_ref is not None and measurement.calibration_ref != calibration.evidence_id:
                raise CephaloRuntimeChainError(
                    f"Measurement {measurement.measurement_id} references a non-current calibration source"
                )

    return ActiveRuntimeChain(
        landmarks=current,
        constructions=construction_map,
        measurements=measurement_map,
        calibration=calibration,
    )


def project_runtime_chain_read_path(
    angles_data: Mapping[str, Any],
    *,
    patient_id: int,
) -> dict[str, Any]:
    """Project typed CRANIOM values only after active-chain authority is proven."""
    projected = project_typed_craniom_read_path(angles_data, patient_id=patient_id)
    payload = angles_data.get(EVIDENCE_GRAPH_KEY)
    if payload is None:
        return projected
    if not isinstance(payload, dict):
        raise CephaloTypedReadError("Persisted evidence graph must be an object")

    graph = deserialize_evidence_snapshot(payload)
    try:
        chain = validate_active_runtime_chain(payload, graph)
    except CephaloRuntimeChainError as exc:
        raise CephaloTypedReadError("Persisted evidence active runtime chain is incoherent") from exc

    projected["scientific_read_path"] = {
        **projected.get("scientific_read_path", {}),
        "active_chain": "VERIFIED",
        "current_landmark_count": len(chain.landmarks),
        "current_construction_count": len(chain.constructions),
        "current_measurement_count": len(chain.measurements),
    }
    return projected
