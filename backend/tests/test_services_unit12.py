"""Twelfth batch — geometry-only cephalo guards, rate-limit file I/O,
data-sanitizer response handling, and accounting-utils happy paths."""
import json


# ── CephaloEngine geometry-only boundary ──────────────────────────────────────

class TestCephaloEngineGeometryOnly:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_legacy_normative_evaluator_is_absent(self):
        assert not hasattr(self._eng(), "_evaluate_metric")

    def test_impa_based_ddm_conversion_is_absent(self):
        assert not hasattr(self._eng(), "calculate_ddm_reelle")

    def test_raw_measurement_contains_no_normative_authority(self):
        result = self._eng()._raw_measurement(82.123)
        assert result["valeur"] == 82.1
        assert result["norm_mean"] is None
        assert result["norm_min"] is None
        assert result["norm_max"] is None
        assert result["plage_compensation"] is None
        assert result["status"] == "N/A"
        assert result["interpretation"] == "Mesure géométrique brute"
        assert result["z_score"] is None

    def test_missing_raw_measurement_remains_uninterpreted(self):
        result = self._eng()._raw_measurement(None)
        assert result["valeur"] is None
        assert result["status"] == "N/A"
        assert result["interpretation"] == "Non calculé"
        assert result["z_score"] is None

    def test_empty_landmarks_do_not_invent_context_or_treatment(self):
        result = self._eng().calculate_metrics({})
        assert result.analysis_metadata["cohort"] == "Non classé"
        assert result.t1_projection == {}
        assert result.t2_projection == {}
        assert result.ai_narrative == {}
        assert result.clinical_data["ddm_reelle"] is None
        assert result.clinical_data["plan_traitement"] == ""


# ── rate_limit file-I/O helpers ───────────────────────────────────────────────

class TestRateLimitLoad:
    def test_load_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PATH", str(tmp_path))
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
            rl._save({"x": [1, 2.0]})
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
