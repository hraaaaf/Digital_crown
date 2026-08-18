"""Tests routers/documents.py — list, download, archive."""
from datetime import datetime
import io


def _seed_archive(db, patient_id, employer_id):
    from backend import models
    import uuid

    doc = models.DocumentArchive(
        patient_id=patient_id,
        uploaded_by_id=employer_id,
        document_type=models.DocumentType.ORDONNANCE,
        filename=f"ord_{uuid.uuid4().hex[:8]}.pdf",
        original_filename="ordonnance.pdf",
        document_group_id=str(uuid.uuid4()),
        version_number=1,
        is_latest_version=True,
        file_hash=uuid.uuid4().hex,
        file_size=512,
        file_path="/tmp/ord.pdf",
        title="Ordonnance test",
        is_accounted=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
        is_collected=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestListDocuments:
    def test_requires_auth(self, client):
        r = client.get("/api/documents/")
        assert r.status_code == 401

    def test_returns_empty_list(self, client, auth_headers):
        r = client.get("/api/documents/", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "documents" in body
        assert "total" in body
        assert isinstance(body["documents"], list)

    def test_filters_by_patient(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="DOCSTEST", prenom="Filter",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        _seed_archive(db, pat.id, dentiste.id)

        r = client.get(
            "/api/documents/",
            params={"patient_id": pat.id},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        assert all(d["patient_id"] == pat.id for d in body["documents"])

    def test_pagination_params(self, client, auth_headers):
        r = client.get(
            "/api/documents/",
            params={"page": 1, "page_size": 5},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["page"] == 1
        assert body["page_size"] == 5

    def test_search_query(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="SEARCHTEST", prenom="Doc",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        _seed_archive(db, pat.id, dentiste.id)

        r = client.get(
            "/api/documents/",
            params={"search": "Ordonnance"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_file_exists_field_present(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="FILETEST", prenom="Exists",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        _seed_archive(db, pat.id, dentiste.id)

        r = client.get(
            "/api/documents/",
            params={"patient_id": pat.id},
            headers=auth_headers,
        )
        assert r.status_code == 200
        docs = r.json()["documents"]
        assert len(docs) >= 1
        assert "file_exists" in docs[0]


class TestDownloadDocument:
    def test_no_token_returns_401(self, client):
        r = client.get("/api/documents/999/download")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        r = client.get(
            "/api/documents/999/download",
            params={"token": "invalid.token.here"},
        )
        assert r.status_code == 401

    def test_query_token_is_rejected_even_if_valid(self, client, dentiste):
        from backend.routers.auth import SECRET_KEY, ALGORITHM
        from jose import jwt
        import time

        token = jwt.encode(
            {"sub": dentiste.email, "type": "access", "exp": int(time.time()) + 3600},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        r = client.get(
            "/api/documents/999999/download",
            params={"token": token},
        )
        assert r.status_code == 401

    def test_bearer_token_doc_not_found_returns_404(self, client, auth_headers):
        r = client.get(
            "/api/documents/999999/download",
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestArchiveDocumentEndpoint:
    def test_requires_auth(self, client):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
        r = client.post(
            "/api/documents/archive",
            params={"patient_id": 1, "doc_type": "ordonnance"},
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        )
        assert r.status_code == 401

    def test_missing_patient_returns_404(self, client, auth_headers):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
        r = client.post(
            "/api/documents/archive",
            params={"patient_id": 999999, "doc_type": "ORDONNANCE"},
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code in (403, 404)

    def test_archive_valid_patient_reaches_endpoint(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = models.Patient(
            nom="ARCHIVEPAT", prenom="Upload",
            date_naissance=datetime(1990, 6, 15),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)
        fake_pdf = io.BytesIO(b"%PDF-1.4 test content for archive")
        r = client.post(
            "/api/documents/archive",
            params={"patient_id": pat.id, "doc_type": "ORDONNANCE"},
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["document"]["download_url"] == f"/api/documents/{body['document']['id']}/download"


class TestTrashRestoreDelete:
    def _make_patient(self, db, dentiste, nom="TRASHPAT"):
        from backend import models
        pat = models.Patient(
            nom=nom, prenom="Test",
            date_naissance=datetime(1988, 8, 8),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)
        return pat

    def test_trash_requires_auth(self, client):
        r = client.post("/api/documents/1/trash")
        assert r.status_code == 401

    def test_trash_nonexistent_returns_404(self, client, auth_headers):
        r = client.post("/api/documents/999999/trash", headers=auth_headers)
        assert r.status_code == 404

    def test_trash_legacy_doc_returns_400(self, client, auth_headers):
        r = client.post("/api/documents/legacy:1:file.pdf/trash", headers=auth_headers)
        assert r.status_code == 400

    def test_trash_invalid_id_returns_400(self, client, auth_headers):
        r = client.post("/api/documents/not-a-number/trash", headers=auth_headers)
        assert r.status_code == 400

    def test_trash_and_restore(self, client, db, auth_headers, dentiste):
        pat = self._make_patient(db, dentiste, "TRASHRESTORE")
        doc = _seed_archive(db, pat.id, dentiste.id)
        r = client.post(f"/api/documents/{doc.id}/trash", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == doc.id
        r2 = client.post(f"/api/documents/{doc.id}/restore", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == doc.id

    def test_restore_requires_auth(self, client):
        r = client.post("/api/documents/1/restore")
        assert r.status_code == 401

    def test_permanent_delete_without_confirm_returns_400(self, client, auth_headers):
        r = client.delete("/api/documents/999999", headers=auth_headers)
        assert r.status_code == 400

    def test_permanent_delete_nonexistent_with_confirm_returns_404(self, client, auth_headers):
        r = client.delete("/api/documents/999999?confirm=true", headers=auth_headers)
        assert r.status_code == 404

    def test_permanent_delete_success(self, client, db, auth_headers, dentiste):
        pat = self._make_patient(db, dentiste, "PERMDELETE2")
        doc = _seed_archive(db, pat.id, dentiste.id)
        r = client.delete(f"/api/documents/{doc.id}?confirm=true", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_delete_requires_auth(self, client):
        r = client.delete("/api/documents/1?confirm=true")
        assert r.status_code == 401


class TestTrashRestoreActe:
    """L'endpoint générique /documents/{id}/trash doit aussi gérer les IDs
    'acte_<id>' (billing line venant de la Comptabilité, pas un DocumentArchive) —
    régression du bug 400 Bad Request rapporté sur la suppression d'un acte."""

    def _make_patient(self, db, dentiste, nom="ACTETRASH"):
        from backend import models
        pat = models.Patient(
            nom=nom, prenom="Test",
            date_naissance=datetime(1988, 8, 8),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)
        return pat

    def _make_acte(self, db, patient_id, praticien_id):
        from backend import models
        acte = models.Acte(
            patient_id=patient_id,
            praticien_id=praticien_id,
            type_acte=models.ActeType.SOIN,
            libelle="Détartrage",
            montant=350.0,
            is_accounted=True,
        )
        db.add(acte)
        db.commit()
        db.refresh(acte)
        return acte

    def test_trash_acte_requires_auth(self, client):
        r = client.post("/api/documents/acte_1/trash")
        assert r.status_code == 401

    def test_trash_acte_nonexistent_returns_404(self, client, auth_headers):
        r = client.post("/api/documents/acte_999999/trash", headers=auth_headers)
        assert r.status_code == 404

    def test_trash_acte_invalid_id_returns_400(self, client, auth_headers):
        r = client.post("/api/documents/acte_notanumber/trash", headers=auth_headers)
        assert r.status_code == 400

    def test_trash_acte_succeeds_and_disappears_from_honoraires(self, client, db, auth_headers, dentiste):
        pat = self._make_patient(db, dentiste)
        acte = self._make_acte(db, pat.id, dentiste.id)
        r0 = client.get("/api/accounting/honoraires", headers=auth_headers)
        assert r0.status_code == 200
        assert any(it["id"] == f"acte_{acte.id}" for it in r0.json()["items"])
        r = client.post(f"/api/documents/acte_{acte.id}/trash", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == f"acte_{acte.id}"
        db.refresh(acte)
        assert acte.deleted_at is not None
        r2 = client.get("/api/accounting/honoraires", headers=auth_headers)
        assert r2.status_code == 200
        assert not any(it["id"] == f"acte_{acte.id}" for it in r2.json()["items"])

    def test_trash_then_restore_acte(self, client, db, auth_headers, dentiste):
        pat = self._make_patient(db, dentiste, "ACTERESTORE")
        acte = self._make_acte(db, pat.id, dentiste.id)
        r = client.post(f"/api/documents/acte_{acte.id}/trash", headers=auth_headers)
        assert r.status_code == 200
        r2 = client.post(f"/api/documents/acte_{acte.id}/restore", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == f"acte_{acte.id}"
        db.refresh(acte)
        assert acte.deleted_at is None

    def test_restore_acte_not_trashed_returns_404(self, client, db, auth_headers, dentiste):
        pat = self._make_patient(db, dentiste, "ACTENOTRASH")
        acte = self._make_acte(db, pat.id, dentiste.id)
        r = client.post(f"/api/documents/acte_{acte.id}/restore", headers=auth_headers)
        assert r.status_code == 404


class TestDocumentsGenerate:
    def test_generate_requires_auth(self, client):
        r = client.post("/api/documents/generate", json={"type": "ordonnance", "patient_id": 1, "data": {}})
        assert r.status_code == 401

    def test_generate_invalid_patient_returns_error(self, client, auth_headers):
        r = client.post(
            "/api/documents/generate",
            json={"type": "ordonnance", "patient_id": 999999, "data": {"medications": []}},
            headers=auth_headers,
        )
        assert r.status_code in (403, 404, 422, 500)
