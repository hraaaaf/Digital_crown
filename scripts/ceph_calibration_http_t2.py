"""Authenticated HTTP → canonical manual calibration → fresh SQLite proof.

Runs AFTER the successful GUI landmark drag/undo/redo E2E on a disposable T2
synthetic case. No real patient, radiograph, inference, normative interpretation,
production environment, external connection, or deployment.
"""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path

import httpx

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"
assert os.environ.get("CLOUD_AI_ENABLED") == "false"
assert Path("t2-runtime-cert.db").is_file()
assert os.environ.get("T2_PASSWORD")
seed = json.loads(os.environ["CEPH_ODF_CASE_JSON"])
assert seed.get("clinical_release") is False
assert seed.get("fixture_name") == "T2-CEPH-ODF-E2E-01"
assert type(seed.get("patient_id")) is int and type(seed.get("analysis_id")) is int

from backend import database, models
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload,
)
from backend.services.cephalo_safe_engine import cephalo_safe_engine

id_ = seed["analysis_id"]
report = {
    "schema": "CEPH_MANUAL_CALIBRATION_AUTHENTICATED_HTTP_SQLITE_V1",
    "product_head": os.environ["PRODUCT_HEAD"],
    "synthetic_only": True,
    "real_patient": False,
    "real_radiograph": False,
    "inference_executed": False,
    "clinical_release": False,
    "checks": [],
}
def check(statement, label):
    assert statement, label
    report["checks"].append(label)
    print("CEPH_CALIBRATION_REAL_HTTP_PASS " + label, flush=True)


def read():
    with database.SessionLocal() as db:
        s = db.get(models.CephaloAnalysis, id_)
        assert s is not None and s.patient_id == seed["patient_id"]
        return {
            "calibrated": s.is_calibrated,
            "ratio": s.mm_per_pixel,
            "data": copy.deepcopy(s.calibration_data),
            "angles": copy.deepcopy(s.angles_data),
            "points": copy.deepcopy(s.landmarks_data),
        }


with database.SessionLocal() as db:
    patient = db.get(models.Patient, seed["patient_id"])
    study = db.get(models.CephaloAnalysis, id_)
    assert patient is not None and patient.numero_dossier == "T2-CEPH-ODF-E2E-01"
    assert study is not None and study.patient_id == patient.id
    assert study.mm_per_pixel is None and study.is_calibrated is False
    raw = copy.deepcopy(study.landmarks_data)
    assert isinstance(raw, list) and len(raw) == 38
    assert len({p["id"] for p in raw}) == 38
    point_map = {p["id"]: (p["x"], p["y"]) for p in raw}
    result = cephalo_safe_engine.calculate_metrics(point_map, custom_mm_ratio=None)
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=patient.id,
        image_record_id=study.image_original_path,
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=f"cephalo:synthetic-http-calibration:{study.id}",
    )
    assert graph["revision"] == 1
    angles = result.model_dump()
    angles["calibration_status"] = "unverified"
    angles[EVIDENCE_GRAPH_KEY] = graph
    study.angles_data = angles
    study.calibration_data = None
    study.mm_per_pixel = None
    study.is_calibrated = False
    db.commit()

start = read()
check(start["ratio"] is None and start["angles"][EVIDENCE_GRAPH_KEY]["revision"] == 1,
      "UNCALIBRATED_TYPED_CASE_READY")

path = f"/api/ia/analyses/{id_}/calibrate"
with httpx.Client(base_url="http://127.0.0.1:8005", timeout=35.0) as client:
    login = client.post("/api/auth/login", data={
        "username": "t2-browser@cabinet.ma",
        "password": os.environ["T2_PASSWORD"],
    })
    check(login.status_code == 200, "AUTHENTICATED_LOGIN_HTTP_200")
    bearer = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {bearer}"}

    def submit(distance_mm, pixels):
        return client.post(path, headers=headers, json={
            "p1": {"x": 100, "y": 100},
            "p2": {"x": 100 + pixels, "y": 100},
            "distance_mm": distance_mm,
        })

    for label, distance, px in [
        ("PIXELS_TOO_CLOSE_400", 20, 3),
        ("ABERRANT_RATIO_400", .1, 100),
        ("NEGATIVE_DISTANCE_422", -1, 100),
    ]:
        response = submit(distance, px)
        expected = 422 if label.endswith("422") else 400
        check(response.status_code == expected, label)
        after_reject = read()
        check(after_reject == start, label + "_ATOMIC_DB_UNCHANGED")

    first = submit(20, 100)
    check(first.status_code == 200, "MANUAL_CALIBRATION_AUTHENTICATED_POST_200")
    check(first.json()["mm_per_pixel"] == .2, "MANUAL_RATIO_0_2")
    saved = read()
    check(saved["calibrated"] is True and math.isclose(saved["ratio"], .2),
          "RATIO_PERSISTED_FRESH_SQLITE")
    data = saved["data"]
    check(data is not None and data["method"] == "MANUAL_TWO_POINT"
          and data["p1"] == {"x": 100, "y": 100}
          and data["p2"] == {"x": 200, "y": 100}
          and data["distance_mm"] == 20 and data["calibrated_by"],
          "TWO_POINT_AUDIT_PERSISTED")
    graph = saved["angles"][EVIDENCE_GRAPH_KEY]
    check(graph["revision"] == 2 and graph["revision_reason"] == "MANUAL_CALIBRATION",
          "ATOMIC_TYPED_REVISION_2")
    sources = [s for s in graph["sources"] if s["kind"] == "calibration"]
    check(len(sources) == 1 and sources[0]["operator_id"] == data["calibrated_by"],
          "SCIENTIFIC_SOURCE_BOUNDS_CLINICIAN")
    linear = [m for m in graph["measurements"]
              if m["analysis_id"] == "CRANIOM" and m["requires_calibration"]]
    check(len(linear) == 4
          and all(m["calibration_ref"] == sources[0]["evidence_id"]
                  and m["availability_status"] == "AVAILABLE" for m in linear),
          "LINEAR_MM_RECOMPUTED_AND_EVIDENCE_LINKED")
    get = client.get(f"/api/ia/analyses/{id_}", headers=headers)
    check(get.status_code == 200, "CANONICAL_HTTP_GET_200_AFTER_CALIBRATION")
    body = get.json()
    check(body["mm_per_pixel"] == .2 and body["is_calibrated"] is True,
          "REAL_HTTP_FRESH_GET_PERSISTS_SCALE")

    recalibrated = submit(25, 100)
    check(recalibrated.status_code == 200 and recalibrated.json()["mm_per_pixel"] == .25,
          "AUTHENTICATED_RECALIBRATION_POST_200")
    newer = read()
    next_graph = newer["angles"][EVIDENCE_GRAPH_KEY]
    old_sources = [s for s in next_graph["history"][-1]["sources"] if s["kind"] == "calibration"]
    current_sources = [s for s in next_graph["sources"] if s["kind"] == "calibration"]
    check(next_graph["revision"] == 3 and len(old_sources) == len(current_sources) == 1
          and old_sources[0]["metadata"]["mm_per_pixel"] == .2
          and current_sources[0]["metadata"]["mm_per_pixel"] == .25,
          "RECALIBRATION_REVISION_AND_HISTORY")
    check(newer["ratio"] == .25 and newer["data"]["distance_mm"] == 25,
          "RECALIBRATION_FRESH_SQLITE_RATIO_AND_METHOD")
    check(newer["points"] == start["points"], "LANDMARKS_UNCHANGED_BY_CALIBRATION")
    check(not any(next_graph.get(key) for key in [
        "diagnoses", "treatment_options", "validations", "final_plans",
    ]), "NO_AUTONOMOUS_MEDICAL_CONCLUSIONS")

report["final_status"] = "CANONICAL_AUTHENTICATED_MANUAL_HTTP_SQLITE_PASS_NONCLINICAL"
output = Path("artifacts/ceph-odf-gui-sqlite-e2e/calibration-http-report.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("CEPH_CALIBRATION_REAL_HTTP_FINAL " + report["final_status"], flush=True)
