import pytest
from pydantic import ValidationError

from backend.schemas.documents import DocumentRequest


def _honoraires_request(installment_amounts):
    return {
        "type": "note",
        "patient_id": 1,
        "is_accounted": True,
        "payment_status": "EN_ATTENTE",
        "data": {
            "payments": [
                {"acte": "Couronne", "montant": 700.0},
                {"acte": "Détartrage", "montant": 300.0},
            ],
            "is_global_note": True,
            "installments": [
                {"label": f"Versement {index + 1}", "amount": amount}
                for index, amount in enumerate(installment_amounts)
            ],
        },
    }


def test_global_honoraires_accepts_exact_installment_total():
    request = DocumentRequest(**_honoraires_request([333.33, 333.33, 333.34]))
    assert request.type == "note"


@pytest.mark.parametrize("amounts", [[400, 500], [600, 500]])
def test_global_honoraires_rejects_installment_total_mismatch(amounts):
    with pytest.raises(ValidationError) as exc_info:
        DocumentRequest(**_honoraires_request(amounts))

    errors = exc_info.value.errors()
    assert any(error["type"] == "installment_total_mismatch" for error in errors)


def test_global_honoraires_rejects_non_positive_installment():
    with pytest.raises(ValidationError) as exc_info:
        DocumentRequest(**_honoraires_request([0, 1000]))

    assert any(error["type"] == "installment_total_mismatch" for error in exc_info.value.errors())


def test_non_global_honoraires_does_not_require_installment_reconciliation():
    payload = _honoraires_request([400, 500])
    payload["data"]["is_global_note"] = False
    request = DocumentRequest(**payload)
    assert request.type == "note"
