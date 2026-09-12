from __future__ import annotations

import hashlib
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import models
from backend.services import document_signature_p3 as signature_service
from backend.services.document_signature_p3 import (
    sign_document,
    verification_state_for_document,
    verify_document_integrity,
)


class _DB:
    def __init__(self):
        self.commit_count = 0
        self.refresh_count = 0

    def commit(self):
        self.commit_count += 1

    def refresh(self, _obj):
        self.refresh_count += 1


class _User(SimpleNamespace):
    def get_employer_id(self) -> int:
        return self.employer_id if self.employer_id is not None else self.id


def _user(
    user_id: int = 1,
    *,
    role=models.UserRole.DENTISTE,
    employer_id=None,
    active=True,
    approval=models.ApprovalStatus.APPROVED.value,
):
    return _User(
        id=user_id,
        role=role,
        employer_id=employer_id,
        is_active=active,
        approval_status=approval,
    )


def _document(tmp_path, *, content=b"exact-pdf-bytes", author_id=1, status=models.DocumentStatus.ACTIF):
    relative = "archives/101/ORDONNANCE/2026/9/document.pdf"
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return SimpleNamespace(
        id=7,
        patient_id=101,
        file_path=f"static/{relative}",
        file_hash=hashlib.sha256(content).hexdigest(),
        file_size=len(content),
        status=status,
        author_practitioner_id=author_id,
        signed_by_practitioner_id=None,
        signed_at=None,
    ), path


def test_integrity_is_bound_to_exact_physical_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    doc, path = _document(tmp_path)

    assert verify_document_integrity(doc) == (True, "OK")

    path.write_bytes(b"tampered")
    ok, reason = verify_document_integrity(doc)
    assert ok is False
    assert "SHA-256" in reason


def test_public_verification_distinguishes_unsigned_signed_and_tampered(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    doc, path = _document(tmp_path)

    unsigned = verification_state_for_document(doc)
    assert unsigned.is_valid is True
    assert unsigned.is_signed is False
    assert unsigned.status_text == "Authentique • Non signé"

    doc.signed_by_practitioner_id = 1
    doc.signed_at = datetime(2026, 9, 12, 20, 0, 0)
    signed = verification_state_for_document(doc)
    assert signed.is_valid is True
    assert signed.is_signed is True
    assert signed.status_text == "Authentique & Signé"

    path.write_bytes(b"tampered")
    tampered = verification_state_for_document(doc)
    assert tampered.is_valid is False
    assert tampered.is_signed is False
    assert tampered.status_text == "Intégrité non vérifiée"


def test_public_verification_rejects_incomplete_signature_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    doc, _ = _document(tmp_path)
    doc.signed_by_practitioner_id = 1
    doc.signed_at = None

    state = verification_state_for_document(doc)
    assert state.is_valid is False
    assert state.status_text == "Signature incohérente"


def test_public_verification_rejects_non_active_document(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    doc, _ = _document(tmp_path, status=models.DocumentStatus.SUPPRIME)

    state = verification_state_for_document(doc)
    assert state.is_valid is False
    assert state.status_text == "Document non actif / invalide"


def test_author_can_sign_exact_active_bytes_once(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    doc, _ = _document(tmp_path, author_id=1)
    user = _user(1)
    db = _DB()

    signed = sign_document(db, doc, user)
    assert signed.signed_by_practitioner_id == 1
    assert signed.signed_at is not None
    first_signed_at = signed.signed_at
    assert db.commit_count == 1
    assert db.refresh_count == 1

    # Idempotence: a second click returns the same proof timestamp.
    signed_again = sign_document(db, doc, user)
    assert signed_again.signed_at == first_signed_at
    assert db.commit_count == 1


def test_signature_refuses_non_author_and_legacy_unknown_author(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    db = _DB()

    other_author_doc, _ = _document(tmp_path, author_id=2)
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, other_author_doc, _user(1))
    assert exc_info.value.status_code == 403

    legacy_doc, _ = _document(tmp_path, author_id=None)
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, legacy_doc, _user(1))
    assert exc_info.value.status_code == 409


def test_signature_refuses_non_practitioner_inactive_trashed_or_tampered(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    db = _DB()

    doc, _ = _document(tmp_path, author_id=1)
    secretary = _user(1, role=models.UserRole.SECRETAIRE)
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, doc, secretary)
    assert exc_info.value.status_code == 403

    inactive = _user(1, active=False)
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, doc, inactive)
    assert exc_info.value.status_code == 403

    trashed, _ = _document(tmp_path, author_id=1, status=models.DocumentStatus.SUPPRIME)
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, trashed, _user(1))
    assert exc_info.value.status_code == 409

    tampered, tampered_path = _document(tmp_path, author_id=1, content=b"original")
    tampered_path.write_bytes(b"changed-after-archive")
    with pytest.raises(HTTPException) as exc_info:
        sign_document(db, tampered, _user(1))
    assert exc_info.value.status_code == 409
    assert "SHA-256" in str(exc_info.value.detail)


def test_p3_signature_and_public_verification_routes_are_unique(client):
    from backend.routers import documents, verification

    sign_routes = [
        route for route in documents.router.routes
        if getattr(route, "path", None) == "/{document_id}/sign"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]
    verify_routes = [
        route for route in verification.router.routes
        if getattr(route, "path", None) == "/verify/{doc_id}"
        and "GET" in (getattr(route, "methods", set()) or set())
    ]

    assert len(sign_routes) == 1
    assert sign_routes[0].endpoint.__name__ == "sign_document_with_provenance"
    assert len(verify_routes) == 1
    assert verify_routes[0].endpoint.__name__ == "verify_document_with_p3_signature"
