"""R23-G5: REAL FastAPI/JWT + SQLite-isolated cephalometry GET -> PUT -> GET.

No real patient, file upload, hardware, OpenAI, Vercel or clinical conclusion.
A TestClient request goes through current workstation/licensing/tenant/permission
dependencies; this is not a direct handler mock.
"""
from __future__ import annotations

from datetime import datetime
from copy import deepcopy

from fastapi.routing import APIRoute

from backend import models
from backend.main import app
from backend.routers import ia
from backend.routers.cephalo_analysis_read import get_analysis_with_typed_read_path
from backend.routers.cephalo_landmark_refinement import update_analysis_with_landmark_audit
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING
from backend.tests.conftest import make_user


PATH = "/api/ia/analyses/"
PROFILES = {
    "mcnamara": 13,
    "ricketts_atlas2009": 33,
    "ricketts_gregoret13": 13,
    "com": 10,
}


def _jwt(client, dentist):
    login = client.post(
        "/api/auth/login",
        data={"username": dentist.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.status_code
    token = login.json()["access_token"]
    # GET/PUT must authenticate with an explicit desktop access JWT, not
    # an accidentally retained privileged cookie from another test identity.
    client.cookies.clear()
    return {"Authorization": f"Bearer {token}"}


def _case(db, dentist):
    patient = models.Patient(
        nom="SYNTHETIC-R23G5", prenom="NEVER-REAL",
        date_naissance=datetime(1990, 1, 1), sexe="M", employer_id=dentist.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.flush()

    points = [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    assert len(points) == 38
    result = cephalo_safe_engine.calculate_metrics(
        {p["id"]: (p["x"], p["y"]) for p in points},
        custom_mm_ratio=None,
    )
    image = "r23g5-synthetic-never-a-real-patient.jpg"
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=patient.id, image_record_id=image,
        result=result, landmarks=points, inference_mode="SOTA_ONNX_38",
        is_calibrated=False, calibration_data=None,
        case_id=f"r23g5:fake-patient:{patient.id}",
    )
    analysis = models.CephaloAnalysis(
        patient_id=patient.id, image_original_path=image,
        landmarks_data=points, angles_data={**result.model_dump(), EVIDENCE_GRAPH_KEY: graph},
        is_calibrated=False, mm_per_pixel=None,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return patient, analysis, points


def _read(client, analysis_id, headers):
    reply = client.get(PATH + str(analysis_id), headers=headers)
    assert reply.status_code == 200, reply.text[:900]
    scientific = reply.json()["angles_data"]["scientific_read_path"]
    assert scientific["authority"] == "EVIDENCE_GRAPH_V1"
    assert scientific["active_chain"] == "VERIFIED"
    assert scientific["current_landmark_count"] == 38
    for name, size in PROFILES.items():
        protocol = scientific["protocol_profiles"][name]
        assert len(protocol["rows"]) == size
        assert protocol["classification_authority"] is False
        for row in protocol["rows"]:
            assert row["classification_authority"] is False
            if row["availability_status"] != "AVAILABLE":
                assert row["value"] is None
                assert not row.get("focus_evidence")
            if row.get("focus_evidence"):
                evidence = row["focus_evidence"]
                assert row["availability_status"] == "AVAILABLE"
                assert evidence["canonical_measurement_id"] == row["canonical_measurement_id"]
                assert evidence["value_authority_method_id"] == row["value_authority_method_id"]
                assert evidence["measurement_ref"] in row["measurement_refs"]
    return reply.json(), scientific


def test_route_uniqueness_denies_legacy_handler_reactivation():
    routes = [r for r in ia.router.routes if isinstance(r, APIRoute)
              and r.path == "/analyses/{analysis_id}"]
    for method, expected in (
        ("GET", get_analysis_with_typed_read_path),
        ("PUT", update_analysis_with_landmark_audit),
    ):
        matches = [r for r in routes if method in (r.methods or set())]
        assert len(matches) == 1
        assert matches[0].endpoint is expected


def test_authenticated_get_put_get_rebuilds_active_evidence_without_norms(
    client, db, dentiste
):
    _, analysis, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    initial, path1 = _read(client, analysis.id, headers)
    assert path1["revision"] == 1
    assert initial["is_calibrated"] is False
    assert initial["mm_per_pixel"] is None
    old_refs = set(db.get(models.CephaloAnalysis, analysis.id)
                   .angles_data[EVIDENCE_GRAPH_KEY]["current_landmark_refs"])
    old_graph = deepcopy(db.get(models.CephaloAnalysis, analysis.id)
                         .angles_data[EVIDENCE_GRAPH_KEY])
    edited = deepcopy(points)
    next(p for p in edited if p["id"] == "A")["x"] += 2.0

    reply = client.put(PATH + str(analysis.id),
                       json={"landmarks": edited}, headers=headers)
    assert reply.status_code == 200, reply.text[:900]
    assert reply.json()["status"] == "success"
    db.expire_all()
    revised = db.get(models.CephaloAnalysis, analysis.id)
    graph = revised.angles_data[EVIDENCE_GRAPH_KEY]
    assert graph["revision"] == 2
    assert graph["revision_reason"] == "LANDMARK_EDIT"
    assert len(graph["current_landmark_refs"]) == 38
    assert set(graph["current_landmark_refs"]) != old_refs
    assert graph["case_id"] == old_graph["case_id"]
    assert revised.mm_per_pixel is None
    assert revised.is_calibrated is False

    response, path2 = _read(client, analysis.id, headers)
    assert path2["revision"] == 2
    assert response["landmarks_data"] == edited
    assert path2["current_landmark_count"] == 38
    assert path2["active_chain"] == "VERIFIED"

    # No coordinate change must not forge a revision or another clinician event.
    replay = client.put(PATH + str(analysis.id),
                        json={"landmarks": edited}, headers=headers)
    assert replay.status_code == 200, replay.text[:900]
    db.expire_all()
    assert db.get(models.CephaloAnalysis, analysis.id).angles_data[
        EVIDENCE_GRAPH_KEY]["revision"] == 2


def test_jwt_and_tenant_boundaries_prevent_read_write_and_mutation(
    client, db, dentiste
):
    _, analysis, points = _case(db, dentiste)
    outsider = make_user(db, email="other-r23g5@cabinet.invalid")
    route = PATH + str(analysis.id)

    client.cookies.clear()
    assert client.get(route).status_code == 401
    assert client.put(route, json={"landmarks": points}).status_code == 401
    outsider_headers = _jwt(client, outsider)
    forbidden_read = client.get(route, headers=outsider_headers)
    forbidden_write = client.put(route, headers=outsider_headers,
                                 json={"landmarks": points})
    assert forbidden_read.status_code == 403
    assert forbidden_write.status_code == 403
    db.expire_all()
    persisted = db.get(models.CephaloAnalysis, analysis.id)
    assert persisted.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 1
    assert persisted.landmarks_data == points


def test_calibration_and_tampering_fail_closed_on_real_http_paths(
    client, db, dentiste
):
    _, analysis, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    route = PATH + str(analysis.id)

    invalid_ratio = client.put(route, headers=headers,
                               json={"landmarks": points, "mm_per_pixel": 0.2})
    assert invalid_ratio.status_code == 400
    db.expire_all()
    persisted = db.get(models.CephaloAnalysis, analysis.id)
    assert persisted.mm_per_pixel is None
    assert persisted.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 1

    # This is deliberate test-only corruption, not a production path:
    # canonical GET MUST refuse inconsistent/missing active landmarks.
    corrupted = deepcopy(persisted.angles_data)
    corrupted[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] = []
    persisted.angles_data = corrupted
    db.commit()
    db.expire_all()

    response = client.get(route, headers=headers)
    assert response.status_code == 409
    assert "lecture scientifique bloquée" in response.json()["detail"]
    assert "NEVER-REAL" not in response.text
