"""Contract tests for the canonical provenance-aware calibration route."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend import schemas
from backend.routers.cephalo_calibration_provenance import calibrate_analysis_with_provenance
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def _raw():
    raw = [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    for item in raw:
        if item["id"] == "Pog":
            item["x"] += 8.0
        elif item["id"] == "Go":
            item["y"] += 6.0
        elif item["id"] == "Pog_soft":
            item["x"] += 7.0
    return raw


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _initial_graph(raw):
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:route-test",
    )


def _db_for(analysis):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = analysis
    return db


def _request():
    return schemas.CalibrationRequest(
        p1=schemas.CalibrationPoint(x=0.0, y=0.0),
        p2=schemas.CalibrationPoint(x=0.0, y=50.0),
        distance_mm=10.0,
    )


def test_route_persists_operator_timestamp_and_typed_calibration_atomically(monkeypatch):
    raw = _raw()
    initial_graph = _initial_graph(raw)
    previous_independent = {
        (item["analysis_id"], item["method_id"]): (
            item["availability_status"], item["value"]
        )
        for item in initial_graph["measurements"]
        if not item["requires_calibration"]
    }
    analysis = SimpleNamespace(
        id=42,
        patient_id=7,
        image_original_path="radio.jpg",
        landmarks_data=raw,
        angles_data={EVIDENCE_GRAPH_KEY: initial_graph, "clinical_data": {"note": "keep"}},
        mm_per_pixel=None,
        is_calibrated=False,
        calibration_data=None,
    )
    db = _db_for(analysis)
    monkeypatch.setattr(
        "backend.routers.cephalo_calibration_provenance.assert_patient_access",
        lambda *_args, **_kwargs: None,
    )

    response = calibrate_analysis_with_provenance(
        42,
        _request(),
        db=db,
        current_user=SimpleNamespace(id=99),
    )

    assert response["status"] == "success"
    assert response["mm_per_pixel"] == 0.2
    assert analysis.is_calibrated is True
    assert analysis.calibration_data["method"] == "MANUAL_TWO_POINT"
    assert analysis.calibration_data["method_version"] == "1"
    assert analysis.calibration_data["calibrated_by"] == "99"
    assert analysis.calibration_data["calibrated_at"]
    assert analysis.angles_data["clinical_data"] == {"note": "keep"}
    assert analysis.angles_data["calibration_status"] == "verified"

    evidence = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    assert evidence["revision"] == 2
    calibration = [item for item in evidence["sources"] if item["kind"] == "calibration"]
    assert len(calibration) == 1
    assert calibration[0]["operator_id"] == "99"
    calibrated_measurements = [
        item for item in evidence["measurements"] if item["requires_calibration"]
    ]
    assert calibrated_measurements
    assert all(
        item["availability_status"] == "AVAILABLE"
        for item in calibrated_measurements
    )
    assert {
        (item["analysis_id"], item["method_id"]): (
            item["availability_status"], item["value"]
        )
        for item in evidence["measurements"]
        if not item["requires_calibration"]
    } == previous_independent
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_legacy_analysis_calibrates_without_fabricating_evidence_graph(monkeypatch):
    raw = _raw()
    analysis = SimpleNamespace(
        id=43,
        patient_id=7,
        image_original_path="legacy-radio.jpg",
        landmarks_data=raw,
        angles_data={"clinical_data": {"note": "legacy"}},
        mm_per_pixel=None,
        is_calibrated=False,
        calibration_data=None,
    )
    db = _db_for(analysis)
    monkeypatch.setattr(
        "backend.routers.cephalo_calibration_provenance.assert_patient_access",
        lambda *_args, **_kwargs: None,
    )

    calibrate_analysis_with_provenance(
        43,
        _request(),
        db=db,
        current_user=SimpleNamespace(id=99),
    )

    assert analysis.calibration_data["calibrated_by"] == "99"
    assert EVIDENCE_GRAPH_KEY not in analysis.angles_data
    assert analysis.angles_data["clinical_data"] == {"note": "legacy"}
    db.commit.assert_called_once()
