"""CEPH-CALIBRATION-E2E-01: actual SQLite manual calibration boundary.

Synthetic geometry only. Fail closed if a historical endpoint returns an
apparent success without persisting auditable physical-source provenance and
a coherently versioned recomputation. No patient/clinical use.
"""
import copy
import math
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.routers import ia


@pytest.fixture()
def synthetic_db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    models.CephaloAnalysis.__table__.create(engine)
    original = {
        "calibration_status": "unverified",
        "_evidence_graph_v1": {
            "schema_version": "CEPHALO_EVIDENCE_V1",
            "case_id": "cephalo:synthetic-calibration",
            "revision": 2,
            "sources": [],
            "landmarks": [],
            "constructions": [],
            "measurements": [],
        },
        "metrics": {"linear_mm": {"availability_status": "UNAVAILABLE"}},
    }
    with Session(engine) as db:
        db.add(models.CephaloAnalysis(
            id=901, patient_id=5001, image_original_path="synthetic://grid",
            landmarks_data=[{"id": "S", "x": 10.0, "y": 20.0}],
            angles_data=copy.deepcopy(original),
            is_calibrated=False, mm_per_pixel=None, calibration_data=None,
        ))
        db.commit()
    monkeypatch.setattr(ia, "assert_patient_access", lambda patient_id, user, db: (
        None if patient_id == 5001 else (_ for _ in ()).throw(AssertionError("wrong patient"))
    ))
    yield engine, original
    engine.dispose()


def _request(distance=20.0, px=100.0):
    return schemas.CalibrationRequest(
        p1={"x": 100.0, "y": 100.0},
        p2={"x": 100.0 + px, "y": 100.0},
        distance_mm=distance,
    )


def _call(engine, req):
    with Session(engine) as db:
        return ia.calibrate_analysis(
            901, req, db=db, current_user=SimpleNamespace(id=77)
        )


def _read(engine):
    with Session(engine) as db:
        a = db.get(models.CephaloAnalysis, 901)
        return {
            "ratio": a.mm_per_pixel,
            "flag": a.is_calibrated,
            "data": copy.deepcopy(a.calibration_data),
            "angles": copy.deepcopy(a.angles_data),
        }


def test_synthetic_manual_ratio_persists_across_fresh_sqlite_session(synthetic_db):
    engine, _ = synthetic_db
    r = _call(engine, _request(distance=20, px=100))
    assert r["status"] == "success"
    state = _read(engine)
    assert r["mm_per_pixel"] == pytest.approx(0.2)
    assert state["ratio"] == pytest.approx(0.2)
    assert state["flag"] is True


@pytest.mark.parametrize("dist,px,expected", [
    (20.0, 3.0, "trop proches"),
    (0.1, 100.0, "aberrant"),
])
def test_invalid_manual_scale_is_rejected_without_sqlite_mutation(synthetic_db, dist, px, expected):
    engine, original = synthetic_db
    with pytest.raises(HTTPException) as err:
        _call(engine, _request(distance=dist, px=px))
    assert err.value.status_code == 400
    assert expected in str(err.value.detail)
    state = _read(engine)
    assert state["ratio"] is None
    assert state["flag"] is False
    assert state["angles"] == original


@pytest.mark.parametrize("distance", [0.0, -5.0, 101.0])
def test_invalid_physical_distance_is_rejected_at_schema(distance):
    with pytest.raises(ValidationError):
        _request(distance=distance)


def test_manual_scale_requires_auditable_source_and_scientific_recalculation(synthetic_db):
    """Acceptance gate: this must FAIL if legacy manual route only sets ratio."""
    engine, before = synthetic_db
    _call(engine, _request(distance=20.0, px=100.0))
    state = _read(engine)
    assert state["ratio"] == pytest.approx(0.2)
    assert state["data"] is not None, (
        "NO-GO: manual calibration returned success without persistent "
        "two-point physical-source provenance"
    )
    assert state["data"].get("method") == "MANUAL_TWO_POINT"
    assert state["data"].get("p1") == {"x": 100.0, "y": 100.0}
    assert state["data"].get("p2") == {"x": 200.0, "y": 100.0}
    assert state["data"].get("distance_mm") == pytest.approx(20.0)
    graph = state["angles"].get("_evidence_graph_v1")
    assert graph is not None and graph["revision"] == before["_evidence_graph_v1"]["revision"] + 1, (
        "NO-GO: physical scale changed without scientific revision"
    )
    assert state["angles"].get("calibration_status") in {"verified", "manual_verified"}
    assert state["angles"].get("metrics") != before["metrics"], (
        "NO-GO: metrics were not recomputed after a physical scale transition"
    )
