"""Optional clinician confirmation of an already AUTO_VERIFIED calibration.

Confirmation is an audit-only revision: it changes neither physical scale nor
patient measurement values, and it never erases the original automatic provenance.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Mapping

from backend.schemas.cephalo_evidence import (
    ConstructionEvidence,
    EvidenceStatus,
    LandmarkEvidence,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.services.cephalo_calibration_evidence import _history
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
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


class AutoCalibrationConfirmationError(ValueError):
    pass


def confirm_auto_calibration(
    *,
    previous_payload: Mapping[str, Any],
    patient_id: int,
    clinician_id: str,
    confirmed_at: dt.datetime,
) -> dict[str, Any]:
    """Create a clinician-confirmation revision without changing scale or values."""
    if previous_payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise AutoCalibrationConfirmationError("typed evidence graph is required")
    if not isinstance(clinician_id, str) or not clinician_id.strip():
        raise AutoCalibrationConfirmationError("clinician_id is required")
    if confirmed_at.tzinfo is None or confirmed_at.utcoffset() is None:
        raise AutoCalibrationConfirmationError("confirmed_at must be timezone-aware")

    for key in _DOWNSTREAM_CLINICAL_KEYS:
        value = previous_payload.get(key, [])
        if not isinstance(value, list):
            raise AutoCalibrationConfirmationError(f"invalid downstream evidence collection: {key}")
        if value:
            raise AutoCalibrationConfirmationError(
                f"confirmation blocked because downstream clinical evidence exists: {key}"
            )

    revision = previous_payload.get("revision")
    case_id = previous_payload.get("case_id")
    if not isinstance(revision, int) or revision < 1:
        raise AutoCalibrationConfirmationError("invalid persisted revision")
    if not isinstance(case_id, str) or not case_id.strip():
        raise AutoCalibrationConfirmationError("invalid persisted case_id")

    try:
        sources = [SourceEvidence.model_validate(raw) for raw in previous_payload.get("sources", [])]
        landmarks = [LandmarkEvidence.model_validate(raw) for raw in previous_payload.get("landmarks", [])]
        constructions = [
            ConstructionEvidence.model_validate(raw)
            for raw in previous_payload.get("constructions", [])
        ]
        measurements = [
            MeasurementEvidence.model_validate(raw)
            for raw in previous_payload.get("measurements", [])
        ]
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
    except ValueError as exc:
        raise AutoCalibrationConfirmationError(str(exc)) from exc

    calibration_sources = [source for source in sources if source.kind == "calibration"]
    if len(calibration_sources) != 1:
        raise AutoCalibrationConfirmationError("exactly one current calibration source is required")
    current_calibration = calibration_sources[0]
    if current_calibration.quality_status != "AUTO_VERIFIED_FIDUCIAL_PROFILE":
        raise AutoCalibrationConfirmationError("only AUTO_VERIFIED calibration can be clinician-confirmed")
    if current_calibration.metadata.get("method") != "AUTO_FIDUCIAL_PROFILE":
        raise AutoCalibrationConfirmationError("automatic fiducial provenance is required")
    if current_calibration.metadata.get("clinician_confirmed") is not False:
        raise AutoCalibrationConfirmationError("automatic calibration is already clinician-confirmed")

    next_revision = revision + 1
    confirmed_source_id = f"source:{case_id}:calibration:r{next_revision}"
    metadata = dict(current_calibration.metadata)
    metadata.update(
        {
            "auto_gate_state": "AUTO_VERIFIED",
            "clinician_confirmed": True,
            "confirmed_by": clinician_id.strip(),
            "confirmed_at": confirmed_at.isoformat(),
            "revision": next_revision,
        }
    )
    confirmed_source = current_calibration.model_copy(
        update={
            "evidence_id": confirmed_source_id,
            "source_record_id": f"calibration:{case_id}:r{next_revision}",
            "operator_id": clinician_id.strip(),
            "recorded_at": confirmed_at,
            "evidence_status": EvidenceStatus.CLINICIAN_VALIDATED,
            "quality_status": "CLINICIAN_CONFIRMED_AUTO_FIDUCIAL_PROFILE",
            "metadata": metadata,
        }
    )

    updated_measurements: list[MeasurementEvidence] = []
    for measurement in measurements:
        if measurement.calibration_ref != current_calibration.evidence_id:
            raise AutoCalibrationConfirmationError(
                f"measurement {measurement.measurement_id} does not reference current calibration"
            )
        updated_measurements.append(
            measurement.model_copy(
                update={
                    "calibration_ref": confirmed_source_id,
                    "evidence_refs": [
                        confirmed_source_id if ref == current_calibration.evidence_id else ref
                        for ref in measurement.evidence_refs
                    ],
                }
            )
        )

    current_sources = [source for source in sources if source.kind != "calibration"] + [confirmed_source]
    graph = EvidenceGraphSnapshot(
        sources=current_sources,
        landmarks=landmarks,
        constructions=constructions,
        measurements=updated_measurements,
    )
    try:
        validate_case_evidence_graph(graph, patient_id=patient_id, case_id=case_id)
    except ValueError as exc:
        raise AutoCalibrationConfirmationError(str(exc)) from exc

    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "case_id": case_id,
        "revision": next_revision,
        "revision_reason": "CLINICIAN_CALIBRATION_CONFIRMATION",
        "legacy_angles_data_role": "COMPATIBILITY_OUTPUT",
        "history": _history(previous_payload),
        "sources": [item.model_dump(mode="json") for item in current_sources],
        "landmarks": [item.model_dump(mode="json") for item in landmarks],
        "constructions": [item.model_dump(mode="json") for item in constructions],
        "measurements": [item.model_dump(mode="json") for item in updated_measurements],
        "normative_evaluations": [],
        "findings": [],
        "diagnoses": [],
        "problems": [],
        "objectives": [],
        "treatment_options": [],
        "validations": [],
        "final_plans": [],
    }
    current_refs = previous_payload.get("current_landmark_refs")
    if current_refs is not None:
        if not isinstance(current_refs, list):
            raise AutoCalibrationConfirmationError("current_landmark_refs must be a list")
        payload["current_landmark_refs"] = list(current_refs)
    return payload
