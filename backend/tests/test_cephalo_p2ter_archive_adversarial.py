"""P2ter++ first-pass A: adversarial HTTP regressions on synthetic patient/archives.

Exercises the *generic* upload and download routes, not only the official replay.
"""
from __future__ import annotations

from types import SimpleNamespace

from backend import models
from backend.tests.test_cephalo_r23g5_authenticated_api import _case, _jwt
from backend.tests.test_cephalo_p2bis_http_pdf_continuity import _cabinet, _temporary_pdf_output


def _setup_official(client, db, dentiste, monkeypatch, tmp_path):
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service

    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _: SimpleNamespace(is_valid=True, fatals=[], warnings=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    headers = _jwt(client, dentiste)
    endpoint = f"/api/patients/{patient.id}/pdf"
    payload = {"analysis_id": study.id, "expected_revision": 1, "archive": True}
    response = client.post(endpoint, json=payload, headers=headers)
    assert response.status_code == 200, response.text[:300] if response.status_code != 200 else ""
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).one()
    return patient, study, headers, payload, doc, response.content


def test_s1_generic_autre_same_sha_cannot_overwrite_or_version_official(
    client, db, dentiste, monkeypatch, tmp_path,
):
    patient, study, headers, payload, doc, official_pdf = _setup_official(
        client, db, dentiste, monkeypatch, tmp_path,
    )
    original = (doc.file_hash, doc.file_path, doc.analysis_id, dict(doc.clinical_data))
    for resolution in ("OVERWRITE", "CREATE_VERSION"):
        upload = client.post(
            "/api/documents/archive",
            params={"patient_id": patient.id, "doc_type": "AUTRE", "on_conflict": resolution},
            files={"file": ("external.pdf", official_pdf, "application/pdf")},
            headers=headers,
        )
        assert upload.status_code == 409, (resolution, upload.status_code, upload.text[:250])
        db.refresh(doc)
        assert (doc.file_hash, doc.file_path, doc.analysis_id, doc.clinical_data) == original
        assert db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient.id,
            models.DocumentArchive.document_type == models.DocumentType.AUTRE,
        ).count() == 0
        assert client.post(
            f"/api/patients/{patient.id}/pdf", json=payload, headers=headers,
        ).content == official_pdf


def test_s2_generic_archive_rejects_filename_path_traversal_http(
    client, db, dentiste, monkeypatch, tmp_path,
):
    from backend.services import archive_service

    _cabinet(db, dentiste)
    patient, _, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    outside = tmp_path / "escape.pdf"
    outside.write_bytes(b"UNMODIFIED-SYNTHETIC")
    for malicious in ("../../../../../../escape.pdf", "..\\escape.pdf", "/tmp/escape.pdf", "report.pdf:alternate", "CON.pdf", "file?.pdf"):
        result = client.post(
            "/api/documents/archive",
            params={"patient_id": patient.id, "doc_type": "AUTRE"},
            files={"file": (malicious, b"%PDF-SYNTHETIC-CORRUPTION", "application/pdf")},
            headers=headers,
        )
        assert result.status_code == 400, (malicious, result.status_code, result.text[:250])
        assert outside.read_bytes() == b"UNMODIFIED-SYNTHETIC"
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
    ).count() == 0


def test_s3_official_pdf_download_routes_serve_verified_bytes_only(
    client, db, dentiste, monkeypatch, tmp_path,
):
    patient, study, headers, _, doc, official_pdf = _setup_official(
        client, db, dentiste, monkeypatch, tmp_path,
    )
    download = f"/api/documents/{doc.id}/download"
    static = "/api/static/archives/" + doc.file_path.removeprefix("static/archives/")
    for route in (download, static):
        response = client.get(route, headers=headers)
        assert response.status_code == 200, (route, response.status_code, response.text[:200])
        assert response.content == official_pdf
    file_path = tmp_path / "archives" / doc.file_path.removeprefix("static/archives/")
    file_path.write_bytes(official_pdf + b" TAMPERED")
    for route in (download, static):
        response = client.get(route, headers=headers)
        assert response.status_code == 409, (route, response.status_code, response.text[:200])


def test_s4_trashed_official_revision_cannot_be_restored_over_active_duplicate(
    client, db, dentiste, monkeypatch, tmp_path,
):
    patient, study, headers, payload, doc, _ = _setup_official(
        client, db, dentiste, monkeypatch, tmp_path,
    )
    doc_id = doc.id
    old_path = tmp_path / "archives" / doc.file_path.removeprefix("static/archives/")
    old_pdf = old_path.read_bytes()
    trashed = client.post(f"/api/documents/{doc_id}/trash", headers=headers)
    assert trashed.status_code == 200, trashed.text[:250]
    replacement = client.post(
        f"/api/patients/{patient.id}/pdf", json=payload, headers=headers,
    )
    assert replacement.status_code == 200, replacement.text[:250] if replacement.status_code != 200 else ""
    # Re-archiving a trashed revision must not overwrite its physical bytes.
    assert old_path.read_bytes() == old_pdf
    restored = client.post(f"/api/documents/{doc_id}/restore", headers=headers)
    assert restored.status_code == 409, restored.text[:250]
    db.expire_all()
    active = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).all()
    assert len(active) == 1
    assert active[0].id != doc_id
    assert active[0].file_path != doc.file_path
