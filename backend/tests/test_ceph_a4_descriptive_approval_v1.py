"""Synthetic-only S2B: exact PDF review -> local immutable archive.

Tests both the stateless HMAC proof and the authenticated FastAPI / real SQLite
path. No patient identity, clinic secret, model inference, or cloud egress.
"""
from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import models
from backend.services import cephalo_a4_approval_v1 as approval
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.p2ter_bridge_synthetic_support import (
    _cabinet, _case, _jwt, _temporary_pdf_output,
)


def _actor(user_id=41, role=models.UserRole.DENTISTE):
    return SimpleNamespace(
        id=user_id, role=role, employer_id=None, is_active=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
        get_employer_id=lambda: user_id,
    )


def _ticket(user, pdf=b"%PDF-1.4\nSYNTHETIC\n%%EOF", now=500):
    hash_ = hashlib.sha256(pdf).hexdigest()
    token = approval.make_approval_token(
        user=user, patient_id=101, analysis_id=202, revision=3,
        source_sha256="a" * 64, pdf_sha256=hash_,
        pdf_length=len(pdf), now=now,
    )
    return token, pdf


def _verify(token, pdf, user=None, now=500, **extra):
    return approval.verify_approval_token(
        token, user=user or _actor(), patient_id=extra.get("patient_id", 101),
        analysis_id=202, revision=extra.get("revision", 3),
        source_sha256=extra.get("source_sha256", "a" * 64), pdf=pdf, now=now,
    )


def test_authorized_exact_bytes_and_bound_claims_reusable_in_review_window():
    token, pdf = _ticket(_actor())
    claims = _verify(token, pdf)
    assert claims["pdf_sha256"] == hashlib.sha256(pdf).hexdigest()
    assert claims["cabinet_id"] == 41
    assert _verify(token, pdf, now=501) == claims


@pytest.mark.parametrize("mutation", [
    "pdf", "tampered_token", "changed_patient", "changed_revision",
    "changed_science", "other_user", "expired", "future",
])
def test_unsigned_or_stale_approval_is_rejected(mutation):
    user = _actor()
    token, pdf = _ticket(user)
    kwargs = {}
    now = 500
    if mutation == "pdf": pdf += b"tampered"
    if mutation == "tampered_token": token = token[:-1] + ("a" if token[-1] != "a" else "b")
    if mutation == "changed_patient": kwargs["patient_id"] = 102
    if mutation == "changed_revision": kwargs["revision"] = 4
    if mutation == "changed_science": kwargs["source_sha256"] = "b" * 64
    if mutation == "other_user": user = _actor(user_id=42)
    if mutation == "expired": now = 500 + approval.TOKEN_SECONDS + 1
    if mutation == "future": now = 460
    with pytest.raises(HTTPException) as error:
        _verify(token, pdf, user=user, now=now, **kwargs)
    assert error.value.status_code == 409


def test_admin_cannot_approve_even_with_valid_pdf():
    with pytest.raises(HTTPException) as error:
        _ticket(_actor(role=models.UserRole.ADMIN))
    assert error.value.status_code == 403


def test_pdf_decoder_rejects_garbage_and_oversize():
    with pytest.raises(HTTPException):
        approval.decode_pdf("not-base64~")
    with pytest.raises(HTTPException):
        approval.decode_pdf("a" * (approval.MAX_PDF_BYTES * 4 // 3 + 100))


def _calibrated_case(client, db, dentist):
    patient, study, points = _case(db, dentist)
    headers = _jwt(client, dentist)
    calibrated = client.post(
        f"/api/ia/analyses/{study.id}/calibrate",
        json={
            "p1": {"x": 100.0, "y": 100.0},
            "p2": {"x": 200.0, "y": 100.0},
            "distance_mm": 20.0,
        },
        headers=headers,
    )
    assert calibrated.status_code == 200, calibrated.text[:500]
    db.refresh(study)
    assert study.is_calibrated is True
    assert study.mm_per_pixel == pytest.approx(0.2)
    return patient, study, points, headers


def _environment(monkeypatch, tmp_path):
    from backend.services import archive_service, document_signature_p3
    _temporary_pdf_output(monkeypatch, tmp_path)
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    monkeypatch.setattr(document_signature_p3, "MEDIA_DIR", tmp_path)
    monkeypatch.setattr(archive_service, "MEDIA_DIR", tmp_path)
    monkeypatch.setattr(archive_service, "LEGACY_DOCS_DIR", tmp_path / "documents")


def _prepare(client, patient, study, headers):
    revision = study.angles_data[EVIDENCE_GRAPH_KEY]["revision"]
    response = client.post(
        f"/api/patients/{patient.id}/cephalo-a4/prepare",
        json={"analysis_id": study.id, "expected_revision": revision},
        headers=headers,
    )
    return revision, response


def test_real_authenticated_prepare_archive_replay_and_exact_sqlite_proof(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _environment(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, points, headers = _calibrated_case(client, db, dentiste)
    revision, prepared = _prepare(client, patient, study, headers)
    assert prepared.status_code == 200, prepared.text[:600]
    candidate = prepared.json()
    assert candidate["expected_revision"] == revision
    assert candidate["document_kind"] == approval.VERSION
    assert candidate["clinical_diagnosis_validated"] is False
    assert candidate["practitioner_name"] == dentiste.nom_complet
    assert candidate["cabinet_stamp_name"] == "SYNTHETIC P2BIS ONLY"
    pdf = base64.b64decode(candidate["pdf_base64"], validate=True)
    assert pdf.startswith(b"%PDF")
    assert hashlib.sha256(pdf).hexdigest() == candidate["pdf_sha256"]
    assert not list(tmp_path.glob("*.pdf")), "No abandoned unapproved PDF"
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0

    import fitz
    with fitz.open(stream=pdf, filetype="pdf") as document:
        pages = "\n".join(page.get_text() for page in document)
    assert "DESCRIPTIF" in pages
    assert "Dr. Test" in pages
    assert "SYNTHETIC P2BIS ONLY" in pages
    assert "PLAN DE TRAITEMENT" not in pages
    assert "DIAGNOSTIC FINAL" not in pages
    assert "BROUILLON" not in pages

    payload = {
        "analysis_id": study.id, "expected_revision": revision,
        "approval_token": candidate["approval_token"],
        "pdf_base64": candidate["pdf_base64"], "approved": True,
    }
    target = f"/api/patients/{patient.id}/cephalo-a4/archive"
    saved = client.post(target, json=payload, headers=headers)
    assert saved.status_code == 200, saved.text[:500] if saved.status_code != 200 else ""
    assert saved.content == pdf
    assert saved.headers["x-cephalo-archive-replayed"] == "false"
    rows = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.file_hash == candidate["pdf_sha256"]
    assert row.file_size == len(pdf)
    assert row.clinical_data["approved_by_practitioner_id"] == dentiste.id
    assert row.clinical_data["scientific_source_sha256"]
    assert row.clinical_data["document_kind"] == approval.VERSION
    assert row.clinical_data["clinical_diagnosis_validated"] is False
    assert row.author_practitioner_id == dentiste.id
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "CEPH_A4_DESCRIPTIVE_APPROVED",
        models.AuditLog.resource_id == str(study.id),
    ).count() == 1

    again = client.post(target, json=payload, headers=headers)
    assert again.status_code == 200
    assert again.headers["x-cephalo-archive-replayed"] == "true"
    assert again.content == pdf
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 1

    from backend.services.cephalo_document_lock import verified_official_archive_bytes
    assert verified_official_archive_bytes(row, db) == pdf


def test_authenticated_rejection_without_validation_and_on_pdf_tamper(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _environment(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, points, headers = _calibrated_case(client, db, dentiste)
    revision, prepared = _prepare(client, patient, study, headers)
    assert prepared.status_code == 200
    data = prepared.json()
    payload = {
        "analysis_id": study.id, "expected_revision": revision,
        "approval_token": data["approval_token"],
        "pdf_base64": data["pdf_base64"],
        "approved": False,
    }
    target = f"/api/patients/{patient.id}/cephalo-a4/archive"
    refused = client.post(target, json=payload, headers=headers)
    assert refused.status_code == 422
    payload["approved"] = True
    original = base64.b64decode(payload["pdf_base64"])
    payload["pdf_base64"] = base64.b64encode(original + b"TAMPERED").decode()
    corrupted = client.post(target, json=payload, headers=headers)
    assert corrupted.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0


def test_revision_changed_after_preview_fails_closed_no_archive(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _environment(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, points, headers = _calibrated_case(client, db, dentiste)
    revision, prepared = _prepare(client, patient, study, headers)
    assert prepared.status_code == 200
    payload = {
        "analysis_id": study.id, "expected_revision": revision,
        "approval_token": prepared.json()["approval_token"],
        "pdf_base64": prepared.json()["pdf_base64"], "approved": True,
    }
    # A persisted calibration/source edit must invalidate the prior preview.
    calibrated = client.post(
        f"/api/ia/analyses/{study.id}/calibrate",
        json={
            "p1": {"x": 100.0, "y": 100.0},
            "p2": {"x": 200.0, "y": 100.0},
            "distance_mm": 25.0,
        },
        headers=headers,
    )
    assert calibrated.status_code == 200, calibrated.text[:350]
    rejected = client.post(
        f"/api/patients/{patient.id}/cephalo-a4/archive",
        json=payload, headers=headers,
    )
    assert rejected.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0
