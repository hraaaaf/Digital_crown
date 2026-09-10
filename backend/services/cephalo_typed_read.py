"""Read-path projection from persisted typed cephalometric evidence.

Only the four already-versioned CRANIOM linear measurements become authoritative
here. No norm, interpretation, diagnosis or treatment logic is performed.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, TypeVar

from pydantic import BaseModel, ValidationError

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ClinicianValidationEvidence,
    ConstructionEvidence,
    DiagnosticHypothesisEvidence,
    FinalPlanEvidence,
    FindingEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
    NormativeEvaluationEvidence,
    ObjectiveEvidence,
    ProblemEvidence,
    SourceEvidence,
    TreatmentOptionEvidence,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot, EvidenceGraphValidationError
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, EVIDENCE_SCHEMA_VERSION


class CephaloTypedReadError(ValueError):
    """Persisted typed evidence cannot safely serve as read authority."""


_CRANIOM_METHOD_TO_LEGACY_FIELD = {
    "CRANIOM_SITUATION_A_MM_V1": "Situation_A",
    "CRANIOM_SITUATION_B_MM_V1": "Situation_B",
    "CRANIOM_AB_PRIME_MM_V1": "Decalage_A_B",
    "CRANIOM_FACIAL_DEPTH_MM_V1": "Profondeur_Faciale",
}

T = TypeVar("T", bound=BaseModel)


def _models(payload: Mapping[str, Any], key: str, model: type[T]) -> list[T]:
    raw = payload.get(key, [])
    if not isinstance(raw, list):
        raise CephaloTypedReadError(f"Evidence field {key} must be a list")
    try:
        return [model.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise CephaloTypedReadError(f"Invalid typed evidence in {key}") from exc


def deserialize_evidence_snapshot(payload: Mapping[str, Any]) -> EvidenceGraphSnapshot:
    if payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise CephaloTypedReadError("Unsupported persisted evidence schema version")
    return EvidenceGraphSnapshot(
        sources=_models(payload, "sources", SourceEvidence),
        landmarks=_models(payload, "landmarks", LandmarkEvidence),
        constructions=_models(payload, "constructions", ConstructionEvidence),
        measurements=_models(payload, "measurements", MeasurementEvidence),
        normative_evaluations=_models(
            payload, "normative_evaluations", NormativeEvaluationEvidence
        ),
        findings=_models(payload, "findings", FindingEvidence),
        diagnoses=_models(payload, "diagnoses", DiagnosticHypothesisEvidence),
        problems=_models(payload, "problems", ProblemEvidence),
        objectives=_models(payload, "objectives", ObjectiveEvidence),
        treatment_options=_models(payload, "treatment_options", TreatmentOptionEvidence),
        validations=_models(payload, "validations", ClinicianValidationEvidence),
        final_plans=_models(payload, "final_plans", FinalPlanEvidence),
    )


def project_typed_craniom_read_path(
    angles_data: Mapping[str, Any],
    *,
    patient_id: int,
) -> dict[str, Any]:
    """Overlay the four typed CRANIOM measurements onto legacy response fields.

    Legacy analyses without a typed graph are copied unchanged. Once a typed graph
    exists, those four values never fall back to legacy numbers: unavailable typed
    evidence projects to ``None`` and malformed typed evidence fails closed.

    Historical snapshots may contain the obsolete ``authority_status`` metadata key.
    Read authority is a property of this active projection, not an immutable property
    of a stored scientific snapshot, so that legacy marker is not exposed downstream.
    """
    projected = deepcopy(dict(angles_data))
    payload = projected.get(EVIDENCE_GRAPH_KEY)
    if payload is None:
        return projected
    if not isinstance(payload, dict):
        raise CephaloTypedReadError("Persisted evidence graph must be an object")

    case_id = payload.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise CephaloTypedReadError("Persisted evidence case_id must be explicit")

    graph = deserialize_evidence_snapshot(payload)
    try:
        validate_case_evidence_graph(graph, patient_id=patient_id, case_id=case_id)
    except EvidenceGraphValidationError as exc:
        raise CephaloTypedReadError("Persisted evidence graph failed case integrity") from exc

    by_method: dict[str, MeasurementEvidence] = {}
    for measurement in graph.measurements:
        if measurement.method_id not in _CRANIOM_METHOD_TO_LEGACY_FIELD:
            continue
        if measurement.method_id in by_method:
            raise CephaloTypedReadError(
                f"Duplicate typed CRANIOM measurement method: {measurement.method_id}"
            )
        by_method[measurement.method_id] = measurement

    missing = sorted(set(_CRANIOM_METHOD_TO_LEGACY_FIELD) - set(by_method))
    if missing:
        raise CephaloTypedReadError(
            "Typed CRANIOM read authority is incomplete: " + ", ".join(missing)
        )

    metrics = projected.setdefault("metrics", {})
    if not isinstance(metrics, dict):
        raise CephaloTypedReadError("Legacy metrics payload must be an object")
    skeletal = metrics.setdefault("analyse_osseuse", {})
    if not isinstance(skeletal, dict):
        raise CephaloTypedReadError("Legacy analyse_osseuse payload must be an object")

    for method_id, field_name in _CRANIOM_METHOD_TO_LEGACY_FIELD.items():
        measurement = by_method[method_id]
        current = skeletal.setdefault(field_name, {})
        if not isinstance(current, dict):
            raise CephaloTypedReadError(f"Legacy field {field_name} must be an object")
        current["valeur"] = (
            measurement.value
            if measurement.availability_status == AvailabilityStatus.AVAILABLE
            else None
        )
        current["availability_status"] = measurement.availability_status.value
        current["scientific_source"] = "EVIDENCE_GRAPH_V1"
        current["measurement_id"] = measurement.measurement_id

    # Older snapshots carried a software-state marker claiming the graph was not yet
    # on a read path. Keeping that marker in an authoritative GET response would be
    # self-contradictory. Preserve the scientific snapshot, retire only that metadata.
    payload.pop("authority_status", None)

    projected["scientific_read_path"] = {
        "authority": "EVIDENCE_GRAPH_V1",
        "schema_version": payload["schema_version"],
        "case_id": case_id,
        "revision": payload.get("revision"),
        "authoritative_fields": list(_CRANIOM_METHOD_TO_LEGACY_FIELD.values()),
    }
    return projected


CRANIOM_TYPED_READ_FIELDS = tuple(_CRANIOM_METHOD_TO_LEGACY_FIELD.values())
