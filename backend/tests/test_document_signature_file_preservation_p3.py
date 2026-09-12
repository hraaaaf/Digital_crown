import hashlib
from types import SimpleNamespace

from backend import models
from backend.services import document_signature_p3 as signature_service


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


def test_recording_signature_preserves_exact_archived_bytes_hash_and_size(tmp_path, monkeypatch):
    monkeypatch.setattr(signature_service, "MEDIA_DIR", tmp_path)
    relative = "archives/101/ORDONNANCE/2026/9/preserved.pdf"
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    original = b"immutable-local-pdf-bytes"
    path.write_bytes(original)
    original_hash = hashlib.sha256(original).hexdigest()

    doc = SimpleNamespace(
        file_path=f"static/{relative}",
        file_hash=original_hash,
        file_size=len(original),
        status=models.DocumentStatus.ACTIF,
        author_practitioner_id=1,
        signed_by_practitioner_id=None,
        signed_at=None,
    )
    user = _User(
        id=1,
        employer_id=None,
        role=models.UserRole.DENTISTE,
        is_active=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
    )
    db = _DB()

    signature_service.sign_document(db, doc, user)

    assert path.read_bytes() == original
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash
    assert doc.file_hash == original_hash
    assert doc.file_size == len(original)
    assert doc.signed_by_practitioner_id == 1
    assert doc.signed_at is not None
    assert db.commit_count == 1
    assert db.refresh_count == 1
