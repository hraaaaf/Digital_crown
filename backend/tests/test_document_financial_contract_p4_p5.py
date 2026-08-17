import pytest
from pydantic import ValidationError

from backend.schemas.documents import DocumentRequest, PaymentItem


def test_document_payment_status_is_closed():
    with pytest.raises(ValidationError):
        DocumentRequest(type="note", patient_id=1, payment_status="INCONNU", data={
            "payments": [{"acte": "Consultation", "montant": 300, "mode_reglement": "Espèces"}],
        })


def test_honoraires_method_is_required_only_for_real_collection():
    pending = DocumentRequest(type="note", patient_id=1, payment_status="EN_ATTENTE", data={
        "payments": [{"acte": "Consultation", "montant": 300}],
    })
    assert pending.payment_status == "EN_ATTENTE"
    assert "mode_reglement" not in pending.data["payments"][0]

    pending_with_stale_frontend_method = DocumentRequest(
        type="note",
        patient_id=1,
        payment_status="EN_ATTENTE",
        data={"payments": [{"acte": "Consultation", "montant": 300, "mode_reglement": "Espèces"}]},
    )
    assert "mode_reglement" not in pending_with_stale_frontend_method.data["payments"][0]

    with pytest.raises(ValidationError) as missing_method:
        DocumentRequest(type="note", patient_id=1, payment_status="PAYE", data={
            "payments": [{"acte": "Consultation", "montant": 300}],
        })
    assert any(error["type"] == "honoraires_payment_method_required" for error in missing_method.value.errors())

    paid = DocumentRequest(type="note", patient_id=1, payment_status="PAYE", data={
        "payments": [{"acte": "Consultation", "montant": 300, "mode_reglement": "CARTE"}],
    })
    assert paid.payment_status == "PAYE"
    assert paid.data["payments"][0]["mode_reglement"] == "CARTE"


def test_payment_item_has_no_implicit_cash_default():
    item = PaymentItem(acte="Consultation", montant=300)
    assert item.mode_reglement == ""


def test_honoraires_request_rejects_invalid_amount_even_without_collection():
    with pytest.raises(ValidationError) as zero_amount:
        DocumentRequest(type="note", patient_id=1, payment_status="EN_ATTENTE", data={
            "payments": [{"acte": "Consultation", "montant": 0}],
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
