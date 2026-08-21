"""Third batch of pure unit tests — treatment_plan_engine and clinical_intelligence helpers."""


# ── treatment_plan_engine ─────────────────────────────────────────────────────

class TestTreatmentPlanEngineMapToPhase:
    def _engine(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        return TreatmentPlanEngine()

    def test_absces_maps_to_urgence(self):
        assert self._engine()._map_to_phase("abcès dentaire") == "URGENCE"

    def test_pulpite_maps_to_urgence(self):
        assert self._engine()._map_to_phase("pulpite aiguë") == "URGENCE"

    def test_infection_maps_to_urgence(self):
        assert self._engine()._map_to_phase("infection périapicale") == "URGENCE"

    def test_douleur_maps_to_urgence(self):
        assert self._engine()._map_to_phase("douleur nocturne") == "URGENCE"

    def test_detartrage_maps_to_initiale(self):
        assert self._engine()._map_to_phase("détartrage") == "INITIALE"

    def test_parodontite_maps_to_initiale(self):
        assert self._engine()._map_to_phase("parodontite") == "INITIALE"

    def test_extraction_maps_to_initiale(self):
        assert self._engine()._map_to_phase("extraction dentaire") == "INITIALE"

    def test_carie_maps_to_conservatrice(self):
        assert self._engine()._map_to_phase("carie dentaire") == "CONSERVATRICE"

    def test_restauration_maps_to_conservatrice(self):
        assert self._engine()._map_to_phase("restauration composite") == "CONSERVATRICE"

    def test_implant_maps_to_rehabilitation(self):
        assert self._engine()._map_to_phase("implant zircone") == "REHABILITATION"

    def test_couronne_maps_to_rehabilitation(self):
        assert self._engine()._map_to_phase("couronne céramique") == "REHABILITATION"

    def test_bridge_maps_to_rehabilitation(self):
        assert self._engine()._map_to_phase("bridge 3 éléments") == "REHABILITATION"

    def test_unknown_maps_to_maintenance(self):
        assert self._engine()._map_to_phase("fluoruration preventive") == "MAINTENANCE"


class TestTreatmentPlanEngineSuggestAct:
    def _engine(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        return TreatmentPlanEngine()

    def test_carie_returns_obturation(self):
        result = self._engine()._suggest_act("carie")
        assert "Obturation" in result

    def test_abces_returns_drainage(self):
        result = self._engine()._suggest_act("abcès")
        assert "Drainage" in result or "Urgence" in result

    def test_detartrage_returns_detartrage(self):
        result = self._engine()._suggest_act("détartrage")
        assert "Détartrage" in result

    def test_implant_returns_pose(self):
        result = self._engine()._suggest_act("implant")
        assert "implant" in result.lower()

    def test_couronne_returns_couronne(self):
        result = self._engine()._suggest_act("couronne")
        assert "couronne" in result.lower()

    def test_unknown_returns_examen(self):
        result = self._engine()._suggest_act("pathologie_inconnue")
        assert "Examen" in result


class TestTreatmentPlanEngineGeneratePlan:
    def _engine(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        return TreatmentPlanEngine()

    def test_empty_detections_returns_structure(self):
        result = self._engine().generate_plan([])
        assert "phases" in result
        assert "total_cost" in result
        assert result["total_cost"] == 0.0

    def test_phases_keys_present(self):
        result = self._engine().generate_plan([])
        for phase in ["URGENCE", "INITIALE", "CONSERVATRICE", "REHABILITATION", "MAINTENANCE"]:
            assert phase in result["phases"]

    def test_carie_detection_goes_to_conservatrice(self):
        detections = [{"label": "carie", "fdi": "16"}]
        result = self._engine().generate_plan(detections)
        assert len(result["phases"]["CONSERVATRICE"]) == 1

    def test_absces_detection_goes_to_urgence(self):
        detections = [{"label": "abcès", "fdi": "26"}]
        result = self._engine().generate_plan(detections)
        assert len(result["phases"]["URGENCE"]) == 1

    def test_multiple_detections(self):
        detections = [
            {"label": "abcès", "fdi": "11"},
            {"label": "carie", "fdi": "16"},
            {"label": "détartrage", "fdi": "Global"},
        ]
        result = self._engine().generate_plan(detections)
        assert len(result["phases"]["URGENCE"]) == 1
        assert len(result["phases"]["CONSERVATRICE"]) == 1
        assert len(result["phases"]["INITIALE"]) == 1

    def test_suggested_act_in_result(self):
        detections = [{"label": "extraction", "fdi": "48"}]
        result = self._engine().generate_plan(detections)
        acts = result["phases"]["INITIALE"]
        assert any("Extraction" in a["suggested_act"] for a in acts)

    def test_total_cost_sums_up(self):
        detections = [
            {"label": "carie", "fdi": "16"},
            {"label": "extraction", "fdi": "48"},
        ]
        result = self._engine().generate_plan(detections)
        assert result["total_cost"] > 0

    def test_summary_present(self):
        result = self._engine().generate_plan([{"label": "carie", "fdi": "16"}])
        assert "summary" in result
        assert isinstance(result["summary"], str)

    def test_empty_summary_says_maintenance(self):
        result = self._engine().generate_plan([])
        assert "Maintenance" in result["summary"] or "maintenance" in result["summary"].lower()

    def test_implant_goes_to_rehabilitation(self):
        detections = [{"label": "implant", "fdi": "36"}]
        result = self._engine().generate_plan(detections)
        assert len(result["phases"]["REHABILITATION"]) == 1

    def test_priority_map_has_expected_keys(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        eng = TreatmentPlanEngine()
        assert "infection" in eng.PRIORITY_MAP
        assert "implant" in eng.PRIORITY_MAP

    def test_pricing_map_has_expected_keys(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        eng = TreatmentPlanEngine()
        assert "implant" in eng.PRICING_MAP
        assert eng.PRICING_MAP["implant"] == 8000.0


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

    def test_all_catalog_keys_have_acts(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        for key, val in MOTIF_CATALOG.items():
            assert "acts" in val, f"Missing 'acts' in MOTIF_CATALOG['{key}']"

    def test_catalog_has_at_least_10_entries(self):
        from backend.services.clinical_intelligence import MOTIF_CATALOG
        assert len(MOTIF_CATALOG) >= 10
