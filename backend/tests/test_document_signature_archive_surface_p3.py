from types import SimpleNamespace

from backend import models
from backend.routers import document_provenance_p3


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self.rows)


class _DB:
    def __init__(self, docs, users):
        self.docs = docs
        self.users = users

    def query(self, model):
        if model is models.DocumentArchive:
            return _Query(self.docs)
        if model is models.User:
            return _Query(self.users)
        raise AssertionError(f"Unexpected query model: {model}")


def test_patient_archive_surface_exposes_truthful_p3_provenance_without_touching_legacy(monkeypatch):
    signed_at = __import__('datetime').datetime(2026, 9, 12, 21, 45, 0)
    doc = SimpleNamespace(
        id=7,
        author_practitioner_id=1,
        signed_by_practitioner_id=1,
        signed_at=signed_at,
    )
    user = SimpleNamespace(id=1, nom_complet="Dr Lina Alaoui", email="lina@test.local")
    db = _DB([doc], [user])

    legacy_payload = [
        {"id": "7", "name": "ordonnance.pdf", "type": "ORDONNANCE"},
        {"id": "legacy:101:old.pdf", "name": "old.pdf", "type": "LEGACY"},
    ]
    monkeypatch.setattr(
        document_provenance_p3.legacy_patients,
        "get_patient_documents",
        lambda **_kwargs: [dict(item) for item in legacy_payload],
    )

    result = document_provenance_p3.get_patient_documents_with_provenance(
        patient_id=101,
        db=db,
        current_user=SimpleNamespace(id=1),
    )

    canonical = result[0]
    assert canonical["author_practitioner_id"] == 1
    assert canonical["author_practitioner_name"] == "Dr Lina Alaoui"
    assert canonical["signed_by_practitioner_id"] == 1
    assert canonical["signed_by_practitioner_name"] == "Dr Lina Alaoui"
    assert canonical["signed_at"] == signed_at.isoformat()

    legacy = result[1]
    assert "author_practitioner_id" not in legacy
    assert "signed_by_practitioner_id" not in legacy
    assert "signed_at" not in legacy


def test_patient_document_listing_has_one_p3_route(client):
    from backend.routers import patients

    routes = [
        route for route in patients.router.routes
        if getattr(route, "path", None) == "/{patient_id}/documents"
        and "GET" in (getattr(route, "methods", set()) or set())
    ]

    assert len(routes) == 1
    assert routes[0].endpoint.__name__ == "get_patient_documents_with_provenance"
