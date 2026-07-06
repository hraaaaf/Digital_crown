"""Tests M5-A — Facturation avancée : CSV export, send-email, overdue, relance, inline edit."""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# ── fixtures helpers ──────────────────────────────────────────────────────────

VALID_PATIENT = {
    "nom": "COMPTAPATIENT",
    "prenom": "Test",
    "date_naissance": "1985-06-15",
    "sexe": "M",
    "telephone": "0600000000",
    "email": "comptapatient@test.dz",
}


def _create_patient(client, headers):
    r = client.post("/api/patients/", json=VALID_PATIENT, headers=headers)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _seed_doc_archive(db, patient_id, employer_id, payment_status="EN_ATTENTE", days_old=0):
    """Directly create a DocumentArchive in DB (bypasses file generation)."""
    from backend import models
    import uuid as _uuid

    doc = models.DocumentArchive(
        patient_id=patient_id,
        uploaded_by_id=employer_id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename=f"note_{_uuid.uuid4().hex[:8]}.pdf",
        original_filename="note.pdf",
        document_group_id=str(_uuid.uuid4()),
        version_number=1,
        is_latest_version=True,
        file_hash=_uuid.uuid4().hex,
        file_size=1024,
        file_path="/tmp/note.pdf",
        title="Consultation",
        is_accounted=True,
        payment_status=models.PaiementStatut(payment_status),
        is_collected=False,
        clinical_data={"payments": [{"acte": "Consultation", "montant": 3000.0}]},
    )
    if days_old > 0:
        doc.created_at = datetime.now() - timedelta(days=days_old)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── CSV export ────────────────────────────────────────────────────────────────

class TestExportCsv:
    def test_export_csv_returns_file(self, client, auth_headers):
        r = client.get("/api/accounting/export-csv", headers=auth_headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")

    def test_export_csv_unauthenticated(self, client):
        r = client.get("/api/accounting/export-csv")
        assert r.status_code == 401

    def test_export_csv_contains_headers(self, client, auth_headers):
        r = client.get("/api/accounting/export-csv", headers=auth_headers)
        content = r.content.decode("utf-8-sig")
        assert "Patient" in content
        assert "Montant" in content


# ── send-email ────────────────────────────────────────────────────────────────

class TestSendEmail:
    def test_send_email_no_patient_email_returns_422(self, client, db, auth_headers, dentiste):
        """Patient without email → 422."""
        from backend import models

        pat = models.Patient(
            nom="NOEMAIL", prenom="Patient",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            email=None,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id)
        r = client.post(f"/api/accounting/send-email/doc_{doc.id}", headers=auth_headers)
        assert r.status_code == 422

    def test_send_email_success(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="HASEMAIL", prenom="Patient",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            email="patient@test.dz",
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id)
        with patch("backend.services.email_service.email_service.send_email", return_value=True):
            r = client.post(f"/api/accounting/send-email/doc_{doc.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_send_email_invalid_id_returns_400(self, client, auth_headers):
        r = client.post("/api/accounting/send-email/invalid_id", headers=auth_headers)
        assert r.status_code == 400

    def test_send_email_doc_not_found_returns_404(self, client, auth_headers):
        r = client.post("/api/accounting/send-email/doc_999999", headers=auth_headers)
        assert r.status_code == 404

    def test_send_email_unauthenticated(self, client):
        r = client.post("/api/accounting/send-email/doc_1")
        assert r.status_code == 401


# ── overdue ───────────────────────────────────────────────────────────────────

class TestOverdue:
    def test_overdue_returns_empty_when_no_old_items(self, client, auth_headers):
        r = client.get("/api/accounting/overdue?days=30", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body

    def test_overdue_detects_old_unpaid_docs(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="OVERDUE", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        # Create doc that's 45 days old and unpaid
        _seed_doc_archive(db, pat.id, dentiste.id, payment_status="EN_ATTENTE", days_old=45)

        r = client.get("/api/accounting/overdue?days=30", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        ids = [i["patient_id"] for i in body["items"]]
        assert pat.id in ids

    def test_overdue_ignores_paid_docs(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="PAIDTEST", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        # 45 days old but already PAYÉ
        _seed_doc_archive(db, pat.id, dentiste.id, payment_status="PAYE", days_old=45)

        r = client.get("/api/accounting/overdue?days=30", headers=auth_headers)
        body = r.json()
        paid_ids = [i["patient_id"] for i in body["items"]]
        assert pat.id not in paid_ids

    def test_overdue_unauthenticated(self, client):
        r = client.get("/api/accounting/overdue")
        assert r.status_code == 401


# ── relance ───────────────────────────────────────────────────────────────────

class TestRelance:
    def test_relance_sends_email(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="RELANCETEST", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            email="relance@test.dz",
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id, days_old=45)
        with patch("backend.services.email_service.email_service.send_email", return_value=True):
            r = client.post(f"/api/accounting/relance/doc_{doc.id}", headers=auth_headers)
        assert r.status_code == 200

    def test_relance_no_email_returns_422(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="RELANCENOEMAIL", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            email=None,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id, days_old=45)
        r = client.post(f"/api/accounting/relance/doc_{doc.id}", headers=auth_headers)
        assert r.status_code == 422

    def test_relance_unauthenticated(self, client):
        r = client.post("/api/accounting/relance/doc_1")
        assert r.status_code == 401


# ── inline edit (PATCH /accounting/item/{item_id}) ───────────────────────────

class TestInlineEdit:
    def test_patch_doc_title(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="INLINEEDIT", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id)
        r = client.patch(
            f"/api/accounting/item/doc_{doc.id}",
            json={"title": "Nouvelle consultation"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Nouvelle consultation"

    def test_patch_empty_title_returns_422(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="EMPTYTITLE", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        doc = _seed_doc_archive(db, pat.id, dentiste.id)
        r = client.patch(
            f"/api/accounting/item/doc_{doc.id}",
            json={"title": ""},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_patch_not_found_returns_404(self, client, auth_headers):
        r = client.patch(
            "/api/accounting/item/doc_999999",
            json={"title": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_patch_invalid_prefix_returns_400(self, client, auth_headers):
        r = client.patch(
            "/api/accounting/item/invalid_123",
            json={"title": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_patch_unauthenticated(self, client):
        r = client.patch("/api/accounting/item/doc_1", json={"title": "X"})
        assert r.status_code == 401
