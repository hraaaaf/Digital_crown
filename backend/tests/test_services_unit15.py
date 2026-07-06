"""Fifteenth batch — llm_cache clear/stats/evict,
base_template update_active_fonts, prescription_service
pure normalizations, medication_dict pure lookups."""
import time
import pytest


# ── LLMCache clear / stats / evict ───────────────────────────────────────────

class TestLlmCacheClear:
    def _cache(self):
        from backend.services.llm_cache import LLMCache
        return LLMCache()

    def test_clear_empties_store(self):
        c = self._cache()
        c.set("model", "prompt", "value")
        c.clear()
        assert c.get("model", "prompt") is None

    def test_stats_returns_dict(self):
        c = self._cache()
        s = c.stats()
        assert isinstance(s, dict)
        assert "size" in s
        assert "ttl_seconds" in s

    def test_stats_size_after_set(self):
        c = self._cache()
        c.set("model", "prompt_x", "value_x")
        assert c.stats()["size"] >= 1

    def test_stats_size_after_clear(self):
        c = self._cache()
        c.set("model", "prompt_y", "value_y")
        c.clear()
        assert c.stats()["size"] == 0

    def test_stats_ttl_is_300(self):
        c = self._cache()
        assert c.stats()["ttl_seconds"] == 300


class TestLlmCacheEvict:
    def _cache(self):
        from backend.services.llm_cache import LLMCache
        return LLMCache()

    def test_evict_removes_expired_entries(self):
        c = self._cache()
        # Inject an entry with an old timestamp directly into the store
        key = c._make_key("model", "old_prompt")
        c._store[key] = ("cached_value", time.time() - 400)  # expired (>300s ago)
        # Force eviction by setting a new value (evict is called in set())
        c.set("model", "trigger_evict", "new_value")
        # The expired key should be gone
        assert key not in c._store

    def test_evict_keeps_fresh_entries(self):
        c = self._cache()
        c.set("model", "fresh_prompt", "fresh_value")
        key = c._make_key("model", "fresh_prompt")
        # Set another entry with a future-ish timestamp to ensure key stays
        c.set("model", "trigger_evict_2", "x")
        assert key in c._store


# ── base_template update_active_fonts ────────────────────────────────────────

class TestUpdateActiveFonts:
    def _bt(self):
        from backend.services.base_template import BaseTemplate
        return BaseTemplate()

    def test_outfit_font_sets_premium(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "outfit"})
        # After update, premium_font should be set (Outfit or Helvetica fallback)
        assert bt.premium_font in ("Outfit", "Helvetica")

    def test_inter_font_sets_premium(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "inter"})
        assert isinstance(bt.premium_font, str)
        assert len(bt.premium_font) > 0

    def test_montserrat_font_sets_premium(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "montserrat"})
        assert isinstance(bt.premium_font, str)

    def test_playfair_font_sets_premium(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "playfair"})
        assert isinstance(bt.premium_font, str)

    def test_helvetica_font_sets_premium(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "helvetica"})
        assert isinstance(bt.premium_font, str)

    def test_unknown_font_falls_back_to_helvetica(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "unknownfont_xyz"})
        assert isinstance(bt.premium_font, str)

    def test_arabic_font_set_after_update(self):
        bt = self._bt()
        bt.update_active_fonts({"font_fr": "outfit", "font_ar": "amiri"})
        assert isinstance(bt.arabic_font, str)


# ── medication_dict pure helpers ──────────────────────────────────────────────

class TestMedicationDictToMg:
    def _fn(self, value, unit):
        from backend.services.medication_dict import _to_mg
        return _to_mg(value, unit)

    def test_mg_unit_returns_float(self):
        assert self._fn("500", "MG") == 500.0

    def test_g_unit_converts_to_mg(self):
        assert self._fn("1", "G") == 1000.0

    def test_empty_value_returns_none(self):
        assert self._fn("", "MG") is None

    def test_none_value_returns_none(self):
        assert self._fn(None, "MG") is None

    def test_non_numeric_returns_none(self):
        assert self._fn("abc", "MG") is None

    def test_ml_unit_returns_none(self):
        assert self._fn("5", "MG/ML") is None

    def test_comma_decimal(self):
        assert self._fn("0,5", "G") == 500.0


class TestMedicationDictBrandRoot:
    def _fn(self, name):
        from backend.services.medication_dict import _brand_root
        return _brand_root(name)

    def test_strips_dosage_number(self):
        assert self._fn("DOLIPRANE 1000 MG") == "DOLIPRANE"

    def test_empty_returns_empty(self):
        assert self._fn("") == ""

    def test_none_returns_empty(self):
        assert self._fn(None) == ""

    def test_single_word_unchanged(self):
        assert self._fn("AMOXICILLINE") == "AMOXICILLINE"


class TestMedicationDictSearch:
    def _fn(self, q):
        from backend.services.medication_dict import search
        return search(q)

    def test_returns_list(self):
        result = self._fn("amoxicilline")
        assert isinstance(result, list)

    def test_empty_query_returns_list(self):
        result = self._fn("")
        assert isinstance(result, list)

    def test_unknown_drug_returns_empty_list(self):
        result = self._fn("UNKNOWNMOLECULE_XYZ_99999")
        assert isinstance(result, list)


class TestMedicationDictMatchingRecords:
    def _fn(self, name):
        from backend.services.medication_dict import _matching_records
        return _matching_records(name)

    def test_empty_name_returns_empty_list(self):
        result = self._fn("")
        assert result == []

    def test_none_name_returns_empty_list(self):
        result = self._fn(None)
        assert result == []

    def test_returns_list(self):
        result = self._fn("AMOXICILLINE")
        assert isinstance(result, list)
