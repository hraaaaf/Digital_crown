from datetime import datetime
from unittest.mock import patch

from backend import models


def test_ordonnance_preview_is_read_only_even_when_archive_requested(
    client, db, dentiste, auth_headers, tmp_path
):
    patient = models.Patient(
        nom="PREVIEW",
        prenom="Ordonnance",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    pdf_path = tmp_path / "ordonnance-preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n% ordonnance preview\n")

    archives_before = db.query(models.DocumentArchive).count()
    audit_logs_before = db.query(models.AuditLog).count()
    payments_before = db.query(models.Payment).count()
    actes_before = db.query(models.Acte).count()

    payload = {
        "type": "ordonnance",
        "patient_id": patient.id,
        "is_accounted": False,
        "data": {
            "medications": [
                {
                    "nom": "PARACETAMOL",
                    "dosage": "1G",
                    "forme": "COMPRIMÉS",
                    "posologie": "Selon prescription du praticien",
                    "type": "MEDICAMENT",
                }
            ],
            "show_legal_annotations": True,
        },
    }

    with patch(
        "backend.routers.documents.doc_factory.create_ordonnance",
        return_value=str(pdf_path),
    ) as create_ordonnance:
        response = client.post(
            "/api/documents/generate?preview=true&archive=true",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "success"
    assert create_ordonnance.call_count == 1
    assert db.query(models.DocumentArchive).count() == archives_before
    assert db.query(models.AuditLog).count() == audit_logs_before
    assert db.query(models.Payment).count() == payments_before
    assert db.query(models.Acte).count() == actes_before
