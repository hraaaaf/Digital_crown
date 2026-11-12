"""Real canonical manual-calibration endpoint + independent SQLite evidence proof.

This test intentionally invokes the endpoint registered on ia.router, *not*
the unmounted legacy function left in ia.py for code history. Synthetic data
only; no model execution, patient records, diagnostic claims, or deployment.
"""
from __future__ import annotations

import copy
import math
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.routers import ia
from backend.routers import cephalo_calibration_provenance as canonical
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def _live_route():
    routes = [
        route for route in ia.router.routes
        if isinstance(route, APIRoute)
        and route.path == "/analyses/{analysis_id}/calibrate"
        and "POST" in route.methods
    ]
    assert len(routes) == 1, "Public calibration route is missing or duplicated"
    assert routes[0].endpoint is canonical.calibrate_analysis_with_provenance, (
        "Legacy unsafe calibration handler must not be mounted"
    )
    assert routes[0].endpoint is not ia.calibrate_analysis
    return routes[0].endpoint


def _fixture_points():
    raw = [
        {"id": name, "x": float(100 + i * 2), "y": float(120 + i * 3)}
        for i, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    for point in raw:
        if point["id"] == "Pog":
            point["x"] += 8.0
        if point["id"] == "Go":
            point["y"] += 6.0
        if point["id"] == "Pog_soft":
            point["x"] += 7.0
    assert len(raw) == 38
    return raw


@pytest.fixture
def synthetic_db(monkeypatch):
    # Execute real SQLite INSERT/UPDATE/COMMIT with the exact 38-point synthetic
    # typed evidence contract that the canonical runtime expects.
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    models.CephaloAnalysis.__table__.create(engine)
    raw = _fixture_points()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(
        {p["id"]: (p["x"], p["y"]) for p in raw}
    )
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=5001,
        image_record_id="synthetic://ceph-grid",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:synthetic-manual-calibration",
    )
    initial_angles = {
        **result.model_dump(),
        "calibration_status": "unverified",
        EVIDENCE_GRAPH_KEY: graph,
        "clinical_data": {"note": "synthetic draft, not validated"},
    }
    with Session(engine) as db:
        db.add(models.CephaloAnalysis(
            id=901,
            patient_id=5001,
            image_original_path="synthetic://ceph-grid",
            landmarks_data=raw,
            angles_data=initial_angles,
            mm_per_pixel=None,
            is_calibrated=False,
            calibration_data=None,
        ))
        db.commit()
    monkeypatch.setattr(canonical, "assert_patient_access", lambda pid, user, db: (
        None if pid == 5001 and user.id == 77
        else (_ for _ in ()).throw(AssertionError("wrong synthetic patient/operator"))
    ))
    yield engine, copy.deepcopy(initial_angles)
    engine.dispose()


def _request(distance=20.0, px=100.0):
    return schemas.CalibrationRequest(
        p1={"x": 100.0, "y": 100.0},
        p2={"x": 100.0 + px, "y": 100.0},
        distance_mm=distance,
    )


def _call(engine, req):
    with Session(engine) as db:
        return _live_route()(
            901, req, db=db, current_user=SimpleNamespace(id=77)
        )


def _read(engine):
    # Every read uses a fresh independent SQLite session.
    with Session(engine) as db:
        analysis = db.get(models.CephaloAnalysis, 901)
        return {
            "ratio": analysis.mm_per_pixel,
            "flag": analysis.is_calibrated,
            "data": copy.deepcopy(analysis.calibration_data),
            "angles": copy.deepcopy(analysis.angles_data),
            "points": copy.deepcopy(analysis.landmarks_data),
        }


def test_live_router_has_one_canonical_manual_calibration_post():
    assert _live_route() is canonical.calibrate_analysis_with_provenance


def test_manual_two_point_persists_ratio_and_full_audit_on_real_sqlite(synthetic_db):
    engine, before = synthetic_db
    response = _call(engine, _request(distance=20, px=100))
    assert response == {"status": "success", "mm_per_pixel": 0.2, "is_calibrated": True}
    after = _read(engine)
    assert after["ratio"] == pytest.approx(.2)
    assert after["flag"] is True
    data = after["data"]
    assert data["method"] == "MANUAL_TWO_POINT"
    assert data["method_version"] == "1"
    assert data["p1"] == {"x": 100.0, "y": 100.0}
    assert data["p2"] == {"x": 200.0, "y": 100.0}
    assert data["distance_mm"] == pytest.approx(20.0)
    assert data["mm_per_pixel"] == pytest.approx(.2)
    assert data["calibrated_by"] == "77"
    assert data["calibrated_at"]
    assert after["points"] == _fixture_points()
    angles = after["angles"]
    assert angles["calibration_status"] == "verified"
    assert angles["clinical_data"] == before["clinical_data"]
    assert angles["analysis_metadata"]["pixel_ratio"] == pytest.approx(.2)
    assert angles[EVIDENCE_GRAPH_KEY]["revision"] == before[EVIDENCE_GRAPH_KEY]["revision"] + 1
    assert angles[EVIDENCE_GRAPH_KEY]["revision_reason"] == "MANUAL_CALIBRATION"
    assert angles[EVIDENCE_GRAPH_KEY]["history"][-1]["revision"] == 1
    calibration = [s for s in angles[EVIDENCE_GRAPH_KEY]["sources"] if s["kind"] == "calibration"]
    assert len(calibration) == 1
    assert calibration[0]["operator_id"] == "77"
    assert calibration[0]["metadata"]["distance_mm"] == 20.0
    assert calibration[0]["metadata"]["mm_per_pixel"] == pytest.approx(.2)
    before_unscaled = [m for m in before[EVIDENCE_GRAPH_KEY]["measurements"]
                       if not m["requires_calibration"]]
    after_unscaled = [m for m in angles[EVIDENCE_GRAPH_KEY]["measurements"]
                      if not m["requires_calibration"]]
    assert after_unscaled == before_unscaled, "Calibration must not mutate angular evidence"
    linear = [m for m in angles[EVIDENCE_GRAPH_KEY]["measurements"]
              if m["analysis_id"] == "CRANIOM" and m["requires_calibration"]]
    assert len(linear) == 4
    assert all(m["availability_status"] == "AVAILABLE" for m in linear)
    assert all(math.isfinite(m["value"]) for m in linear)
    assert all(m["calibration_ref"] == calibration[0]["evidence_id"] for m in linear)


@pytest.mark.parametrize("mm,px,expected", [
    (20.0, 3.0, "trop proches"),
    (0.1, 100.0, "aberrant"),
])
def test_invalid_manual_scale_is_rejected_without_any_sqlite_mutation(
    synthetic_db, mm, px, expected,
):
    engine, before = synthetic_db
    with pytest.raises(HTTPException) as err:
        _call(engine, _request(distance=mm, px=px))
    assert err.value.status_code == 400
    assert expected in str(err.value.detail)
    state = _read(engine)
    assert state["ratio"] is None
    assert state["flag"] is False
    assert state["data"] is None
    assert state["angles"] == before


@pytest.mark.parametrize("distance", [0.0, -5.0, 101.0])
def test_invalid_physical_distance_is_rejected_at_schema(distance):
    with pytest.raises(ValidationError):
        _request(distance=distance)


def test_manual_recalibration_replaces_current_source_but_keeps_history(synthetic_db):
    engine, before = synthetic_db
    _call(engine, _request(20.0, 100.0))
    prior = _read(engine)
    _call(engine, _request(25.0, 100.0))
    after = _read(engine)
    assert after["ratio"] == pytest.approx(.25)
    graph = after["angles"][EVIDENCE_GRAPH_KEY]
    assert graph["revision"] == before[EVIDENCE_GRAPH_KEY]["revision"] + 2
    assert len([s for s in graph["sources"] if s["kind"] == "calibration"]) == 1
    historic = graph["history"][-1]["sources"]
    old_cal = [s for s in historic if s["kind"] == "calibration"]
    assert len(old_cal) == 1
    assert old_cal[0]["metadata"]["mm_per_pixel"] == pytest.approx(.2)
    assert graph["revision_reason"] == "MANUAL_CALIBRATION"
    assert prior["angles"]["analysis_metadata"]["pixel_ratio"] == pytest.approx(.2)
    assert after["angles"]["analysis_metadata"]["pixel_ratio"] == pytest.approx(.25)


def test_manual_calibration_rejects_downstream_clinical_evidence_atomically(synthetic_db):
    engine, _ = synthetic_db
    with Session(engine) as db:
        a = db.get(models.CephaloAnalysis, 901)
        angles = copy.deepcopy(a.angles_data)
        angles[EVIDENCE_GRAPH_KEY]["findings"] = [{"finding_id": "synthetic-stale"}]
        a.angles_data = angles
        db.commit()
    prior = _read(engine)
    with pytest.raises(HTTPException) as err:
        _call(engine, _request())
    assert err.value.status_code == 400
    assert "downstream clinical evidence" in str(err.value.detail)
    assert _read(engine) == prior


def test_manual_calibration_rejects_mismatched_landmark_evidence_atomically(synthetic_db):
    engine, _ = synthetic_db
    with Session(engine) as db:
        a = db.get(models.CephaloAnalysis, 901)
        points = copy.deepcopy(a.landmarks_data)
        points[4]["x"] += 1
        a.landmarks_data = points
        db.commit()
    prior = _read(engine)
    with pytest.raises(HTTPException) as err:
        _call(engine, _request())
    assert err.value.status_code == 400
    assert _read(engine) == prior


def test_legacy_function_is_not_the_registered_public_endpoint():
    assert ia.calibrate_analysis is not _live_route()
