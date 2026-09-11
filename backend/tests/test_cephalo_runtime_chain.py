"""R2 contracts for one active cephalometric runtime evidence chain."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.cephalo_typed_read import CephaloTypedReadError
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 11, 9, 30, tzinfo=timezone.utc)
CASE_ID = "cephalo:r2-runtime-chain"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _angles():
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    angles = result.model_dump()
    angles[EVIDENCE_GRAPH_KEY] = graph
    return angles


def test_unambiguous_pre_r2_snapshot_remains_readable_and_reports_verified_active_chain():
    projected = project_runtime_chain_read_path(_angles(), patient_id=7)

    assert projected["scientific_read_path"]["authority"] == "EVIDENCE_GRAPH_V1"
    assert projected["scientific_read_path"]["active_chain"] == "VERIFIED"
    assert projected["scientific_read_path"]["current_landmark_count"] == 38
    assert projected["scientific_read_path"]["current_construction_count"] == 4
    assert projected["scientific_read_path"]["current_measurement_count"] == 4


def test_get_fails_closed_when_historical_landmark_makes_current_authority_ambiguous():
    angles = _angles()
    payload = angles[EVIDENCE_GRAPH_KEY]
    duplicate = deepcopy(payload["landmarks"][0])
    duplicate["evidence_id"] = duplicate["evidence_id"] + ":historical"
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

    target = next(
        item for item in payload["constructions"]
        if item["definition_id"] == "CRANIOM_A_TO_N_VERTICAL_V1"
    )
    stale_ref = next(ref for ref in target["landmark_refs"] if ref.endswith(":A"))
    payload["current_landmark_refs"].remove(stale_ref)

    with pytest.raises(CephaloTypedReadError, match="active runtime chain"):
        project_runtime_chain_read_path(angles, patient_id=7)
