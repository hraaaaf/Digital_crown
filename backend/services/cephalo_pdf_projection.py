"""Authoritative, fail-closed document projection for cephalometric PDF output.

The PDF is a presentation surface only. This module consumes the active typed
measurement chain plus the R15 Clinical Scientific Studio snapshot and emits a
single renderer-neutral document model. It deliberately ignores legacy free-text
clinical fields such as ai_diagnostic, ai_narrative and clinical_data.
"""
from __future__ import annotations

from typing import Any, Mapping

from backend.services.cephalo_r15_clinical_studio import build_r15_clinical_studio_snapshot
from backend.services.cephalo_runtime_chain import (
    project_runtime_chain_read_path,
    validate_active_runtime_chain,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_typed_read import deserialize_evidence_snapshot

CEPHALO_PDF_PROJECTION_VERSION = "CEPHALO_PDF_PROJECTION_V1"


def _measurement_row(measurement: Any) -> dict[str, Any]:
    status = getattr(measurement.availability_status, "value", str(measurement.availability_status))
    return {
        "measurement_id": measurement.measurement_id,
        "analysis_id": measurement.analysis_id,
        "method_id": measurement.method_id,
        "method_version": measurement.method_version,
        "value": measurement.value,
        "unit": measurement.unit,
        "availability_status": status,
        "requires_calibration": bool(measurement.requires_calibration),
        "calibration_ref": measurement.calibration_ref,
        "landmark_refs": list(measurement.landmark_refs),
        "construction_refs": list(measurement.construction_refs),
        "evidence_refs": list(measurement.evidence_refs),
        "scientific_source": "EVIDENCE_GRAPH_V1",
    }


def build_cephalo_pdf_projection(
    *,
    patient_id: int,
    analysis_id: int | None,
    angles_data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the renderer-neutral PDF model from backend authority only.

    Missing or incoherent typed evidence never falls back to legacy patient
    numbers. Measurements are exposed only after the exact authoritative runtime
    read path, including case integrity, succeeds for this patient.
    """
    payload = dict(angles_data or {})
    studio = build_r15_clinical_studio_snapshot(
        patient_id=patient_id,
        analysis_id=analysis_id,
        angles_data=payload,
    )

    measurements: list[dict[str, Any]] = []
    projection_blockers: list[str] = []
    typed_projection_verified = False
    graph_payload = payload.get(EVIDENCE_GRAPH_KEY)

    if isinstance(graph_payload, dict):
        try:
            # This is the same authoritative read gate used by the API/Studio. It
            # verifies typed-read case integrity before any patient value is exposed.
            project_runtime_chain_read_path(payload, patient_id=patient_id)
            graph = deserialize_evidence_snapshot(graph_payload)
            chain = validate_active_runtime_chain(graph_payload, graph)
            measurements = sorted(
                (_measurement_row(item) for item in chain.measurements.values()),
                key=lambda row: row["measurement_id"],
            )
            typed_projection_verified = True
        except Exception:
            projection_blockers.append("typed_measurement_projection_incoherent")
    else:
        projection_blockers.append("typed_evidence_graph_missing")

    stages = []
    for stage in studio.get("stages", []):
        stages.append(
            {
                "stage_id": stage.get("stage_id"),
                "title": stage.get("title"),
                "presentation_state": stage.get("presentation_state"),
                "authoritative_status": stage.get("authoritative_status"),
                "summary": stage.get("summary"),
                "blocking_gates": list(stage.get("blocking_gates") or []),
                "missing_data_refs": list(stage.get("missing_data_refs") or []),
                "contradictions": list(stage.get("contradictions") or []),
                "contraindications": list(stage.get("contraindications") or []),
                "provenance": list(stage.get("provenance") or []),
                "clinician_action": dict(stage.get("clinician_action") or {}),
            }
        )

    blockers = sorted(
        set(studio.get("blocking_gates") or []) | set(projection_blockers)
    )
    is_complete = bool(studio.get("clinical_validation_available")) and not blockers
    active_runtime_chain_verified = (
        bool(studio.get("active_runtime_chain_verified")) and typed_projection_verified
    )

    return {
        "contract_version": CEPHALO_PDF_PROJECTION_VERSION,
        "patient_id": patient_id,
        "analysis_id": analysis_id,
        "document_state": "COMPLETE" if is_complete else "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": active_runtime_chain_verified,
        "evidence_graph_present": bool(studio.get("evidence_graph_present")),
        "measurements": measurements,
        "stages": stages,
        "blocking_gates": blockers,
        "clinical_validation_available": bool(studio.get("clinical_validation_available")),
        "clinical_validation_reason": studio.get("clinical_validation_reason"),
    }
