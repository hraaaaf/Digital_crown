"""Second batch of pure unit tests — llm_cache, data_sanitizer, clinical_coherence helpers,
accounting_utils, medication_dict internals."""
import time


# ── llm_cache ─────────────────────────────────────────────────────────────────

class TestLLMCache:
    def _cache(self):
        from backend.services.llm_cache import LLMCache
        return LLMCache()

    def test_get_miss_returns_none(self):
        c = self._cache()
        assert c.get("gpt-4", "hello") is None

    def test_set_and_get_hit(self):
        c = self._cache()
        c.set("gpt-4", "hello", "world")
        assert c.get("gpt-4", "hello") == "world"

    def test_different_model_same_prompt_miss(self):
        c = self._cache()
        c.set("modelA", "prompt", "response")
        assert c.get("modelB", "prompt") is None

    def test_clear_empties_cache(self):
        c = self._cache()
        c.set("m", "p", "v")
        c.clear()
        assert c.get("m", "p") is None

    def test_stats_returns_size(self):
        c = self._cache()
        c.set("m1", "p1", "v1")
        c.set("m2", "p2", "v2")
        stats = c.stats()
        assert stats["size"] == 2
        assert stats["ttl_seconds"] > 0

    def test_stats_empty_cache(self):
        c = self._cache()
        assert c.stats()["size"] == 0

    def test_overwrite_same_key(self):
        c = self._cache()
        c.set("m", "p", "first")
        c.set("m", "p", "second")
        assert c.get("m", "p") == "second"

    def test_multiple_entries(self):
        c = self._cache()
        for i in range(5):
            c.set("m", f"prompt_{i}", f"resp_{i}")
        for i in range(5):
            assert c.get("m", f"prompt_{i}") == f"resp_{i}"

    def test_ttl_eviction(self):
        from backend.services import llm_cache as mod
        original_ttl = mod.TTL_SECONDS
        try:
            mod.TTL_SECONDS = 0  # expire immediately
            c = mod.LLMCache()
            c.set("m", "p", "v")
            time.sleep(0.01)
            # Force eviction by calling get
            result = c.get("m", "p")
            assert result is None
        finally:
            mod.TTL_SECONDS = original_ttl


# ── data_sanitizer ────────────────────────────────────────────────────────────

class TestDataSanitizerSanitize:
    def _san(self):
        from backend.services.security.data_sanitizer import DataSanitizer
        return DataSanitizer()

    def test_email_masked(self):
        s = self._san()
        text, mapping = s.sanitize("Contact: test@example.com")
        assert "test@example.com" not in text
        assert any("test@example.com" in v for v in mapping.values())

    def test_email_token_format(self):
        s = self._san()
        text, mapping = s.sanitize("Email: user@domain.ma")
        assert "[EMAIL_1]" in text

    def test_moroccan_phone_masked(self):
        s = self._san()
        text, mapping = s.sanitize("Tel: 0661234567")
        assert "0661234567" not in text

    def test_amount_mad_masked(self):
        s = self._san()
        text, mapping = s.sanitize("Facture de 500 MAD")
        assert "500 MAD" not in text

    def test_proper_name_masked(self):
        s = self._san()
        text, mapping = s.sanitize("Patient Dupont est arrivé")
        # "Dupont" is a capitalized proper name
        assert "[NAME_" in text

    def test_whitelist_word_not_masked(self):
        s = self._san()
        text, _ = s.sanitize("Bonjour, prendre un rdv")
        # "Bonjour" is in whitelist
        assert "Bonjour" in text

    def test_dental_term_not_masked(self):
        s = self._san()
        text, _ = s.sanitize("Extraction d'une couronne")
        assert "Extraction" in text

    def test_same_email_same_token(self):
        s = self._san()
        text, mapping = s.sanitize("user@x.com et user@x.com")
        # Both occurrences replaced by same token
        assert text.count("[EMAIL_1]") == 2
        assert "[EMAIL_2]" not in text

    def test_no_email_or_phone_in_plain_text(self):
        s = self._san()
        text, mapping = s.sanitize("aucune donnée sensible ici")
        # lowercase text: no emails, phones, amounts → no EMAIL/PHONE/AMOUNT tokens
        email_tokens = [k for k in mapping if k.startswith("[EMAIL")]
        phone_tokens = [k for k in mapping if k.startswith("[PHONE")]
        assert email_tokens == []
        assert phone_tokens == []

    def test_returns_tuple(self):
        s = self._san()
        result = s.sanitize("test message")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestDataSanitizerRestore:
    def _san(self):
        from backend.services.security.data_sanitizer import DataSanitizer
        return DataSanitizer()

    def test_restore_replaces_token(self):
        s = self._san()
        text, mapping = s.sanitize("Email: user@test.ma")
        restored = s.restore(text, mapping)
        assert "user@test.ma" in restored

    def test_restore_empty_mapping(self):
        s = self._san()
        assert s.restore("hello world", {}) == "hello world"

    def test_restore_strips_result(self):
        s = self._san()
        assert s.restore("  hello  ", {}) == "hello"

    def test_restore_removes_orphan_tokens(self):
        s = self._san()
        text = "Réponse: [NAME_99] est arrivé"
        result = s.restore(text, {})
        assert "[NAME_99]" not in result

    def test_sanitize_then_restore_roundtrip(self):
        s = self._san()
        original = "Contact: user@cabinet.ma — Tel: 0661234567"
        masked, mapping = s.sanitize(original)
        assert "user@cabinet.ma" not in masked
        restored = s.restore(masked, mapping)
        assert "user@cabinet.ma" in restored


class TestDataSanitizerStream:
    def _san(self):
        from backend.services.security.data_sanitizer import DataSanitizer
        return DataSanitizer()

    def test_restore_stream_basic(self):
        s = self._san()
        _, mapping = s.sanitize("user@x.com")
        # Reverse mapping for stream test
        rev = {v: k for k, v in mapping.items()}
        chunks = ["Bonjour ", "[EMAIL_1]"]
        result = "".join(s.restore_stream(chunks, mapping))
        assert isinstance(result, str)

    def test_restore_stream_no_tokens(self):
        s = self._san()
        chunks = ["hello ", "world"]
        result = "".join(s.restore_stream(chunks, {}))
        assert result == "hello world"

    def test_sanitize_bot_response_returns_string(self):
        s = self._san()
        result = s.sanitize_bot_response("Patient Dupont a payé 300 MAD")
        assert isinstance(result, str)

    def test_sanitize_bot_response_masks_sensitive(self):
        s = self._san()
        result = s.sanitize_bot_response("Email: user@test.ma")
        assert "user@test.ma" not in result


# ── clinical_coherence helpers ────────────────────────────────────────────────

class TestClinicalCoherenceHelpers:
    def _svc(self):
        from backend.services.clinical_coherence import ClinicalCoherenceService
        return ClinicalCoherenceService()

    def test_is_antibiotic_amoxicilline(self):
        assert self._svc()._is_antibiotic("amoxicilline")

    def test_is_antibiotic_clamoxyl(self):
        assert self._svc()._is_antibiotic("CLAMOXYL 1g")

    def test_is_antibiotic_metronidazole(self):
        assert self._svc()._is_antibiotic("METRONIDAZOLE 500mg")

    def test_is_antibiotic_paracetamol_false(self):
        assert not self._svc()._is_antibiotic("Paracétamol")

    def test_is_antibiotic_ibuprofen_false(self):
        assert not self._svc()._is_antibiotic("Ibuprofène 400mg")

    def test_is_nsaid_ibuprofen(self):
        assert self._svc()._is_nsaid("ibuprofene")

    def test_is_nsaid_advil(self):
        assert self._svc()._is_nsaid("Advil")

    def test_is_nsaid_diclofenac(self):
        assert self._svc()._is_nsaid("Voltarène diclofenac")

    def test_is_nsaid_amoxicilline_false(self):
        assert not self._svc()._is_nsaid("Amoxicilline")

    def test_is_stomach_risk_ulcere(self):
        assert self._svc()._is_stomach_risk("Antécédent d'ulcère gastrique")

    def test_is_stomach_risk_gastrite(self):
        assert self._svc()._is_stomach_risk("gastrite chronique")

    def test_is_stomach_risk_none_false(self):
        assert not self._svc()._is_stomach_risk(None)

    def test_is_stomach_risk_rgo(self):
        assert self._svc()._is_stomach_risk("RGO sévère")

    def test_is_stomach_risk_ras_false(self):
        assert not self._svc()._is_stomach_risk("RAS")

    def test_is_invasive_extraction(self):
        assert self._svc()._is_invasive_act("Extraction dentaire")

    def test_is_invasive_implant(self):
        assert self._svc()._is_invasive_act("Pose implant chirurgie")

    def test_is_invasive_canalaire(self):
        assert self._svc()._is_invasive_act("Traitement canalaire")

    def test_is_invasive_detartrage(self):
        assert self._svc()._is_invasive_act("Détartrage complet")

    def test_is_invasive_composite_false(self):
        assert not self._svc()._is_invasive_act("Composite postérieur")

    def test_calculate_age_returns_int(self):
        from datetime import datetime
        born = datetime(1990, 1, 1)
        age = self._svc()._calculate_age(born)
        assert isinstance(age, int)
        assert age >= 35

    def test_calculate_age_none_returns_30(self):
        assert self._svc()._calculate_age(None) == 30


# ── accounting_utils ──────────────────────────────────────────────────────────

class TestExtractAmountFromClinicalData:
    def _fn(self, data):
        from backend.utils.accounting_utils import extract_amount_from_clinical_data
        return extract_amount_from_clinical_data(data)

    def test_none_returns_zero(self):
        assert self._fn(None) == 0.0

    def test_empty_dict_returns_zero(self):
        assert self._fn({}) == 0.0

    def test_total_amount_key(self):
        assert self._fn({"total_amount": 1500.0}) == 1500.0

    def test_total_key(self):
        assert self._fn({"total": 800.0}) == 800.0

    def test_amount_key(self):
        assert self._fn({"amount": 350.0}) == 350.0

    def test_montant_total_key(self):
        assert self._fn({"montant_total": 2200.0}) == 2200.0

    def test_payments_list_sum(self):
        data = {"payments": [{"montant": 500.0}, {"montant": 300.0}]}
        assert self._fn(data) == 800.0

    def test_payments_amount_field(self):
        data = {"payments": [{"amount": 750.0}]}
        assert self._fn(data) == 750.0

    def test_items_list_sum(self):
        data = {"items": [{"prix_unitaire": 600.0}, {"prix_unitaire": 400.0}]}
        assert self._fn(data) == 1000.0

    def test_items_montant_field(self):
        data = {"items": [{"montant": 1200.0}]}
        assert self._fn(data) == 1200.0

    def test_fallback_prix_key(self):
        assert self._fn({"prix": 450.0}) == 450.0

    def test_zero_total_falls_through_to_next(self):
        data = {"total": 0, "amount": 600.0}
        assert self._fn(data) == 600.0

    def test_invalid_value_falls_through(self):
        data = {"total": "invalid", "amount": 300.0}
        assert self._fn(data) == 300.0

    def test_string_number_parsed(self):
        assert self._fn({"total_amount": "1250.5"}) == 1250.5


# ── medication_dict internals ─────────────────────────────────────────────────

class TestMedicationDictInternals:
    def test_to_mg_milligrams(self):
        from backend.services.medication_dict import _to_mg
        assert _to_mg("500", "MG") == 500.0

    def test_to_mg_grams(self):
        from backend.services.medication_dict import _to_mg
        assert _to_mg("1", "G") == 1000.0

    def test_to_mg_none_value(self):
        from backend.services.medication_dict import _to_mg
        assert _to_mg("", "MG") is None

    def test_to_mg_concentration_returns_none(self):
        from backend.services.medication_dict import _to_mg
        assert _to_mg("5", "MG/ML") is None

    def test_to_mg_invalid_value_returns_none(self):
        from backend.services.medication_dict import _to_mg
        assert _to_mg("abc", "MG") is None

    def test_brand_root_strips_dosage(self):
        from backend.services.medication_dict import _brand_root
        assert _brand_root("DOLIPRANE 1000 MG") == "DOLIPRANE"

    def test_brand_root_single_word(self):
        from backend.services.medication_dict import _brand_root
        assert _brand_root("ADVIL") == "ADVIL"

    def test_brand_root_empty_returns_empty(self):
        from backend.services.medication_dict import _brand_root
        assert _brand_root("") == ""

    def test_brand_root_none_returns_empty(self):
        from backend.services.medication_dict import _brand_root
        assert _brand_root(None) == ""

    def test_search_short_query_returns_empty(self):
        from backend.services.medication_dict import search
        # Query shorter than 2 chars after upper/strip
        assert search("a") == []

    def test_search_empty_returns_empty(self):
        from backend.services.medication_dict import search
        assert search("") == []

    def test_validate_dosage_unknown_med(self):
        from backend.services.medication_dict import validate_dosage
        result = validate_dosage("MEDICAMENT_INEXISTANT_XYZ", None)
        assert result == {"known": False}

    def test_strengths_mg_simple(self):
        from backend.services.medication_dict import _strengths_mg
        rec = {"dosage": "500", "unite": "MG"}
        result = _strengths_mg(rec)
        assert 500.0 in result

    def test_strengths_mg_compound(self):
        from backend.services.medication_dict import _strengths_mg
        rec = {"dosage": "500/125", "unite": "MG/MG"}
        result = _strengths_mg(rec)
        assert 500.0 in result
        assert 125.0 in result

    def test_strengths_mg_grams(self):
        from backend.services.medication_dict import _strengths_mg
        rec = {"dosage": "1", "unite": "G"}
        result = _strengths_mg(rec)
        assert 1000.0 in result

    def test_search_returns_list(self):
        from backend.services.medication_dict import search
        result = search("DOLIPRANE")
        assert isinstance(result, list)
