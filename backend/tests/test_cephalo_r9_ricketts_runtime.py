from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.repositories.cephalo_repository import _canonicalize_evidence_projection
from backend.services.cephalo_auto_calibration_gate import AutoCalibrationState, ValidatedFiducialProfile, evaluate_auto_calibration
from backend.services.cephalo_auto_calibration_transition import rebuild_evidence_after_auto_calibration
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 12, 8, 5, tzinfo=timezone.utc)
LATEST = datetime(2026, 9, 12, 8, 10, tzinfo=timezone.utc)
CASE_ID = "cephalo:r9-ricketts-runtime"


def _raw():
    raw = [{"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)} for index, name in SOTA_LANDMARKS_MAPPING.items()]
    overrides = {
        "Po": (0.0, 0.0), "Or": (10.0, 0.0), "N": (4.0, 0.0), "Pog": (6.0, 10.0),
        "Go": (0.0, 12.0), "Me": (10.0, 12.0), "Ba": (-6.0, 0.0), "PT_point": (2.0, 4.0),
        "A": (8.0, 4.0), "Prn": (5.0, -5.0), "Pog_soft": (9.0, 10.0),
        "Ls_soft": (10.0, 2.0), "Li_soft": (5.0, 5.0),
    }
    for item in raw:
        if item["id"] in overrides:
            item["x"], item["y"] = overrides[item["id"]]
    return raw


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _initial(raw=None):
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(
        patient_id=7, image_record_id="radio-r9.jpg", result=result,
        landmarks=raw, inference_mode="SOTA_ONNX_38", case_id=CASE_ID, recorded_at=NOW,
    )


def _ricketts(graph, *, calibrated: bool):
    items = [item for item in graph["measurements"] if item["analysis_id"] == "RICKETTS"]
    by_method = {item["method_id"]: item for item in items}
    assert set(by_method) == {
        "RICKETTS_FACIAL_DEPTH_DEG_V1",
        "RICKETTS_CONVEXITY_A_NPOG_MM_V1", "RICKETTS_E_LINE_LS_MM_V1", "RICKETTS_E_LINE_LI_MM_V1",
    }
    assert "RICKETTS_FACIAL_AXIS_DEG_V1" not in by_method
    depth = by_method["RICKETTS_FACIAL_DEPTH_DEG_V1"]
    assert depth["availability_status"] == "AVAILABLE"
    assert depth["requires_calibration"] is False
    assert depth["calibration_ref"] is None
    assert depth["value"] is not None
    for method in ("RICKETTS_CONVEXITY_A_NPOG_MM_V1", "RICKETTS_E_LINE_LS_MM_V1", "RICKETTS_E_LINE_LI_MM_V1"):
        item = by_method[method]
        assert item["requires_calibration"] is True
        if calibrated:
            assert item["availability_status"] == "AVAILABLE"
            assert item["calibration_ref"] is not None
            assert item["value"] is not None
        else:
            assert item["availability_status"] == "NOT_COMPUTABLE"
            assert item["calibration_ref"] is None
            assert item["value"] is None
    return by_method


def _auto_decision():
    candidate = CalibrationCandidate.from_ticks(axis_x_px=40, tick_positions_y_px=[10, 35, 60, 85, 110])
    profile = ValidatedFiducialProfile(
        profile_id="R9_TEST_RULER", version="1", known_tick_spacing_mm=5.0,
        min_ticks=5, max_spacing_deviation_ratio=0.05,
        validation_reference="test-fixture://r9-ricketts-ruler-v1",
    )
    decision = evaluate_auto_calibration(candidate, profile=profile)
    assert decision.state is AutoCalibrationState.AUTO_VERIFIED
    assert decision.mm_per_pixel == pytest.approx(0.2)
    return decision


def test_ricketts_creation_edit_manual_calibration_edit_and_read_path():
    raw = _raw()
    initial = _initial(raw)
    initial_ricketts = _ricketts(initial, calibrated=False)
    canonical = _canonicalize_evidence_projection({EVIDENCE_GRAPH_KEY: initial})[EVIDENCE_GRAPH_KEY]

    edited = [dict(item) for item in raw]
    next(item for item in edited if item["id"] == "Pog")["x"] += 1.0
    edit_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    revision2 = rebuild_evidence_after_landmark_edit(
        previous_payload=canonical, patient_id=7, image_record_id="radio-r9.jpg",
        result=edit_result, runtime_landmarks=edited, clinician_id="clinician-r9", validated_at=LATER,
    )
    edited_ricketts = _ricketts(revision2, calibrated=False)
    assert edited_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"]["value"] != pytest.approx(initial_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"]["value"])

    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(edited))
    revision3 = rebuild_evidence_after_manual_calibration(
        previous_payload=revision2, patient_id=7, image_record_id="radio-r9.jpg",
        result=calibrated_result, runtime_landmarks=edited,
        p1={"x": 0.0, "y": 0.0}, p2={"x": 0.0, "y": 50.0}, distance_mm=10.0,
        clinician_id="clinician-r9", calibrated_at=LATEST,
    )
    calibrated_ricketts = _ricketts(revision3, calibrated=True)
    assert calibrated_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"] == edited_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"]

    recalculated = [dict(item) for item in edited]
    next(item for item in recalculated if item["id"] == "Ls_soft")["x"] += 1.0
    recalc_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(recalculated))
    revision4 = rebuild_evidence_after_landmark_edit(
        previous_payload=revision3, patient_id=7, image_record_id="radio-r9.jpg",
        result=recalc_result, runtime_landmarks=recalculated, clinician_id="clinician-r9", validated_at=LATEST,
    )
    recalculated_ricketts = _ricketts(revision4, calibrated=True)
    assert recalculated_ricketts["RICKETTS_E_LINE_LS_MM_V1"]["value"] != pytest.approx(calibrated_ricketts["RICKETTS_E_LINE_LS_MM_V1"]["value"])
    assert recalculated_ricketts["RICKETTS_E_LINE_LI_MM_V1"]["value"] == pytest.approx(calibrated_ricketts["RICKETTS_E_LINE_LI_MM_V1"]["value"])

    angles = recalc_result.model_dump(); angles[EVIDENCE_GRAPH_KEY] = revision4
    projected = project_runtime_chain_read_path(angles, patient_id=7)
    assert projected["scientific_read_path"]["active_chain"] == "VERIFIED"
    assert projected["scientific_read_path"]["revision"] == 4
    _ricketts(projected[EVIDENCE_GRAPH_KEY], calibrated=True)


def test_ricketts_auto_calibration_unlocks_linear_measurements_and_preserves_depth():
    raw = _raw(); initial = _initial(raw); initial_ricketts = _ricketts(initial, calibrated=False)
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    calibrated = rebuild_evidence_after_auto_calibration(
        previous_payload=initial, patient_id=7, image_record_id="radio-r9.jpg",
        result=result, runtime_landmarks=raw, decision=_auto_decision(), calibrated_at=LATER,
    )
    auto_ricketts = _ricketts(calibrated, calibrated=True)
    assert auto_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"] == initial_ricketts["RICKETTS_FACIAL_DEPTH_DEG_V1"]
    assert calibrated["revision_reason"] == "AUTO_CALIBRATION"
