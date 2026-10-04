"""LOT07-G canonical Orthodontic Workbench export.

The exporter is deliberately a projection layer. It never recomputes cephalometric
geometry or measurements and never accepts scientific authority from the client.
LOT06 typed evidence remains the only scientific source.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Final, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from backend import models
from backend.schemas.cephalo_evidence import LandmarkEvidence
from backend.services.cephalo_runtime_chain import (
    CephaloRuntimeChainError,
    project_runtime_chain_read_path,
    validate_active_runtime_chain,
)
from backend.services.cephalo_typed_read import (
    CephaloTypedReadError,
    deserialize_evidence_snapshot,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.ortho_media_record import build_ortho_media_record, validate_ortho_timepoint


ORTHO_WORKBENCH_EXPORT_SCHEMA_VERSION: Final = "ORTHO_WORKBENCH_EXPORT_V1"
ORTHO_WORKBENCH_EXPORT_CONTRACT_VERSION: Final = "ORTHO_WORKBENCH_EXPORT_CONTRACT_V1"
LOT06_SCIENTIFIC_AUTHORITY: Final = "LOT06_CANONICAL_ENGINE"
SCIENTIFIC_READ_AUTHORITY: Final = "EVIDENCE_GRAPH_V1"
LAYER_IDS: Final = (
    "landmarks",
    "plans",
    "hard_tissue",
    "teeth",
    "soft_tissue",
    "measurements",
    "t1",
    "t2",
)
UNAVAILABLE_LAYERS: Final = frozenset({"hard_tissue"})


class OrthoWorkbenchExportError(ValueError):
    """The workbench cannot be exported without inventing or overstating authority."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TracedStructureState(_StrictModel):
    structure_id: str = Field(min_length=1)
    structure_class: str = Field(min_length=1)
    authority_state: Literal["DISPLAY_TEMPLATE_ONLY", "DERIVED_VISUALIZATION"]
    coordinate_space: Literal["IMAGE_PIXEL", "CALIBRATED_MM", "REGISTERED_LONGITUDINAL"]
    version: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime
    provenance: dict[str, Any]
    edit_history: list[dict[str, Any]] = Field(default_factory=list)
    geometry: dict[str, Any] | None = None

    @field_validator("created_at", "updated_at")
    @classmethod
    def _timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("structure timestamps must be timezone-aware")
        return value

    @field_validator("provenance")
    @classmethod
    def _provenance_required(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("structure provenance is required")
        return value


class SessionEditAuditEvent(_StrictModel):
    sequence: int = Field(ge=1)
    action: Literal["EDIT", "UNDO", "REDO", "RESET_TO_BASELINE"]
    transactionId: str = Field(min_length=1)
    changedLandmarkIds: list[str]


class OrthoWorkbenchExportRequest(_StrictModel):
    timepoint: str
    layer_visibility: dict[str, bool]
    layer_opacity: dict[str, float]
    traced_structures: list[TracedStructureState] = Field(default_factory=list)
    session_edit_audit: list[SessionEditAuditEvent] = Field(default_factory=list)

    @field_validator("timepoint")
    @classmethod
    def _valid_timepoint(cls, value: str) -> str:
        return validate_ortho_timepoint(value)

    @field_validator("layer_visibility")
    @classmethod
    def _visibility_complete(cls, value: dict[str, bool]) -> dict[str, bool]:
        if set(value) != set(LAYER_IDS):
            raise ValueError("layer_visibility must contain exactly the canonical LOT07 layer ids")
        if any(value.get(layer_id) for layer_id in UNAVAILABLE_LAYERS):
            raise ValueError("unavailable LOT07 layer cannot be exported as visible")
        return value

    @field_validator("layer_opacity")
    @classmethod
    def _opacity_complete(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != set(LAYER_IDS):
            raise ValueError("layer_opacity must contain exactly the canonical LOT07 layer ids")
        for layer_id, raw in value.items():
            numeric = float(raw)
            if not math.isfinite(numeric) or not 0.1 <= numeric <= 1.0:
                raise ValueError(f"invalid opacity for layer {layer_id}")
        return value


def _current_landmark_rows(payload: Mapping[str, Any], graph) -> list[dict[str, Any]]:
    refs = payload.get("current_landmark_refs")
    if not isinstance(refs, list) or not refs:
        raise OrthoWorkbenchExportError("explicit current_landmark_refs are required for export")
    by_ref = {item.evidence_id: item for item in graph.landmarks}
    rows: list[dict[str, Any]] = []
    for ref in refs:
        item = by_ref.get(ref)
        if item is None:
            raise OrthoWorkbenchExportError(f"current landmark ref does not resolve: {ref}")
        rows.append(
            {
                "evidence_id": item.evidence_id,
                "landmark_id": item.landmark_id,
                "x": item.x,
                "y": item.y,
                "source_image_ref": item.source_image_ref,
                "origin": item.origin.value,
                "validated_by": item.validated_by,
                "validated_at": item.validated_at,
                "availability_status": item.availability_status.value,
            }
        )
    return rows


def _manual_correction_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    snapshots: list[tuple[int | None, Mapping[str, Any]]] = []
    history = payload.get("history", [])
    if not isinstance(history, list):
        raise OrthoWorkbenchExportError("persisted evidence history must be a list")
    for snapshot in history:
        if not isinstance(snapshot, Mapping):
            raise OrthoWorkbenchExportError("persisted evidence history entry must be an object")
        snapshots.append((snapshot.get("revision"), snapshot))
    snapshots.append((payload.get("revision"), payload))

    corrections: list[dict[str, Any]] = []
    seen: set[str] = set()
    for revision, snapshot in snapshots:
        landmarks = snapshot.get("landmarks", [])
        if not isinstance(landmarks, list):
            raise OrthoWorkbenchExportError("persisted history landmarks must be a list")
        for raw_item in landmarks:
            try:
                item = LandmarkEvidence.model_validate(raw_item)
            except ValidationError as exc:
                raise OrthoWorkbenchExportError(
                    "persisted correction history contains invalid landmark evidence"
                ) from exc
            if item.origin.value != "MANUAL_CORRECTED":
                continue
            if item.evidence_id in seen:
                continue
            seen.add(item.evidence_id)
            corrections.append(
                {
                    "revision": revision,
                    "evidence_id": item.evidence_id,
                    "landmark_id": item.landmark_id,
                    "x": item.x,
                    "y": item.y,
                    "original_auto_x": item.original_auto_x,
                    "original_auto_y": item.original_auto_y,
                    "validated_by": item.validated_by,
                    "validated_at": item.validated_at.isoformat() if item.validated_at else None,
                    "evidence_refs": list(item.evidence_refs),
                }
            )
    return corrections


def _construction_refs(chain) -> list[dict[str, Any]]:
    return [
        {
            "construction_id": item.construction_id,
            "definition_id": item.definition_id,
            "definition_version": item.definition_version,
            "landmark_refs": list(item.landmark_refs),
            "evidence_refs": list(item.evidence_refs),
            "availability_status": item.availability_status.value,
        }
        for item in sorted(chain.constructions.values(), key=lambda value: value.construction_id)
    ]


def _measurement_refs(chain) -> list[dict[str, Any]]:
    return [
        {
            "measurement_id": item.measurement_id,
            "analysis_id": item.analysis_id,
            "method_id": item.method_id,
            "method_version": item.method_version,
            "landmark_refs": list(item.landmark_refs),
            "construction_refs": list(item.construction_refs),
            "calibration_ref": item.calibration_ref,
            "requires_calibration": item.requires_calibration,
            "evidence_refs": list(item.evidence_refs),
            "availability_status": item.availability_status.value,
        }
        for item in sorted(chain.measurements.values(), key=lambda value: value.measurement_id)
    ]


def _cephalogram_source(graph):
    sources = [item for item in graph.sources if item.kind == "lateral_ceph"]
    if len(sources) != 1:
        raise OrthoWorkbenchExportError("exactly one canonical lateral cephalogram source is required")
    source = sources[0]
    if source.availability_status.value != "AVAILABLE":
        raise OrthoWorkbenchExportError("canonical lateral cephalogram source must be available")
    return source


def _calibration_payload(chain) -> dict[str, Any] | None:
    if chain.calibration is None:
        requires_current_calibration = any(
            item.requires_calibration and item.availability_status.value == "AVAILABLE"
            for item in chain.measurements.values()
        )
        if requires_current_calibration:
            raise OrthoWorkbenchExportError(
                "available calibration-dependent measurements require current calibration provenance"
            )
        return None
    return chain.calibration.model_dump(mode="json")


def build_ortho_workbench_export(
    db: Session,
    *,
    analysis: models.CephaloAnalysis,
    employer_id: int,
    request: OrthoWorkbenchExportRequest,
    exported_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a deterministic projection from canonical evidence + presentation state."""
    timestamp = exported_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise OrthoWorkbenchExportError("exported_at must be timezone-aware")

    raw_angles = analysis.angles_data
    if not isinstance(raw_angles, dict):
        raise OrthoWorkbenchExportError("typed cephalometric evidence is required for export")
    raw_graph = raw_angles.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(raw_graph, dict):
        raise OrthoWorkbenchExportError("typed cephalometric evidence graph is required for export")

    try:
        projected = project_runtime_chain_read_path(raw_angles, patient_id=analysis.patient_id)
        scientific = projected.get("scientific_read_path")
        if (
            not isinstance(scientific, dict)
            or scientific.get("authority") != SCIENTIFIC_READ_AUTHORITY
            or scientific.get("active_chain") != "VERIFIED"
        ):
            raise OrthoWorkbenchExportError("verified LOT06 scientific read path is required")
        graph = deserialize_evidence_snapshot(raw_graph)
        chain = validate_active_runtime_chain(raw_graph, graph)
    except (CephaloTypedReadError, CephaloRuntimeChainError) as exc:
        raise OrthoWorkbenchExportError("LOT06 scientific prerequisites are incoherent") from exc

    case_id = scientific.get("case_id")
    revision = scientific.get("revision")
    if not isinstance(case_id, str) or not case_id.strip() or not isinstance(revision, int):
        raise OrthoWorkbenchExportError("explicit case_id and evidence revision are required")

    current_landmarks = _current_landmark_rows(raw_graph, graph)
    calibration = _calibration_payload(chain)
    cephalogram_source = _cephalogram_source(graph)

    structure_ids = [item.structure_id for item in request.traced_structures]
    if len(structure_ids) != len(set(structure_ids)):
        raise OrthoWorkbenchExportError("duplicate traced structure ids are not allowed")
    structures: list[dict[str, Any]] = []
    for item in request.traced_structures:
        if item.coordinate_space == "REGISTERED_LONGITUDINAL":
            raise OrthoWorkbenchExportError(
                "longitudinal registration is outside LOT07 export authority"
            )
        if item.coordinate_space == "CALIBRATED_MM" and calibration is None:
            raise OrthoWorkbenchExportError(
                "calibrated structure coordinates require current calibration provenance"
            )
        serialized = item.model_dump(mode="json")
        serialized["server_binding"] = {
            "patient_id": analysis.patient_id,
            "analysis_id": analysis.id,
            "case_id": case_id,
            "timepoint_id": request.timepoint,
            "persistence_state": "SESSION_PRESENTATION_ONLY",
        }
        structures.append(serialized)

    media = build_ortho_media_record(
        db,
        employer_id=employer_id,
        patient_id=analysis.patient_id,
        timepoint=request.timepoint,
    )

    return {
        "schema_version": ORTHO_WORKBENCH_EXPORT_SCHEMA_VERSION,
        "contract_version": ORTHO_WORKBENCH_EXPORT_CONTRACT_VERSION,
        "exported_at": timestamp.isoformat(),
        "authority": {
            "scientific": LOT06_SCIENTIFIC_AUTHORITY,
            "scientific_read": SCIENTIFIC_READ_AUTHORITY,
            "clinical_decision": "CLINICIAN",
            "presentation": "LOT07_PRESENTATION_STATE",
            "correction_history": "BACKEND_CEPHALO_EVIDENCE_HISTORY",
            "media": media["schema_version"],
        },
        "case": {
            "patient_id": analysis.patient_id,
            "analysis_id": analysis.id,
            "case_id": case_id,
            "timepoint_id": request.timepoint,
            "evidence_revision": revision,
            "source_evidence_id": cephalogram_source.evidence_id,
            "source_record_id": cephalogram_source.source_record_id,
            "source_provenance": cephalogram_source.model_dump(mode="json"),
        },
        "landmarks": {
            "authority": "LOT06_TYPED_EVIDENCE_CURRENT_LANDMARKS",
            "current_refs": list(raw_graph["current_landmark_refs"]),
            "items": current_landmarks,
            "canonical_dependency_items": [
                {
                    "evidence_id": item.evidence_id,
                    "landmark_id": item.landmark_id,
                    "x": item.x,
                    "y": item.y,
                    "source_image_ref": item.source_image_ref,
                    "origin": item.origin.value,
                    "availability_status": item.availability_status.value,
                }
                for item in sorted(chain.landmarks.values(), key=lambda value: value.evidence_id)
                if item.evidence_id not in set(raw_graph["current_landmark_refs"])
            ],
        },
        "correction_history": {
            "authority": "BACKEND_CEPHALO_EVIDENCE_HISTORY",
            "persisted_revision_count": len(raw_graph.get("history", [])) + 1,
            "manual_corrections": _manual_correction_rows(raw_graph),
            "session_operations": {
                "authority": "SESSION_OPERATIONAL_UNDO_REDO_ONLY",
                "events": [event.model_dump(mode="json") for event in request.session_edit_audit],
            },
        },
        "traced_structures": {
            "authority": "LOT07_PRESENTATION_STATE_NON_SCIENTIFIC",
            "items": structures,
        },
        "layers": {
            "authority": "LOT07_PRESENTATION_STATE_NON_SCIENTIFIC",
            "visibility": dict(request.layer_visibility),
            "opacity": {key: float(value) for key, value in request.layer_opacity.items()},
        },
        "lot06_scientific_refs": {
            "authority": "LOT06_EXECUTABLE_MEASUREMENT_CONTRACT",
            "evidence_schema_version": scientific["schema_version"],
            "active_chain": scientific["active_chain"],
            "construction_refs": _construction_refs(chain),
            "measurement_refs": _measurement_refs(chain),
            "canonical_measurements": list(scientific.get("canonical_measurements") or []),
            "blocked_method_ids": list(scientific.get("blocked_method_ids") or []),
            "unmapped_method_ids": list(scientific.get("unmapped_method_ids") or []),
        },
        "calibration": {
            "authority": "LOT06_TYPED_SOURCE_EVIDENCE",
            "current": calibration,
        },
        "media": media,
    }
