import pytest
from pydantic import ValidationError

from backend.schemas.documents import DocumentRequest


def test_document_payment_status_is_closed():
    with pytest.raises(ValidationError):
        DocumentRequest(type="note", patient_id=1, payment_status="INCONNU", data={
            "payments": [{"acte": "Consultation", "montant": 300, "mode_reglement": "Espèces"}],
        })


def test_honoraires_request_requires_explicit_method_and_positive_amount():
    with pytest.raises(ValidationError) as missing_method:
        DocumentRequest(type="note", patient_id=1, data={
            "payments": [{"acte": "Consultation", "montant": 300}],
        })
    assert any(error["type"] == "honoraires_payment_method_required" for error in missing_method.value.errors())

    with pytest.raises(ValidationError) as zero_amount:
        DocumentRequest(type="note", patient_id=1, data={
            "payments": [{"acte": "Consultation", "montant": 0, "mode_reglement": "Espèces"}],
        })
    assert any(error["type"] == "honoraires_invalid_amount" for error in zero_amount.value.errors())


def test_direct_echeancier_requires_exact_total_and_explicit_dates():
    valid = DocumentRequest(type="echeancier", patient_id=1, data={
        "title": "Plan",
        "totalAmount": 1000,
        "items": [
            {"label": "A", "amount": 500, "dueDate": "2026-09-01"},
            {"label": "B", "amount": 500, "dueDate": "2026-10-01"},
        ],
    })
    assert valid.type == "echeancier"

    with pytest.raises(ValidationError) as mismatch:
        DocumentRequest(type="echeancier", patient_id=1, data={
            "title": "Plan",
            "totalAmount": 1000,
            "items": [{"label": "A", "amount": 900, "dueDate": "2026-09-01"}],
        })
    assert any(error["type"] == "installment_total_mismatch" for error in mismatch.value.errors())

    with pytest.raises(ValidationError) as missing_date:
        DocumentRequest(type="echeancier", patient_id=1, data={
            "title": "Plan",
            "totalAmount": 1000,
            "items": [{"label": "A", "amount": 1000}],
        })
    assert any(error["type"] == "installment_date_required" for error in missing_date.value.errors())
