import hashlib
from datetime import datetime
from types import SimpleNamespace

from backend import models
from backend.services import document_signature_p3 as signature_service


def _doc(tmp_path, *, author_id, signer_id):
    relative = "archives/101/ORDONNANCE/2026/9/read-proof.pdf"
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    content = b"read-proof"
    path.write_bytes(content)
    return SimpleNamespace(
        file_path=f"static/{relative}",
        file_hash=hashlib.sha256(content).hexdigest(),
        file_size=len(content),
        status=models.DocumentStatus.ACTIF,
        author_practitioner_id=author_id,
        signed_by_practitioner_id=signer_id,
        signed_at=datetime(2026, 9, 12, 22, 0, 0),
    )


def test_public_read_refuses_signer_different_from_recorded_author(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    state = signature_service.verification_state_for_document(
        _doc(tmp_path, author_id=1, signer_id=2)
    )

    assert state.is_valid is False
    assert state.is_signed is False
    assert state.status_text == "Signature incohérente"
    assert "ne correspond pas" in state.warning_msg


def test_public_read_refuses_signature_without_recorded_author(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    state = signature_service.verification_state_for_document(
        _doc(tmp_path, author_id=None, signer_id=1)
    )

    assert state.is_valid is False
    assert state.is_signed is False
    assert state.status_text == "Signature incohérente"
