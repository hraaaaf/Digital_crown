from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.routers import document_provenance_p3


def test_signature_permission_delegates_for_explicitly_mapped_type(monkeypatch):
    calls = []

    def _require(doc_type, current_user):
        calls.append((doc_type, current_user))

    monkeypatch.setattr(
        document_provenance_p3.legacy_documents,
        "require_document_permission",
        _require,
    )
    user = SimpleNamespace(id=1)

    document_provenance_p3.require_signature_document_permission("ORDONNANCE", user)

    assert calls == [("ORDONNANCE", user)]


def test_signature_permission_fails_closed_for_unmapped_bilan_type(monkeypatch):
    called = False

    def _require(_doc_type, _current_user):
        nonlocal called
        called = True

    monkeypatch.setattr(
        document_provenance_p3.legacy_documents,
        "require_document_permission",
        _require,
    )

    with pytest.raises(HTTPException) as exc_info:
        document_provenance_p3.require_signature_document_permission(
            "BILAN",
            SimpleNamespace(id=1),
        )

    assert exc_info.value.status_code == 403
    assert "sans politique de signature explicite" in str(exc_info.value.detail)
    assert called is False
