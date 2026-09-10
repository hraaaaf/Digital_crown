"""Read-path contracts for the four versioned CRANIOM linear measurements."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.cephalo_typed_read import CephaloTypedReadError, project_typed_craniom_read_path
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 16, 0, tzinfo=timezone.utc)
CASE_ID = "cephalo:typed-read-test"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _angles_with_graph(*, ratio=None, calibrated=False):
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=ratio).calculate_metrics(_points(raw))
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    if calibrated:
        graph = rebuild_evidence_after_manual_calibration(
            previous_payload=graph,
            patient_id=7,
            image_record_id="radio.jpg",
            result=result,
            runtime_landmarks=raw,
            p1={"x": 0.0, "y": 0.0},
            p2={"x": 0.0, "y": 50.0},
            distance_mm=10.0,
            clinician_id="99",
            calibrated_at=NOW,
        )
    angles = result.model_dump()
    angles[EVIDENCE_GRAPH_KEY] = graph
    return angles, graph


def _typed_by_field(graph):
    result = {}
    for measurement in graph["measurements"]:
        field = measurement["measurement_id"].rsplit(":", 1)[-1]
        result[field] = measurement
    return result


def test_available_typed_measurement_overrides_stale_legacy_number_without_mutating_input():
    angles, graph = _angles_with_graph(ratio=0.2, calibrated=True)
    original_typed = _typed_by_field(graph)["Situation_A"]
    angles["metrics"]["analyse_osseuse"]["Situation_A"]["valeur"] = 999.0

    projected = project_typed_craniom_read_path(angles, patient_id=7)

    assert angles["metrics"]["analyse_osseuse"]["Situation_A"]["valeur"] == 999.0
    output = projected["metrics"]["analyse_osseuse"]["Situation_A"]
    assert output["valeur"] == original_typed["value"]
    assert output["valeur"] != 999.0
    assert output["scientific_source"] == "EVIDENCE_GRAPH_V1"
    assert output["availability_status"] == "AVAILABLE"


def test_unavailable_typed_measurement_never_falls_back_to_legacy_value():
    angles, graph = _angles_with_graph(ratio=0.2, calibrated=False)
    assert angles["metrics"]["analyse_osseuse"]["Situation_A"]["valeur"] is not None
    assert _typed_by_field(graph)["Situation_A"]["availability_status"] == "NOT_COMPUTABLE"

    projected = project_typed_craniom_read_path(angles, patient_id=7)
    output = projected["metrics"]["analyse_osseuse"]["Situation_A"]
    assert output["valeur"] is None
    assert output["availability_status"] == "NOT_COMPUTABLE"
    assert output["scientific_source"] == "EVIDENCE_GRAPH_V1"


def test_incomplete_or_wrong_patient_typed_graph_fails_closed():
    angles, graph = _angles_with_graph(ratio=None, calibrated=False)
    broken = {**angles, EVIDENCE_GRAPH_KEY: {**graph, "measurements": graph["measurements"][:-1]}}
    with pytest.raises(CephaloTypedReadError, match="incomplete"):
        project_typed_craniom_read_path(broken, patient_id=7)

    with pytest.raises(CephaloTypedReadError, match="case integrity"):
        project_typed_craniom_read_path(angles, patient_id=999)


def test_legacy_analysis_without_graph_is_copied_unchanged():
    legacy = {
        "metrics": {"analyse_osseuse": {"Situation_A": {"valeur": 12.3}}},
        "calibration_status": "verified",
    }
    projected = project_typed_craniom_read_path(legacy, patient_id=7)
    assert projected == legacy
    assert projected is not legacy
