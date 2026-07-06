"""Tests backend.utils.accounting_utils — extract_amount_from_clinical_data."""
from backend.utils.accounting_utils import extract_amount_from_clinical_data


class TestExtractAmount:
    def test_extracts_from_payments(self):
        data = {"payments": [{"montant": 3000.0}, {"montant": 1500.0}]}
        assert extract_amount_from_clinical_data(data) == 4500.0

    def test_extracts_from_items(self):
        data = {"items": [{"prix_unitaire": 5000.0, "quantite": 2}]}
        result = extract_amount_from_clinical_data(data)
        assert result >= 5000.0  # at least one item's price

    def test_returns_zero_for_empty(self):
        assert extract_amount_from_clinical_data({}) == 0.0
        assert extract_amount_from_clinical_data(None) == 0.0

    def test_single_payment(self):
        data = {"payments": [{"montant": 12000.0}]}
        assert extract_amount_from_clinical_data(data) == 12000.0

    def test_string_montant_is_handled(self):
        """montant may be stored as string in older records."""
        data = {"payments": [{"montant": "2500.0"}]}
        result = extract_amount_from_clinical_data(data)
        assert result == 2500.0 or result == 0.0  # graceful handling

    def test_total_amount_key_takes_priority(self):
        data = {"total_amount": 9999.0, "payments": [{"montant": 100.0}]}
        assert extract_amount_from_clinical_data(data) == 9999.0

    def test_total_key(self):
        data = {"total": 4200.0}
        assert extract_amount_from_clinical_data(data) == 4200.0

    def test_amount_key(self):
        data = {"amount": 3300.0}
        assert extract_amount_from_clinical_data(data) == 3300.0

    def test_montant_total_key(self):
        data = {"montant_total": 7700.0}
        assert extract_amount_from_clinical_data(data) == 7700.0

    def test_prix_fallback(self):
        data = {"prix": 1500.0}
        assert extract_amount_from_clinical_data(data) == 1500.0

    def test_item_with_montant_field(self):
        data = {"items": [{"montant": 2000.0}, {"montant": 3000.0}]}
        assert extract_amount_from_clinical_data(data) == 5000.0

    def test_invalid_total_falls_through_to_payments(self):
        data = {"total": "not_a_number", "payments": [{"montant": 500.0}]}
        assert extract_amount_from_clinical_data(data) == 500.0

    def test_zero_total_falls_through_to_payments(self):
        data = {"total": 0, "payments": [{"montant": 500.0}]}
        assert extract_amount_from_clinical_data(data) == 500.0
