"""Synthetic P2ter++ HTTP fixtures preserved from source tests, NO CLINICAL AUTHORITY.

Bridge-only test support: no scientific algorithm code is imported from the
unmerged R23 clinical branches. Assertions in _read are preserved verbatim;
a missing protocol or source evidence must fail, not be mocked away.
"""
from __future__ import annotations
from datetime import datetime
from backend import models
from backend.routers.documents import doc_factory
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

PATH = "/api/ia/analyses/"
PROFILES = {"mcnamara": 13, "ricketts_atlas2009": 33, "ricketts_gregoret13": 13, "com": 10}

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

def _cabinet(db, dentist):
    db.add(models.CabinetConfig(
        owner_id=dentist.id, nom_cabinet="SYNTHETIC P2BIS ONLY",
        nom_praticien="NON PATIENT",
    ))
    db.commit()

def _temporary_pdf_output(monkeypatch, tmp_path):
    # Globally constructed document factory must never write to an actual
    # cabinet's document store when this HTTP contract executes.
    monkeypatch.setattr(doc_factory.ceph_gen, "output_dir", str(tmp_path))
    monkeypatch.setattr(doc_factory, "output_dir", str(tmp_path))

