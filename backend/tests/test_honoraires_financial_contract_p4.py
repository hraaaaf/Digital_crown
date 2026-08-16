import math

import pytest

from backend.services.honoraires_persistence import (
    _validated_honoraires_item,
    normalize_document_payment_method,
)


def test_honoraires_requires_explicit_positive_line():
    with pytest.raises(ValueError, match="acte explicite"):
        _validated_honoraires_item({"acte": "  ", "montant": 100})

    for value in (0, -1, float("nan"), float("inf"), 1_000_001):
        with pytest.raises(ValueError):
            _validated_honoraires_item({"acte": "Consultation", "montant": value})


def test_honoraires_accepts_valid_line():
    label, amount = _validated_honoraires_item({"acte": "Consultation", "montant": 300})
    assert label == "Consultation"
    assert amount == 300.0
    assert math.isfinite(amount)


def test_paid_honoraires_never_defaults_missing_method_to_cash():
    for value in (None, "", "   "):
        with pytest.raises(ValueError, match="mode de paiement est requis"):
            normalize_document_payment_method(value)


def test_payment_method_aliases_remain_explicit_and_known():
    assert normalize_document_payment_method("Espèces") == "ESPECES"
    assert normalize_document_payment_method("TPE") == "CARTE"
    assert normalize_document_payment_method("Chèque") == "CHEQUE"
    assert normalize_document_payment_method("Virement") == "VIREMENT"
    with pytest.raises(ValueError, match="Mode de paiement invalide"):
        normalize_document_payment_method("crypto")
