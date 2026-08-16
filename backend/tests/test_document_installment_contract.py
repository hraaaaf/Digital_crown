import pytest

from backend.utils.document_installment_contract import normalize_document_installment_plan_id


def test_non_installment_document_is_unchanged():
    assert normalize_document_installment_plan_id("devis", {"anything": True}) is None


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"title": "Plan brut", "items": [{"amount": 100}]},
        {"plan_id": None},
        {"plan_id": 0},
        {"plan_id": -1},
        {"plan_id": True},
        {"plan_id": "01"},
        {"plan_id": "1.0"},
    ],
)
def test_raw_or_noncanonical_installment_document_is_rejected(data):
    with pytest.raises(ValueError):
        normalize_document_installment_plan_id("echeancier", data)


def test_positive_integer_plan_id_is_accepted():
    assert normalize_document_installment_plan_id("echeancier", {"plan_id": 42}) == 42
    assert normalize_document_installment_plan_id("ECHEANCIER", {"plan_id": "42"}) == 42
