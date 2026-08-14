from datetime import datetime
from unittest.mock import patch

from backend import models


def test_installment_preview_does_not_mutate_database(
    client, db, dentiste, auth_headers, tmp_path
):
    patient = models.Patient(
        nom="PREVIEW",
        prenom="Readonly",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    pdf_path = tmp_path / "preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n% preview\n")

    plans_before = db.query(models.InstallmentPlan).count()
    installments_before = db.query(models.Installment).count()
    audit_logs_before = db.query(models.AuditLog).count()

    payload = {
        "type": "echeancier",
        "patient_id": patient.id,
        "is_accounted": False,
        "data": {
            "title": "Échéancier preview",
            "totalAmount": 1000.0,
            "items": [
                {
                    "label": "Versement 1",
                    "amount": 500.0,
                    "dueDate": "2026-09-01",
                },
                {
                    "label": "Versement 2",
                    "amount": 500.0,
                    "dueDate": "2026-10-01",
                },
            ],
        },
    }

    with patch(
        "backend.routers.documents.doc_factory.create_installment_plan",
        return_value=str(pdf_path),
    ) as create_installment_plan:
        response = client.post(
            "/api/documents/generate?preview=true",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 200, response.text
    assert db.query(models.InstallmentPlan).count() == plans_before
    assert db.query(models.Installment).count() == installments_before
    assert db.query(models.AuditLog).count() == audit_logs_before
    assert create_installment_plan.call_count == 1
    assert create_installment_plan.call_args.kwargs.get("archive") is False
