"""CEPH-BILAN-A4-SIGNATURE-01 S1 — synthetic security-first contract.

PASS: existing P3 generic signing / tamper refusals and the unsigned CEPh hold.
XFAIL(strict): missing CEPh-specific boundaries; DO NOT treat as a signed A4.

This is a characterisation gate, NOT a clinical or signing feature. No real
patient, migration, media, network, treatment plan, or runtime changes.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import models
from backend.services import document_signature_p3 as p3


ROOT = Path(__file__).resolve().parents[2]
_MISSING = pytest.mark.xfail(
    strict=True,
    reason="S1 EXPECTED RED: no CEPh-specific exact-PDF attestation + study revision gate",
)


class _User(SimpleNamespace):
    def get_employer_id(self) -> int:
        return self.employer_id if self.employer_id is not None else self.id


class _DB:
    def __init__(self, *, current_scientific_revision=3):
        self.commits = 0
        self.refreshes = 0
        self.current_scientific_revision = current_scientific_revision

    def commit(self):
        self.commits += 1

    def refresh(self, _):
        self.refreshes += 1


def _user(user_id=41):
    return _User(
        id=user_id, role=models.UserRole.DENTISTE, employer_id=None,
        is_active=True, approval_status=models.ApprovalStatus.APPROVED.value,
    )


def _doc(tmp_path, *, kind=models.DocumentType.RAPPORT_CEPHALO, author=41,
         data=None, payload=b"%PDF-1.4\n% SYNTHETIC-ONLY\n%%EOF\n"):
    relative = "archives/101/SYNTHETIC/document.pdf"
    file_path = tmp_path / relative
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(payload)
    doc = SimpleNamespace(
        id=8001, patient_id=101, analysis_id=303,
        document_type=kind, status=models.DocumentStatus.ACTIF,
        file_path=f"static/{relative}",
        file_hash=hashlib.sha256(payload).hexdigest(),
        file_size=len(payload), author_practitioner_id=author,
        signed_by_practitioner_id=None, signed_at=None,
        clinical_data=data if data is not None else {
            "cephalo_analysis_id": 303, "cephalo_analysis_revision": 3,
        },
    )
    return doc, file_path


# Existing behaviour to preserve (green): P3 is not broken by Ceph test-first.

def test_existing_ceph_unsigned_archive_and_r14_gates_remain_closed():
    patients = (ROOT / "backend/routers/patients.py").read_text(encoding="utf-8")
    studio = (ROOT / "backend/services/cephalo_r15_clinical_studio.py").read_text(encoding="utf-8")
    report = (ROOT / "backend/services/generators/cephalo_four_part_report.py").read_text(encoding="utf-8")
    assert "BROUILLON NON SIGNÉ" in patients
    assert "Utiliser archive=false" in patients
    assert '"clinical_validation_available": False' in studio
    assert "BROUILLON — NON SIGNÉ" in report


def test_p3_still_signs_exact_bytes_of_ordinary_document_once(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path, kind=models.DocumentType.ORDONNANCE)
    db = _DB()
    first = p3.sign_document(db, doc, _user())
    assert first.signed_by_practitioner_id == 41
    assert first.signed_at is not None
    assert db.commits == 1
    assert p3.sign_document(db, doc, _user()).signed_at == first.signed_at
    assert db.commits == 1


def test_p3_refuses_byte_tampering_without_write(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, pdf = _doc(tmp_path, kind=models.DocumentType.ORDONNANCE)
    pdf.write_bytes(b"%PDF-1.4\nTAMPERED\n")
    db = _DB()
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 409
    assert db.commits == 0


def test_p3_refuses_foreign_author_without_write(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path, kind=models.DocumentType.ORDONNANCE, author=99)
    db = _DB()
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 403
    assert db.commits == 0


# Missing Ceph-specific gates (expected RED) — these must become real PASS in S2.

@_MISSING
def test_ceph_pdf_cannot_be_signed_without_exact_review_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path)
    db = _DB()
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 409
    assert db.commits == 0


@_MISSING
def test_ceph_pdf_stale_scientific_revision_must_refuse_without_write(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path, data={
        "cephalo_analysis_id": 303,
        "cephalo_analysis_revision": 2,
        "descriptive_document_attestation_v1": {
            "scientific_revision": 2,
            "reviewed_pdf_sha256": "a" * 64,
        },
    })
    db = _DB(current_scientific_revision=3)
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 409
    assert db.commits == 0


@_MISSING
def test_ceph_pdf_unmatched_preview_sha256_must_refuse(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path, data={
        "cephalo_analysis_id": 303,
        "cephalo_analysis_revision": 3,
        "descriptive_document_attestation_v1": {
            "scientific_revision": 3,
            "reviewed_pdf_sha256": "f" * 64,
        },
    })
    assert doc.file_hash != "f" * 64
    db = _DB()
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 409
    assert db.commits == 0


@_MISSING
def test_ceph_pdf_must_reject_unvetted_diagnostic_or_treatment_text(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path, data={
        "cephalo_analysis_id": 303,
        "cephalo_analysis_revision": 3,
        "ai_diagnostic": "SYNTHETIC_UNAPPROVED_DIAGNOSIS",
        "treatment_plan": "SYNTHETIC_UNAPPROVED_PLAN",
    })
    db = _DB()
    with pytest.raises(HTTPException) as failure:
        p3.sign_document(db, doc, _user())
    assert failure.value.status_code == 409
    assert db.commits == 0


@_MISSING
def test_ceph_public_verifier_must_not_claim_signed_without_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(p3, "MEDIA_DIR", tmp_path)
    doc, _ = _doc(tmp_path)
    doc.signed_by_practitioner_id = 41
    doc.signed_at = datetime(2026, 11, 12, 11, 23)
    state = p3.verification_state_for_document(doc)
    assert state.is_valid is False
    assert state.is_signed is False
