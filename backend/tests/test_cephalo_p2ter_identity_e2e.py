"""P2ter selected-study PDF identity tests — synthetic HTTP/JWT and binary PDF.

No clinical patient data, no Cabinet DB, no real archive store. Database runs
under conftest StaticPool; SQLite does NOT certify PostgreSQL row locking.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import re

import fitz

from backend import models
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_document_identity import analysis_source_revision
from backend.routers.documents import doc_factory
from backend.tests.test_cephalo_r23g5_authenticated_api import _case, _jwt


def _compact(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", value).lower()


def _pdf_text(result):
    assert result.status_code == 200, result.text[:750]
    assert result.content.startswith(b"%PDF")
    with fitz.open(stream=result.content, filetype="pdf") as pdf:
        assert len(pdf) >= 1
        return "\n".join(page.get_text() for page in pdf)


def _setup(db, dentiste, monkeypatch, tmp_path):
    monkeypatch.setattr(doc_factory.ceph_gen, "output_dir", str(tmp_path))
    monkeypatch.setattr(doc_factory, "output_dir", str(tmp_path))
    db.add(models.CabinetConfig(
        owner_id=dentiste.id, nom_cabinet="P2TER SYNTHETIC",
        nom_praticien="NO REAL PATIENT",
    ))
    db.commit()
    patient, a, points = _case(db, dentiste)
    b_points = deepcopy(points)
    next(point for point in b_points if point["id"] == "A")["x"] += 7
    b_result = cephalo_safe_engine.calculate_metrics(
        {point["id"]: (point["x"], point["y"]) for point in b_points},
        custom_mm_ratio=None,
    )
    b_image = "p2ter-synthetic-study-B.jpg"
    b_graph = build_cephalo_runtime_evidence_payload(
        patient_id=patient.id, image_record_id=b_image,
        result=b_result, landmarks=b_points,
        inference_mode="SOTA_ONNX_38", is_calibrated=False,
        calibration_data=None, case_id=f"p2ter:synthetic-B:{patient.id}",
    )
    b = models.CephaloAnalysis(
        patient_id=patient.id, image_original_path=b_image,
        landmarks_data=b_points, angles_data={**b_result.model_dump(), EVIDENCE_GRAPH_KEY: b_graph},
        is_calibrated=False, mm_per_pixel=None,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    assert a.id != b.id
    return patient, a, b


def _body(patient, study):
    return {
        "patient_id": patient.id,
        "analysis_id": study.id,
        "source_revision": analysis_source_revision(study),
        "archive": False,
    }


def test_select_a_even_if_b_newer_and_binary_is_study_bound(
    client, db, dentiste, monkeypatch, tmp_path
):
    patient, a, b = _setup(db, dentiste, monkeypatch, tmp_path)
    headers = _jwt(client, dentiste)
    assert b.id > a.id

    for study, other in ((a, b), (b, a)):
        payload = _body(patient, study)
        rendered = _pdf_text(client.post(
            f"/api/patients/{patient.id}/pdf", json=payload, headers=headers))
        assert f"Analysis ID: {study.id}" in rendered, rendered[:1200]
        assert _compact(payload["source_revision"]) in _compact(rendered)
        expected_ref = hashlib.sha256(study.image_original_path.encode()).hexdigest()
        assert expected_ref in _compact(rendered)
        unwanted_ref = hashlib.sha256(other.image_original_path.encode()).hexdigest()
        assert unwanted_ref not in _compact(rendered)
    # Same-second concurrent export names must not collide.
    assert len(list(tmp_path.glob("*.pdf"))) == 2


def test_negative_identity_and_revision_http_paths_fail_without_pdf(
    client, db, dentiste, monkeypatch, tmp_path
):
    patient, a, b = _setup(db, dentiste, monkeypatch, tmp_path)
    headers = _jwt(client, dentiste)
    route = f"/api/patients/{patient.id}/pdf"
    legacy_route = f"/api/documents/patients/{patient.id}/report"
    ok = _body(patient, a)

    for endpoint in (route, legacy_route):
        for payload, expected in (
            ({}, 422),
            ({"patient_id": patient.id, "source_revision": ok["source_revision"]}, 422),
            ({**ok, "analysis_id": 999999999}, 404),
            ({**ok, "analysis_id": -3}, 422),
            ({**ok, "patient_id": patient.id + 10000}, 422),
            ({**ok, "analysis_id": b.id}, 409),
            ({**ok, "source_revision": "sha256:" + "0" * 64}, 409),
        ):
            reply = client.post(endpoint, json=payload, headers=headers)
            assert reply.status_code == expected, (endpoint, payload, reply.text[:500])
    assert list(tmp_path.glob("*.pdf")) == []

    assert client.get(f"/api/patients/{patient.id}/cephalo-validation", headers=headers).status_code == 422
    assert client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": a.id, "source_revision": "sha256:" + "0" * 64},
        headers=headers,
    ).status_code == 409
    checked = client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": a.id, "source_revision": ok["source_revision"]},
        headers=headers,
    )
    assert checked.status_code == 200, checked.text[:500]
    assert checked.json()["document_identity"]["analysis_id"] == a.id


def test_other_patient_tenant_no_jwt_and_stale_chain_are_denied(
    client, db, dentiste, monkeypatch, tmp_path
):
    patient, a, b = _setup(db, dentiste, monkeypatch, tmp_path)
    h = _jwt(client, dentiste)
    body = _body(patient, a)
    client.cookies.clear()
    assert client.post(f"/api/patients/{patient.id}/pdf", json=body).status_code == 401

    other = models.Patient(
        nom="SYNTHETIC-OTHER", prenom="NEVER-REAL",
        date_naissance=patient.date_naissance, sexe="M",
        employer_id=dentiste.id,
    )
    db.add(other)
    db.commit()
    assert client.post(f"/api/patients/{other.id}/pdf", json={
        **body, "patient_id": other.id,
    }, headers=h).status_code == 404
    assert list(tmp_path.glob("*.pdf")) == []

    # Fresh client snapshot becomes stale after a persisted edit in another tab.
    old = analysis_source_revision(a)
    changed = deepcopy(a.angles_data)
    changed["p2ter_documentary_marker"] = "different-persisted-revision"
    a.angles_data = changed
    db.commit()
    db.refresh(a)
    assert old != analysis_source_revision(a)
    assert client.post(f"/api/patients/{patient.id}/pdf", json={
        **body, "source_revision": old,
    }, headers=h).status_code == 409

    # A cryptographically matching revision still cannot authorize a corrupt graph.
    broken = deepcopy(a.angles_data)
    broken[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] = []
    a.angles_data = broken
    db.commit()
    db.refresh(a)
    invalid = client.post(f"/api/patients/{patient.id}/pdf", json={
        **body, "source_revision": analysis_source_revision(a),
    }, headers=h)
    assert invalid.status_code == 409, invalid.text[:500]
    assert list(tmp_path.glob("*.pdf")) == []


def test_archiving_keeps_identity_and_reopens_exact_bytes(
    client, db, dentiste, monkeypatch, tmp_path
):
    from backend.services import archive_service
    patient, a, b = _setup(db, dentiste, monkeypatch, tmp_path)
    archive_root = tmp_path / "synthetic-archives"
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", archive_root)
    h = _jwt(client, dentiste)
    body = {**_body(patient, a), "archive": True}
    result = client.post(f"/api/patients/{patient.id}/pdf", json=body, headers=h)
    rendered = _pdf_text(result)
    assert f"Analysis ID: {a.id}" in rendered
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).one()
    assert doc.analysis_id == a.id
    assert doc.clinical_data["cephalo_document_identity"]["source_revision"] == body["source_revision"]
    assert doc.clinical_data["cephalo_document_identity"]["analysis_id"] == a.id
    saved = archive_root / doc.file_path.split("static/archives/", 1)[1]
    assert saved.is_file()
    assert saved.read_bytes() == result.content
    with fitz.open(stream=saved.read_bytes(), filetype="pdf") as archived:
        assert f"Analysis ID: {a.id}" in "\n".join(page.get_text() for page in archived)
