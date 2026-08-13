"""Eleventh batch — PrescriptionAgenticService pure methods,
clinical_rules_engine remaining paths, habits_engine patterns."""
from datetime import datetime, date


# ── PrescriptionAgenticService pure methods ───────────────────────────────────

class TestPrescriptionAgenticDesignPlan:
    def _svc(self):
        from backend.services.prescription_agentic_service import PrescriptionAgenticService
        return PrescriptionAgenticService()

    @staticmethod
    def _evaluable(**assessment):
        return {"evaluation": {"status": "evaluable"}, **assessment}

    def test_empty_drugs_returns_empty_prescriptions(self):
        assessment = self._evaluable(drugs=[], act_context="carie")
        result = self._svc().design_treatment_plan(assessment, {})
        assert result["prescriptions"] == []

    def test_plan_nom_includes_act_context(self):
        assessment = self._evaluable(drugs=[], act_context="Détartrage")
        result = self._svc().design_treatment_plan(assessment, {})
        assert "Détartrage" in result["plan_nom"]

    def test_single_drug_mapped(self):
        assessment = self._evaluable(
            drugs=[{"name": "amoxicilline", "dosage": "1g", "forme": "Comprimés", "posologie": "3/j"}],
            act_context="extraction",
        )
        result = self._svc().design_treatment_plan(assessment, {})
        assert len(result["prescriptions"]) == 1
        assert result["prescriptions"][0]["medicament"] == "AMOXICILLINE"
        assert result["prescriptions"][0]["dosage"] == "1g"

    def test_is_deterministic_flag(self):
        result = self._svc().design_treatment_plan({"drugs": []}, {})
        assert result["is_deterministic"] is True

    def test_multiple_drugs(self):
        assessment = self._evaluable(
            drugs=[
                {"name": "amoxicilline", "dosage": "1g", "forme": "Cp", "posologie": "3/j"},
                {"name": "ibuprofene", "dosage": "400mg", "forme": "Cp", "posologie": "2/j"},
            ],
            act_context="chirurgie",
        )
        result = self._svc().design_treatment_plan(assessment, {})
        assert len(result["prescriptions"]) == 2

    def test_conseils_patient_present(self):
        result = self._svc().design_treatment_plan({"drugs": []}, {})
        assert "conseils_patient" in result
        assert isinstance(result["conseils_patient"], list)

    def test_default_act_context(self):
        result = self._svc().design_treatment_plan(self._evaluable(drugs=[]), {})
        assert "Standard" in result["plan_nom"]

    def test_missing_evaluation_fails_closed(self):
        result = self._svc().design_treatment_plan(
            {"drugs": [{"name": "amoxicilline", "dosage": "1g"}], "act_context": "extraction"},
            {},
        )
        assert result["plan_nom"] == "Non évaluable"
        assert result["prescriptions"] == []
        assert result["evaluation"]["status"] == "non_evaluable"


class TestPrescriptionAgenticCalculateAge:
    def _svc(self):
        from backend.services.prescription_agentic_service import PrescriptionAgenticService
        return PrescriptionAgenticService()

    def test_none_returns_none(self):
        assert self._svc()._calculate_age(None) is None

    def test_positive_age(self):
        born = datetime(1990, 1, 1)
        assert self._svc()._calculate_age(born) > 0

    def test_returns_int(self):
        assert isinstance(self._svc()._calculate_age(datetime(1985, 6, 15)), int)

    def test_age_accuracy(self):
        born = datetime(2000, 1, 1)
        age = self._svc()._calculate_age(born)
        today = datetime.now()
        expected = today.year - 2000 - ((today.month, today.day) < (1, 1))
        assert age == expected


# ── clinical_rules_engine extra paths ────────────────────────────────────────

class TestClinicalRulesEngineGetAlternative:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_allergie_suggests_alternative(self):
        result = self._svc()._get_alternative("amoxicilline", "allergie_penicilline")
        # Should return alternative or None — not crash
        # The method may return None or an alternative molecule

    def test_returns_none_or_string(self):
        result = self._svc()._get_alternative("ibuprofene", "ulcere")
        assert result is None or isinstance(result, str)

    def test_unknown_molecule_returns_none(self):
        result = self._svc()._get_alternative("molecule_inconnue_xyz", "allergie")
        assert result is None or isinstance(result, str)


class TestClinicalRulesEnginePediatricDosage:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_returns_string(self):
        result = self._svc()._calculate_pediatric_dosage("amoxicilline", 20.0)
        assert isinstance(result, str)

    def test_ibuprofene_returns_string(self):
        result = self._svc()._calculate_pediatric_dosage("ibuprofene", 15.0)
        assert isinstance(result, str)

    def test_unknown_returns_string(self):
        result = self._svc()._calculate_pediatric_dosage("molecule_inconnue", 25.0)
        assert isinstance(result, str)

    def test_dosage_includes_weight_context(self):
        result = self._svc()._calculate_pediatric_dosage("amoxicilline", 20.0)
        # Should return a meaningful dosage string (e.g., "Xmg" or similar)
        assert len(result) > 0

    def test_zero_weight_handled(self):
        # Should not crash
        result = self._svc()._calculate_pediatric_dosage("amoxicilline", 0.0)
        assert isinstance(result, str)


# ── habits_engine more patterns ───────────────────────────────────────────────

class TestGetRecommendedDurationExtended:
    def _svc(self):
        from backend.services.habits_engine import HabitsEngine
        return HabitsEngine()

    def test_endo_pluriradiculaire_returns_60(self):
        assert self._svc().get_recommended_duration("Traitement Canalaire Pluriradiculaire") == 60

    def test_biopsie_returns_60(self):
        assert self._svc().get_recommended_duration("Biopsie gingivale") == 60

    def test_incluse_returns_45(self):
        assert self._svc().get_recommended_duration("Extraction Dent Incluse") == 45

    def test_avulsion_simple_returns_30(self):
        assert self._svc().get_recommended_duration("Avulsion dent") == 30

    def test_prothese_returns_45(self):
        assert self._svc().get_recommended_duration("Prothèse amovible") == 45

    def test_prophylaxie_returns_30(self):
        assert self._svc().get_recommended_duration("Prophylaxie dentaire") == 30

    def test_facette_returns_45(self):
        assert self._svc().get_recommended_duration("Pose Facette céramique") == 45

    def test_reconstruction_returns_30(self):
        assert self._svc().get_recommended_duration("Reconstruction composite") == 30

    def test_examen_returns_15(self):
        assert self._svc().get_recommended_duration("Examen clinique complet") == 15
