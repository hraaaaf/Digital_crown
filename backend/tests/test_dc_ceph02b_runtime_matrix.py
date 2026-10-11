"""DC-CEPH-02B: real typed runtime path + honest 38-contract coverage matrix.

Synthetic SRPose38-shaped points only. No actual model, patient, cabinet DB or FACAD.
All production functions are imported normally; unlike DC-CEPH-02A this tests
runtime evidence, revision, calibration, canonical read and PDF projection.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from backend.repositories.cephalo_repository import _canonicalize_evidence_projection
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_pdf_projection import build_cephalo_pdf_projection
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_typed_read import CephaloTypedReadError
from backend.tests.test_cephalo_runtime_chain import (
    CASE_ID, LATER, LATEST, _initial_graph, _points, _raw,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
)
ALLOWED = {"AVAILABLE", "NOT_COMPUTABLE", "INVALID", "NOT_EXPOSED"}


def _read(graph: dict, result) -> dict:
    data = result.model_dump()
    data[EVIDENCE_GRAPH_KEY] = graph
    path = project_runtime_chain_read_path(data, patient_id=7)
    assert path["scientific_read_path"]["active_chain"] == "VERIFIED"
    return path


def _matrix(path: dict) -> tuple[dict[str, str], dict[str, int]]:
    doc = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ids = [item["measurement_id"] for item in doc["measurements"]]
    assert len(ids) == 38 and len(set(ids)) == 38
    projected = path["scientific_read_path"]["canonical_measurements"]
    index = {x["canonical_measurement_id"]: x for x in projected}
    assert len(index) == len(projected), "Duplicate canonical values must not be hidden"
    statuses = {}
    for item in doc["measurements"]:
        key = item["measurement_id"]
        value = index.get(key)
        if value is None:
            statuses[key] = "NOT_EXPOSED"
            continue
        status = value["availability_status"]
        assert status in ALLOWED - {"NOT_EXPOSED"}, f"Invalid runtime status for {key}"
        if status == "AVAILABLE":
            assert value["value"] is not None
            if item["requires_calibration"]:
                # Calibrated value must be generated from a distinct, current source.
                assert value["unit"] == "mm"
        else:
            assert value["value"] is None, f"Unavailable value leaked for {key}"
        expected_unit = "mm" if item["unit"] == "mm" else "deg"
        assert value["unit"] == expected_unit, f"Contract/runtime unit conflict: {key}"
        statuses[key] = status
    counts = {s: list(statuses.values()).count(s) for s in sorted(ALLOWED)}
    assert sum(counts.values()) == 38
    return statuses, counts


def test_real_runtime_revisions_and_all_38_contract_statuses() -> None:
    raw = _raw()
    initial_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    initial_graph = _initial_graph(raw)
    initial_status, initial_count = _matrix(_read(initial_graph, initial_result))
    assert initial_status["M_CO_A_MM_V1"] == "NOT_COMPUTABLE"
    assert initial_count["AVAILABLE"] > 0
    assert all(
        initial_status[x["measurement_id"]] != "AVAILABLE"
        for x in json.loads(CONTRACT.read_text(encoding="utf-8"))["measurements"]
        if x["requires_calibration"]
    ), "Uncalibrated millimetric evidence was promoted"

    canonical = _canonicalize_evidence_projection({EVIDENCE_GRAPH_KEY: initial_graph})[EVIDENCE_GRAPH_KEY]
    edited = [dict(item) for item in raw]
    next(item for item in edited if item["id"] == "A")["x"] += 2.0
    edited_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    second = rebuild_evidence_after_landmark_edit(
        previous_payload=canonical,
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=edited_result,
        runtime_landmarks=edited,
        clinician_id="synthetic-clinician",
        validated_at=LATER,
    )
    assert second["revision_reason"] == "LANDMARK_EDIT"
    assert second["revision"] == 2
    _read(second, edited_result)
    third_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(edited))
    third = rebuild_evidence_after_manual_calibration(
        previous_payload=second,
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=third_result,
        runtime_landmarks=edited,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="synthetic-clinician",
        calibrated_at=LATEST,
    )
    assert third["revision_reason"] == "MANUAL_CALIBRATION"
    assert third["revision"] == 3
    third_status, third_count = _matrix(_read(third, third_result))
    assert third_status["M_CO_A_MM_V1"] == "AVAILABLE"
    assert third_count["AVAILABLE"] > initial_count["AVAILABLE"], "Calibration unlocked no measure"

    correction = [dict(item) for item in edited]
    next(item for item in correction if item["id"] == "B")["x"] += 1.0
    fourth_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(correction))
    fourth = rebuild_evidence_after_landmark_edit(
        previous_payload=third,
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=fourth_result,
        runtime_landmarks=correction,
        clinician_id="synthetic-clinician",
        validated_at=LATEST,
    )
    assert fourth["revision_reason"] == "LANDMARK_EDIT"
    assert fourth["revision"] == 4
    final_projection = _read(fourth, fourth_result)
    final_status, final_count = _matrix(final_projection)
    assert final_status["M_CO_A_MM_V1"] == "AVAILABLE"
    assert final_count["AVAILABLE"] >= third_count["AVAILABLE"] - 2
    assert all(
        x["calibration_ref"] is not None
        for x in fourth["measurements"]
        if x["requires_calibration"] and x["availability_status"] == "AVAILABLE"
    )

    # PDF is an authoritative presentation consumer, not a clinical diagnosis.
    data = fourth_result.model_dump()
    data[EVIDENCE_GRAPH_KEY] = fourth
    pdf = build_cephalo_pdf_projection(patient_id=7, analysis_id=9, angles_data=data)
    if pdf["active_runtime_chain_verified"]:
        assert pdf["measurements"] and pdf["canonical_measurements"]
    else:
        assert pdf["measurements"] == [] and pdf["canonical_measurements"] == []
    assert pdf["document_state"] != "COMPLETE", "Fixture cannot certify a clinical report"

    # Never write per-measure, per-patient, raw landmark or numeric values to CI.
    aggregate = {
        "schema": "DC_CEPH02B_RUNTIME_MATRIX_V1",
        "status": "SYNTHETIC_RUNTIME_ONLY",
        "contract_measurements": 38,
        "uncalibrated": initial_count,
        "calibrated": third_count,
        "post_correction": final_count,
        "revision_sequence": ["INITIAL", "LANDMARK_EDIT", "MANUAL_CALIBRATION", "LANDMARK_EDIT"],
        "typed_runtime_read_valid": True,
        "pdf_projection_invoked": True,
        "pdf_document_clinically_complete": False,
        "all_38_measurements_available": False,
        "facad_numeric_parity_proved": False,
        "clinical_activation_allowed": False,
        "real_patient_data_used": False,
    }
    assert sum(aggregate["post_correction"].values()) == 38
    print("DC_CEPH02B_MATRIX_SAFE=" + json.dumps(aggregate, sort_keys=True, separators=(",", ":")))


def test_tampered_active_landmark_prevents_runtime_and_pdf_value_promotion() -> None:
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    graph = _initial_graph(raw)
    tampered = deepcopy(graph)
    refs = tampered["current_landmark_refs"]
    assert refs and len(refs) == 38
    # Keep the object but remove one current authority while retaining references.
    target = next(item for item in tampered["constructions"]
                  if item["definition_id"] == "CRANIOM_A_TO_N_VERTICAL_V1")
    stale_ref = next(ref for ref in target["landmark_refs"] if ref.endswith(":A"))
    refs.remove(stale_ref)
    with pytest.raises(CephaloTypedReadError, match="active runtime chain"):
        _read(tampered, result)
    data = result.model_dump()
    data[EVIDENCE_GRAPH_KEY] = tampered
    pdf = build_cephalo_pdf_projection(patient_id=7, analysis_id=9, angles_data=data)
    assert pdf["active_runtime_chain_verified"] is False
    assert pdf["measurements"] == [] and pdf["canonical_measurements"] == []
    assert pdf["document_state"] == "INCOMPLETE"
