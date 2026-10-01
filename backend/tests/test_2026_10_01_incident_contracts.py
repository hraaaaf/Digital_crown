"""Regression contracts for the 2026-10-01 accounting/document incidents."""
from datetime import datetime


def _patient(db, dentiste, *, email="patient@example.test"):
    from backend import models

    patient = models.Patient(
        nom="INCIDENT",
        prenom="Regression",
        date_naissance=datetime(1980, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
        email=email,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def test_encaisser_rejects_malformed_typed_id_without_500(client, auth_headers):
    response = client.post(
        "/api/accounting/encaisser/doc_acte_356",
        json={"payment_method": "ESPECES"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_encaisser_requires_explicit_payment_method(client, auth_headers):
    response = client.post(
        "/api/accounting/encaisser/doc_999999",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_encaisser_acte_is_idempotency_guarded(client, db, auth_headers, dentiste):
    from backend import models

    patient = _patient(db, dentiste)
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Détartrage",
        montant=500.0,
        is_accounted=True,
        is_collected=False,
    )
    db.add(acte)
    db.commit()
    db.refresh(acte)

    first = client.post(
        f"/api/accounting/encaisser/acte_{acte.id}",
        json={"payment_method": "CARTE"},
        headers=auth_headers,
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/api/accounting/encaisser/acte_{acte.id}",
        json={"payment_method": "CARTE"},
        headers=auth_headers,
    )
    assert second.status_code == 409
    assert db.query(models.Payment).filter(models.Payment.acte_id == acte.id).count() == 1


def test_send_email_uses_real_typed_id_and_attaches_pdf(
    client, db, auth_headers, dentiste, tmp_path, monkeypatch
):
    from backend import models
    from backend.services.email_service import email_service

    patient = _patient(db, dentiste)
    pdf_path = tmp_path / "note.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n% regression fixture\n")

    doc = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename="note.pdf",
        original_filename="note.pdf",
        document_group_id="incident-email-regression",
        version_number=1,
        is_latest_version=True,
        file_hash="incident-email-regression",
        file_size=pdf_path.stat().st_size,
        file_path=str(pdf_path),
        title="Note d'honoraires",
        is_accounted=True,
        payment_status=models.PaiementStatut.EN_ATTENTE,
        is_collected=False,
        clinical_data={"payments": [{"montant": 500.0}]},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    captured = {}

    def fake_send_email(to_email, subject, text, html=None, attachments=None):
        captured["to_email"] = to_email
        captured["attachments"] = attachments
        return True

    monkeypatch.setattr(email_service, "send_email", fake_send_email)

    response = client.post(
        f"/api/accounting/send-email/doc_{doc.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert captured["to_email"] == patient.email
    assert captured["attachments"]
    filename, payload, content_type = captured["attachments"][0]
    assert filename == "note.pdf"
    assert payload.startswith(b"%PDF")
    assert content_type == "application/pdf"


def test_send_email_rejects_double_prefixed_id_without_500(client, auth_headers):
    response = client.post(
        "/api/accounting/send-email/doc_acte_356",
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_document_download_rejects_typed_accounting_id_without_500(client, auth_headers):
    response = client.get(
        "/api/documents/acte_356/download",
        headers=auth_headers,
    )
    assert response.status_code == 400
