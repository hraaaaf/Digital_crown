"""Twelfth batch — CephaloEngine._evaluate_metric / calculate_ddm_reelle,
rate_limit file-I/O helpers, data_sanitizer sanitize_for_llm,
accounting_utils happy paths."""
import os
import json
import tempfile
import pytest


# ── CephaloEngine._evaluate_metric ───────────────────────────────────────────

class TestEvaluateMetricNormal:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_value_within_bounds_status_normal(self):
        result = self._eng()._evaluate_metric(82.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["status"] == "Normal"

    def test_value_within_bounds_interpretation_is_norm_msg(self):
        result = self._eng()._evaluate_metric(82.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["interpretation"] == "Norm"

    def test_returns_dict_with_required_keys(self):
        result = self._eng()._evaluate_metric(82.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        for key in ("valeur", "norm_mean", "norm_min", "norm_max", "status", "interpretation", "z_score"):
            assert key in result

    def test_norm_mean_and_bounds_correct(self):
        result = self._eng()._evaluate_metric(82.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["norm_mean"] == 82.0
        assert result["norm_min"] == 79.0
        assert result["norm_max"] == 85.0

    def test_z_score_zero_at_mean(self):
        result = self._eng()._evaluate_metric(82.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["z_score"] == 0.0

    def test_z_score_nonzero_when_offset(self):
        result = self._eng()._evaluate_metric(85.0, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["z_score"] > 0.0


class TestEvaluateMetricHigh:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_value_above_max_status_high(self):
        result = self._eng()._evaluate_metric(90.0, 82.0, 3.0, "Prognathisme", "Dec", "Norm")
        assert result["status"] == "High"

    def test_value_above_max_interpretation_is_inc_msg(self):
        result = self._eng()._evaluate_metric(90.0, 82.0, 3.0, "Prognathisme", "Dec", "Norm")
        assert result["interpretation"] == "Prognathisme"

    def test_valeur_rounded_to_one_decimal(self):
        result = self._eng()._evaluate_metric(90.123, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["valeur"] == 90.1


class TestEvaluateMetricLow:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_value_below_min_status_low(self):
        result = self._eng()._evaluate_metric(74.0, 82.0, 3.0, "Inc", "Rétrognathisme", "Norm")
        assert result["status"] == "Low"

    def test_value_below_min_interpretation_is_dec_msg(self):
        result = self._eng()._evaluate_metric(74.0, 82.0, 3.0, "Inc", "Rétrognathisme", "Norm")
        assert result["interpretation"] == "Rétrognathisme"


class TestEvaluateMetricCompensated:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_high_but_within_comp_range_status_compensated(self):
        # value=88 > max(85) but within comp_range upper(92)
        result = self._eng()._evaluate_metric(88.0, 82.0, 3.0, "Inc", "Dec", "Norm", comp_range=(75.0, 92.0))
        assert result["status"] == "Compensated"

    def test_compensated_interpretation_contains_compensation_label(self):
        result = self._eng()._evaluate_metric(88.0, 82.0, 3.0, "Inc", "Dec", "Norm", comp_range=(75.0, 92.0))
        assert "Compensé" in result["interpretation"]

    def test_low_but_within_comp_range_status_compensated(self):
        # value=77 < min(79) but within comp_range lower(75)
        result = self._eng()._evaluate_metric(77.0, 82.0, 3.0, "Inc", "Dec", "Norm", comp_range=(75.0, 92.0))
        assert result["status"] == "Compensated"

    def test_above_comp_range_still_high(self):
        # value=95 > comp_range upper(92) → stays High
        result = self._eng()._evaluate_metric(95.0, 82.0, 3.0, "Inc", "Dec", "Norm", comp_range=(75.0, 92.0))
        assert result["status"] == "High"


class TestEvaluateMetricMissing:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_none_value_status_missing(self):
        result = self._eng()._evaluate_metric(None, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["status"] == "Missing"

    def test_none_value_valeur_is_none(self):
        result = self._eng()._evaluate_metric(None, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["valeur"] is None

    def test_none_value_z_score_zero(self):
        result = self._eng()._evaluate_metric(None, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["z_score"] == 0.0

    def test_none_value_bounds_still_computed(self):
        result = self._eng()._evaluate_metric(None, 82.0, 3.0, "Inc", "Dec", "Norm")
        assert result["norm_min"] == 79.0
        assert result["norm_max"] == 85.0


# ── CephaloEngine.calculate_ddm_reelle ───────────────────────────────────────

class TestCalculateDdmReelle:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_impa_90_returns_ddm_clinique_unchanged(self):
        # IMPA=90 → ecart=0 → ddm_cephalo=0 → ddm_reelle = ddm_clinique
        assert self._eng().calculate_ddm_reelle(-3.0, 90.0) == -3.0

    def test_impa_above_90_reduces_ddm(self):
        # IMPA=95 → ecart=5 → ddm_cephalo=2 → ddm_reelle = -3 + 2 = -1
        assert self._eng().calculate_ddm_reelle(-3.0, 95.0) == -1.0

    def test_impa_below_90_increases_ddm(self):
        # IMPA=85 → ecart=-5 → ddm_cephalo=-2 → ddm_reelle = -3 - 2 = -5
        assert self._eng().calculate_ddm_reelle(-3.0, 85.0) == -5.0

    def test_returns_float(self):
        result = self._eng().calculate_ddm_reelle(0.0, 90.0)
        assert isinstance(result, float)

    def test_result_rounded_to_two_decimals(self):
        # 5 / 2.5 = 2.0 exactly → ddm = 0 + 2.0 = 2.0
        result = self._eng().calculate_ddm_reelle(0.0, 95.0)
        assert result == 2.0

    def test_zero_ddm_clinique_and_zero_ecart(self):
        assert self._eng().calculate_ddm_reelle(0.0, 90.0) == 0.0


# ── rate_limit file-I/O helpers ───────────────────────────────────────────────

class TestRateLimitLoad:
    def test_load_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PATH", str(tmp_path))
        # Patch _store_path to a non-existent path
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "nonexistent.json")
            result = rl._load()
            assert result == {}
        finally:
            rl._store_path = original

    def test_load_reads_existing_file(self, tmp_path, monkeypatch):
        import backend.utils.rate_limit as rl
        store_file = tmp_path / "rate_limit.json"
        store_file.write_text(json.dumps({"192.168.1.1": [3, 1700000000.0]}))
        original = rl._store_path
        try:
            rl._store_path = str(store_file)
            result = rl._load()
            assert "192.168.1.1" in result
            assert result["192.168.1.1"] == (3, 1700000000.0)
        finally:
            rl._store_path = original

    def test_load_returns_empty_on_corrupted_file(self, tmp_path):
        import backend.utils.rate_limit as rl
        store_file = tmp_path / "rate_limit.json"
        store_file.write_text("not valid json{{")
        original = rl._store_path
        try:
            rl._store_path = str(store_file)
            result = rl._load()
            assert result == {}
        finally:
            rl._store_path = original


class TestRateLimitSave:
    def test_save_writes_json_file(self, tmp_path):
        import backend.utils.rate_limit as rl
        store_file = tmp_path / "rate_limit.json"
        original = rl._store_path
        try:
            rl._store_path = str(store_file)
            rl._save({"10.0.0.1": (2, 1700000000.0)})
            assert store_file.exists()
            loaded = json.loads(store_file.read_text())
            assert "10.0.0.1" in loaded
        finally:
            rl._store_path = original

    def test_save_then_load_roundtrip(self, tmp_path):
        import backend.utils.rate_limit as rl
        store_file = tmp_path / "rate_limit.json"
        original = rl._store_path
        try:
            rl._store_path = str(store_file)
            data = {"10.0.0.2": (1, 1700000001.0)}
            rl._save(data)
            result = rl._load()
            assert result["10.0.0.2"] == (1, 1700000001.0)
        finally:
            rl._store_path = original

    def test_save_does_not_raise_on_unwritable_path(self):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = "/nonexistent_dir/rate.json"
            rl._save({"x": [1, 2.0]})  # should silently pass
        finally:
            rl._store_path = original


# ── data_sanitizer.sanitize_bot_response ─────────────────────────────────────

class TestDataSanitizerSanitizeBotResponse:
    def _san(self):
        from backend.services.security.data_sanitizer import DataSanitizer
        return DataSanitizer()

    def test_returns_string(self):
        result = self._san().sanitize_bot_response("patient Ahmed, 45 ans")
        assert isinstance(result, str)

    def test_pii_removed_from_output(self):
        result = self._san().sanitize_bot_response("email: test@clinic.ma")
        assert "test@clinic.ma" not in result

    def test_no_mapping_returned(self):
        result = self._san().sanitize_bot_response("texte neutre")
        assert not isinstance(result, tuple)

    def test_phone_masked(self):
        result = self._san().sanitize_bot_response("Tel: 0612345678")
        assert "0612345678" not in result

    def test_empty_string_returns_empty(self):
        result = self._san().sanitize_bot_response("")
        assert result == ""


# ── accounting_utils happy paths ──────────────────────────────────────────────

class TestAccountingUtilsHappyPaths:
    def _fn(self, data):
        from backend.utils.accounting_utils import extract_amount_from_clinical_data
        return extract_amount_from_clinical_data(data)

    def test_total_key_float(self):
        assert self._fn({"total": 150.0}) == 150.0

    def test_total_amount_key(self):
        assert self._fn({"total_amount": 200.0}) == 200.0

    def test_amount_key(self):
        assert self._fn({"amount": 75.5}) == 75.5

    def test_prix_fallback_key(self):
        assert self._fn({"prix": 300.0}) == 300.0

    def test_payments_sum(self):
        data = {"payments": [{"montant": 100.0}, {"montant": 50.0}]}
        assert self._fn(data) == 150.0

    def test_payments_amount_field(self):
        data = {"payments": [{"amount": 80.0}, {"amount": 20.0}]}
        assert self._fn(data) == 100.0

    def test_items_sum(self):
        data = {"items": [{"prix_unitaire": 80.0}, {"prix_unitaire": 40.0}]}
        assert self._fn(data) == 120.0

    def test_empty_dict_returns_zero(self):
        assert self._fn({}) == 0.0
