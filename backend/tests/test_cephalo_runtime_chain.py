"""R2 contracts for one active cephalometric runtime evidence chain."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from backend.repositories.cephalo_repository import _canonicalize_evidence_projection
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.cephalo_typed_read import CephaloTypedReadError
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 11, 9, 30, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 11, 9, 35, tzinfo=timezone.utc)
LATEST = datetime(2026, 9, 11, 9, 40, tzinfo=timezone.utc)
CASE_ID = "cephalo:r2-runtime-chain"


def _raw():
    return [{"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)} for index, name in SOTA_LANDMARKS_MAPPING.items()]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _initial_graph(raw=None):
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(patient_id=7, image_record_id="radio-r2.jpg", result=result, landmarks=raw, inference_mode="SOTA_ONNX_38", case_id=CASE_ID, recorded_at=NOW)


def _angles():
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    angles = result.model_dump()
    angles[EVIDENCE_GRAPH_KEY] = _initial_graph(raw)
    return angles


def test_unambiguous_pre_r2_snapshot_remains_readable_and_reports_verified_active_chain():
    projected = project_runtime_chain_read_path(_angles(), patient_id=7)
    assert projected["scientific_read_path"]["authority"] == "EVIDENCE_GRAPH_V1"
    assert projected["scientific_read_path"]["active_chain"] == "VERIFIED"
    assert projected["scientific_read_path"]["current_landmark_count"] == 38


def test_get_fails_closed_when_historical_landmark_makes_current_authority_ambiguous():
    angles = _angles()
    payload = angles[EVIDENCE_GRAPH_KEY]
    duplicate = deepcopy(payload["landmarks"][0])
    duplicate["evidence_id"] += ":historical"
    duplicate["origin"] = "MANUAL"
    duplicate["model_id"] = None
    duplicate["model_sha256"] = None
    duplicate["pipeline_version"] = None
    payload["landmarks"].append(duplicate)
    with pytest.raises(CephaloTypedReadError, match="active runtime chain"):
        project_runtime_chain_read_path(angles, patient_id=7)


def test_get_fails_closed_when_construction_points_to_non_current_landmark():
    angles = _angles()
    payload = angles[EVIDENCE_GRAPH_KEY]
    payload["current_landmark_refs"] = [item["evidence_id"] for item in payload["landmarks"]]
    target = next(item for item in payload["constructions"] if item["definition_id"] == "CRANIOM_A_TO_N_VERTICAL_V1")
    stale_ref = next(ref for ref in target["landmark_refs"] if ref.endswith(":A"))
    payload["current_landmark_refs"].remove(stale_ref)
    with pytest.raises(CephaloTypedReadError, match="active runtime chain"):
        project_runtime_chain_read_path(angles, patient_id=7)


def test_creation_edit_calibration_recalculation_and_get_keep_one_active_chain():
    raw = _raw()
    initial_graph = _initial_graph(raw)
    canonical = _canonicalize_evidence_projection({EVIDENCE_GRAPH_KEY: initial_graph})[EVIDENCE_GRAPH_KEY]
    assert len(canonical["current_landmark_refs"]) == 38

    edited = [dict(item) for item in raw]
    a = next(item for item in edited if item["id"] == "A")
    a["x"] += 2.0
    edit_result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(edited))
    revision2 = rebuild_evidence_after_landmark_edit(previous_payload=canonical, patient_id=7, image_record_id="radio-r2.jpg", result=edit_result, runtime_landmarks=edited, clinician_id="clinician-7", validated_at=LATER)
    assert revision2["revision_reason"] == "LANDMARK_EDIT"
    assert len(revision2["current_landmark_refs"]) == 38

    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(edited))
    revision3 = rebuild_evidence_after_manual_calibration(previous_payload=revision2, patient_id=7, image_record_id="radio-r2.jpg", result=calibrated_result, runtime_landmarks=edited, p1={"x": 0.0, "y": 0.0}, p2={"x": 0.0, "y": 50.0}, distance_mm=10.0, clinician_id="clinician-7", calibrated_at=LATEST)
    assert revision3["revision_reason"] == "MANUAL_CALIBRATION"
    assert revision3["current_landmark_refs"] == revision2["current_landmark_refs"]

    recalculated = [dict(item) for item in edited]
    b = next(item for item in recalculated if item["id"] == "B")
    b["x"] += 1.0
    recalc_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(recalculated))
    revision4 = rebuild_evidence_after_landmark_edit(previous_payload=revision3, patient_id=7, image_record_id="radio-r2.jpg", result=recalc_result, runtime_landmarks=recalculated, clinician_id="clinician-7", validated_at=LATEST)

    angles = recalc_result.model_dump()
    angles[EVIDENCE_GRAPH_KEY] = revision4
    projected = project_runtime_chain_read_path(angles, patient_id=7)
    assert projected["scientific_read_path"]["active_chain"] == "VERIFIED"
    assert projected["scientific_read_path"]["revision"] == 4
    assert projected["scientific_read_path"]["current_landmark_count"] == 38
    assert all(measurement["calibration_ref"] is not None for measurement in revision4["measurements"] if measurement["availability_status"] == "AVAILABLE" and measurement["requires_calibration"])

    craniom_angular = [measurement for measurement in revision4["measurements"] if measurement["analysis_id"] == "CRANIOM" and not measurement["requires_calibration"]]
    assert {measurement["method_id"] for measurement in craniom_angular} == {"CRANIOM_U1_FRANKFORT_DEG_V1", "CRANIOM_L1_DOWNS_DEG_V1", "CRANIOM_INTERINCISAL_DEG_V1"}
    assert all(measurement["availability_status"] == "AVAILABLE" for measurement in craniom_angular)
    assert all(measurement["calibration_ref"] is None for measurement in craniom_angular)

    steiner = [measurement for measurement in revision4["measurements"] if measurement["analysis_id"] == "STEINER"]
    assert {measurement["method_id"] for measurement in steiner} == {"STEINER_SNA_DEG_V1", "STEINER_SNB_DEG_V1", "STEINER_ANB_DEG_V1", "STEINER_U1_NA_DEG_V1", "STEINER_L1_NB_DEG_V1", "STEINER_SN_MP_DEG_V1"}
    assert all(measurement["requires_calibration"] is False for measurement in steiner)
    assert all(measurement["calibration_ref"] is None for measurement in steiner)
