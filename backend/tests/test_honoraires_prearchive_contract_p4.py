import pytest

from backend.schemas.documents import HonorairesData, PaymentItem
from backend.services.honoraires_contract import validate_honoraires_document_data


def test_honoraires_rejects_missing_explicit_payment_method_before_pdf():
    data = HonorairesData(payments=[PaymentItem(acte="Consultation", montant=300)])
    with pytest.raises(ValueError, match="choisi explicitement"):
        validate_honoraires_document_data(data)


def test_honoraires_rejects_zero_negative_and_empty_label_before_pdf():
    for item in (
        PaymentItem(acte="Consultation", montant=0, mode_reglement="Espèces"),
        PaymentItem(acte="Consultation", montant=-10, mode_reglement="Espèces"),
        PaymentItem(acte="", montant=100, mode_reglement="Espèces"),
    ):
        with pytest.raises(ValueError):
            validate_honoraires_document_data(HonorairesData(payments=[item]))


def test_honoraires_accepts_explicit_valid_line():
    data = HonorairesData(payments=[PaymentItem(
        acte="Consultation",
        montant=300,
        mode_reglement="TPE",
    )])
    assert validate_honoraires_document_data(data) is data
