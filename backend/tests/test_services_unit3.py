"""Third batch of pure unit tests — clinical_intelligence helpers."""


# ── clinical_intelligence._resolve_motifs ─────────────────────────────────────

class TestResolveMotifs:
    def _fn(self, raw):
        from backend.services.clinical_intelligence import _resolve_motifs
        return _resolve_motifs(raw)

    def test_none_returns_empty(self):
        assert self._fn(None) == []

    def test_empty_string_returns_empty(self):
        assert self._fn("") == []

    def test_valid_json_array(self):
        result = self._fn('["carie", "abces"]')
        assert isinstance(result, list)
        assert len(result) == 2

    def test_single_valid_id(self):
        result = self._fn('["douleur_aigue"]')
        assert len(result) == 1
        assert result[0]["label"] == "Douleur dentaire aiguë"

    def test_unknown_id_skipped(self):
        result = self._fn('["motif_inconnu_xyz"]')
        assert result == []

    def test_invalid_json_returns_empty(self):
        result = self._fn("pas du json")
        assert result == []

    def test_mixed_known_unknown(self):
        result = self._fn('["carie", "motif_xyz_inconnu"]')
        assert len(result) == 1

    def test_urgence_motif_has_urgency_field(self):
        result = self._fn('["abces"]')
        assert len(result) == 1
        assert result[0]["urgency"] == "urgence"

    def test_planified_motif_has_correct_urgency(self):
        result = self._fn('["controle_annuel"]')
        assert len(result) == 1
        assert result[0]["urgency"] == "planifié"

    def test_all_catalog_keys_have_label(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        for key, val in MOTIF_CATALOG.items():
            assert "label" in val, f"Missing 'label' in MOTIF_CATALOG['{key}']"

    def test_non_ortho_catalog_entries_keep_acts(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        for key, val in MOTIF_CATALOG.items():
            if "ORTHODONTIE" not in val.get("specialties", []):
                assert "acts" in val, f"Missing 'acts' in non-ortho MOTIF_CATALOG['{key}']"

    def test_ortho_catalog_can_be_routing_only(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        ortho_without_acts = [
            key
            for key, val in MOTIF_CATALOG.items()
            if "ORTHODONTIE" in val.get("specialties", []) and "acts" not in val
        ]
        assert ortho_without_acts, "At least one orthodontic motif must remain routing-only"

    def test_catalog_has_at_least_10_entries(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        assert len(MOTIF_CATALOG) >= 10
