import pytest
from pydantic import ValidationError

from backend.schemas.documents import DocumentRequest
from backend.schemas.payments import PaymentCreate


def _document_request(status: str) -> DocumentRequest:
    return DocumentRequest(
        type="note",
        patient_id=1,
        data={
            "payments": [
                {
                    "acte": "Soin",
                    "montant": 1000.0,
                    "mode_reglement": "Espèces",
                }
            ]
        },
        payment_status=status,
    )


def test_document_flow_rejects_partial_status_without_explicit_collected_amount():
    with pytest.raises(ValidationError) as exc_info:
        _document_request("PARTIEL")

    message = str(exc_info.value)
    assert "Paiement partiel refusé" in message
    assert "montant encaissé explicite" in message


def test_document_flow_keeps_non_partial_statuses_valid():
    assert _document_request("EN_ATTENTE").payment_status == "EN_ATTENTE"
    assert _document_request("PAYE").payment_status == "PAYE"


def test_dedicated_payment_flow_requires_explicit_amount_and_method():
    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1)

    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1, amount=250.0)

    payment = PaymentCreate(patient_id=1, amount=250.0, payment_method="ESPECES")
    assert payment.amount == 250.0
    assert payment.payment_method == "ESPECES"
