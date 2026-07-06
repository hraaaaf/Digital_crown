"""Unit tests for services/treatment_plan_engine.py — pure Python, no DB required."""
from backend.services.treatment_plan_engine import TreatmentPlanEngine


class TestTreatmentPlanEngineInit:
    def test_priority_map_has_keys(self):
        engine = TreatmentPlanEngine()
        assert "carie" in engine.PRIORITY_MAP
        assert "implant" in engine.PRIORITY_MAP
        assert "orthodontie" in engine.PRIORITY_MAP

    def test_pricing_map_has_implant(self):
        engine = TreatmentPlanEngine()
        assert engine.PRICING_MAP["implant"] == 8000.0


class TestGeneratePlan:
    def setup_method(self):
        self.engine = TreatmentPlanEngine()

    def test_empty_detections(self):
        plan = self.engine.generate_plan([])
        assert "phases" in plan
        assert plan["total_cost"] == 0.0

    def test_returns_required_keys(self):
        plan = self.engine.generate_plan([])
        for key in ("phases", "total_cost", "summary", "created_at", "patient_id"):
            assert key in plan

    def test_patient_id_is_none(self):
        plan = self.engine.generate_plan([])
        assert plan["patient_id"] is None

    def test_single_carie_detection(self):
        plan = self.engine.generate_plan([{"label": "carie", "fdi": "36"}])
        assert len(plan["phases"]["CONSERVATRICE"]) == 1
        act = plan["phases"]["CONSERVATRICE"][0]
        assert act["fdi"] == "36"
        assert act["estimated_cost"] == 400.0
        assert act["status"] == "SUGGESTED"

    def test_abces_goes_to_urgence(self):
        plan = self.engine.generate_plan([{"label": "abcès", "fdi": "46"}])
        assert len(plan["phases"]["URGENCE"]) == 1

    def test_pulpite_goes_to_urgence(self):
        plan = self.engine.generate_plan([{"label": "pulpite", "fdi": "16"}])
        assert len(plan["phases"]["URGENCE"]) == 1

    def test_detartrage_goes_to_initiale(self):
        plan = self.engine.generate_plan([{"label": "détartrage", "fdi": "Global"}])
        assert len(plan["phases"]["INITIALE"]) == 1

    def test_implant_goes_to_rehabilitation(self):
        plan = self.engine.generate_plan([{"label": "implant", "fdi": "46"}])
        assert len(plan["phases"]["REHABILITATION"]) == 1
        assert plan["phases"]["REHABILITATION"][0]["estimated_cost"] == 8000.0

    def test_unknown_label_goes_to_maintenance(self):
        plan = self.engine.generate_plan([{"label": "bilan_paro", "fdi": "Global"}])
        assert len(plan["phases"]["MAINTENANCE"]) == 1

    def test_total_cost_aggregated(self):
        detections = [
            {"label": "carie", "fdi": "36"},   # 400
            {"label": "implant", "fdi": "46"},  # 8000
        ]
        plan = self.engine.generate_plan(detections)
        assert plan["total_cost"] == 8400.0

    def test_diagnosis_capitalized(self):
        plan = self.engine.generate_plan([{"label": "carie", "fdi": "36"}])
        act = plan["phases"]["CONSERVATRICE"][0]
        assert act["diagnosis"] == "Carie"

    def test_suggested_act_carie(self):
        plan = self.engine.generate_plan([{"label": "carie", "fdi": "26"}])
        act = plan["phases"]["CONSERVATRICE"][0]
        assert "Obturation" in act["suggested_act"]

    def test_suggested_act_unknown_returns_examen(self):
        plan = self.engine.generate_plan([{"label": "xyz_unknown", "fdi": "11"}])
        act = plan["phases"]["MAINTENANCE"][0]
        assert "Examen approfondi" in act["suggested_act"]

    def test_empty_summary_message(self):
        plan = self.engine.generate_plan([])
        assert "Aucun traitement" in plan["summary"]

    def test_non_empty_summary_mentions_budget(self):
        plan = self.engine.generate_plan([{"label": "carie", "fdi": "36"}])
        assert "MAD" in plan["summary"]

    def test_multiple_detections_sorted_by_priority(self):
        # urgence (priority=1) should come before other phases
        detections = [
            {"label": "suivi", "fdi": "Global"},
            {"label": "abcès", "fdi": "11"},
        ]
        plan = self.engine.generate_plan(detections)
        assert len(plan["phases"]["URGENCE"]) == 1
        assert len(plan["phases"]["MAINTENANCE"]) == 1


class TestMapToPhase:
    def setup_method(self):
        self.engine = TreatmentPlanEngine()

    def test_infection_urgence(self):
        assert self.engine._map_to_phase("infection") == "URGENCE"

    def test_douleur_urgence(self):
        assert self.engine._map_to_phase("douleur") == "URGENCE"

    def test_extraction_initiale(self):
        assert self.engine._map_to_phase("extraction") == "INITIALE"

    def test_restauration_conservatrice(self):
        assert self.engine._map_to_phase("restauration") == "CONSERVATRICE"

    def test_bridge_rehabilitation(self):
        assert self.engine._map_to_phase("bridge") == "REHABILITATION"

    def test_couronne_rehabilitation(self):
        assert self.engine._map_to_phase("couronne") == "REHABILITATION"

    def test_unknown_maintenance(self):
        assert self.engine._map_to_phase("controle_annuel") == "MAINTENANCE"


class TestSuggestAct:
    def setup_method(self):
        self.engine = TreatmentPlanEngine()

    def test_carie_suggests_obturation(self):
        assert "Obturation" in self.engine._suggest_act("carie")

    def test_abces_suggests_drainage(self):
        assert "Drainage" in self.engine._suggest_act("abcès")

    def test_implant_suggests_pose(self):
        assert "implant" in self.engine._suggest_act("implant").lower()

    def test_unknown_suggests_examen(self):
        assert "Examen" in self.engine._suggest_act("xyz_unknown")
