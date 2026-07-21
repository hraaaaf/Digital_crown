"""Unit tests for services/ai_advisor.py — pure NLG rule engine, no DB required."""
import pytest
from backend.services.ai_advisor import AIAdvisor, ClinicalNorms
from backend.schemas.clinical import (
    CephaloAnalysisResult, AnalysisMetrics, AnalysisMetadata,
    SkeletalAnalysis, DentalAnalysis, MeasureData,
)
from backend.schemas import ClinicalData
from backend.services.cephalo_normative_service import reset_cache


@pytest.fixture(autouse=True)
def _clean_cache():
    reset_cache()
    yield
    reset_cache()


def _make_result(
    ab_status="Normal", ab_value=2.3,
    tweed_status="Normal", tweed_value=26.0,
    sit_a_value=2.3, sit_b_value=0.0,
    impa_status="Normal", impa_value=90.0,
    if_status="Normal", if_value=107.0,
    surplomb=2.0, recouv=2.0,
    cohort="Adulte",
):
    return CephaloAnalysisResult(
        analysis_metadata=AnalysisMetadata(pixel_ratio=1.0, cohort=cohort),
        metrics=AnalysisMetrics(
            analyse_osseuse=SkeletalAnalysis(
                Decalage_A_B=MeasureData(valeur=ab_value, status=ab_status),
                Angle_de_Tweed=MeasureData(valeur=tweed_value, status=tweed_status),
                Situation_A=MeasureData(valeur=sit_a_value, status="Normal"),
                Situation_B=MeasureData(valeur=sit_b_value, status="Normal"),
            ),
            analyse_dentaire=DentalAnalysis(
                IMPA=MeasureData(valeur=impa_value, status=impa_status),
                I_Francfort=MeasureData(valeur=if_value, status=if_status),
                Surplomb=MeasureData(valeur=surplomb, status="Normal"),
                Recouvrement=MeasureData(valeur=recouv, status="Normal"),
            ),
        ),
        visual_debug={},
        t1_projection={},
        t2_projection={},
        clinical_data=ClinicalData(),
    )


class TestClinicalNorms:
    def test_adult_norms_returned(self):
        norms = ClinicalNorms.get(is_child=False)
        assert norms["a_mean"] == 2.3
        assert "tweed_default" not in norms

    def test_child_norms_returned(self):
        norms = ClinicalNorms.get(is_child=True)
        assert norms["a_mean"] == 2.8


class TestAIAdvisorInit:
    def test_model_name(self):
        advisor = AIAdvisor()
        assert advisor.model_name == "ghost-brain-nlg"


class TestGenerateDiagnostic:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_returns_four_keys(self):
        result = _make_result()
        out = self.advisor.generate_diagnostic(result)
        assert "diagnostic_squelettique" in out
        assert "analyse_dentaire" in out
        assert "strategie_therapeutique" in out
        assert "is_fallback" in out

    def test_is_fallback_always_false(self):
        out = self.advisor.generate_diagnostic(_make_result())
        assert out["is_fallback"] is False

    def test_use_slm_ignored(self):
        r = _make_result()
        out1 = self.advisor.generate_diagnostic(r, use_slm=False)
        out2 = self.advisor.generate_diagnostic(r, use_slm=True)
        assert out1 == out2


class TestSkeletalDiagnostic:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_extreme_custom_ab_does_not_generate_skeletal_classification(self):
        for ab_value, ab_status in ((100.0, "High"), (-100.0, "Low")):
            out = self.advisor.generate_diagnostic(_make_result(ab_status=ab_status, ab_value=ab_value))
            assert "A-B" not in out["diagnostic_squelettique"]
            assert "Classe II" not in out["diagnostic_squelettique"]
            assert "Classe III" not in out["diagnostic_squelettique"]
    def test_tweed_status_no_longer_drives_a_local_classification(self):
        # Tweed no longer classifies via the shared `.status` field (CEPHALOMETRY-
        # NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C) — the real registry has
        # no VALIDATED_FOR_PROFILE Tweed profile, so this stays a neutral, value-only
        # note regardless of what `.status` says.
        for status, value in (("High", 35.0), ("Low", 18.0), ("Normal", 26.0)):
            out = self.advisor.generate_diagnostic(_make_result(tweed_status=status, tweed_value=value))
            narrative = out["diagnostic_squelettique"]
            assert "hyperdivergente" not in narrative
            assert "hypodivergente" not in narrative
            assert "normodivergent" not in narrative
            assert f"Tweed = {value}° (référence normative non validée)." in narrative

    def test_situation_a_no_longer_classifies_via_local_norms(self):
        # Situation_A no longer classifies via local ClinicalNorms constants
        # (CEPHALOMETRY-FINAL-NORMATIVE-MIGRATION-5) — no prognathique/rétrognathique
        # claim regardless of value; raw value stated as non-validated.
        for value in (7.0, -2.0, 2.3):
            out = self.advisor.generate_diagnostic(_make_result(sit_a_value=value))
            narrative = out["diagnostic_squelettique"]
            assert "prognathique" not in narrative
            assert "rétrognathique" not in narrative
            assert "bases osseuses bien positionnées" not in narrative
            assert f"Situation A = {value} mm (référence normative non validée)." in narrative

    def test_extreme_situation_b_does_not_generate_mandibular_conclusion(self):
        for sit_b_value in (100.0, -100.0):
            out = self.advisor.generate_diagnostic(_make_result(sit_b_value=sit_b_value))
            assert "mandibule prognathique" not in out["diagnostic_squelettique"]
            assert "mandibule rétrognathique" not in out["diagnostic_squelettique"]


class TestDentalDiagnostic:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_impa_status_no_longer_drives_a_local_classification(self):
        # IMPA no longer classifies via the shared `.status` field (same 4C
        # mission as Tweed above) — neutral, value-only note regardless of status.
        for status, value in (("Normal", 90.0), ("High", 98.0), ("Low", 82.0)):
            out = self.advisor.generate_diagnostic(_make_result(impa_status=status, impa_value=value))
            narrative = out["analyse_dentaire"]
            assert "vestibuloversée" not in narrative
            assert "linguoversée" not in narrative
            assert "bien positionnées" not in narrative
            assert f"IMPA = {value}° (référence normative non validée)." in narrative

    def test_if_status_no_longer_drives_a_local_classification(self):
        for status, value in (("High", 115.0), ("Low", 99.0)):
            out = self.advisor.generate_diagnostic(_make_result(if_status=status, if_value=value))
            narrative = out["analyse_dentaire"]
            assert "proalvéolie maxillaire" not in narrative
            assert "rétroalvéolie maxillaire" not in narrative

    def test_surplomb_no_longer_classifies_via_local_cutoff(self):
        # Surplomb no longer classifies via a local raw>3 cutoff (CEPHALOMETRY-
        # FINAL-NORMATIVE-MIGRATION-5) — no overjet claim regardless of value.
        out = self.advisor.generate_diagnostic(_make_result(surplomb=5.0))
        assert "overjet" not in out["analyse_dentaire"]

    def test_recouvrement_no_longer_classifies_deep_bite_via_local_cutoff(self):
        out = self.advisor.generate_diagnostic(_make_result(recouv=5.0))
        assert "deep bite" not in out["analyse_dentaire"]
        assert "supraclusion" not in out["analyse_dentaire"]

    def test_impa_compensated_sentence_dropped_no_authoritative_equivalent(self):
        # The old "Compensated" sentence had no equivalent in the registry's IMPA
        # classification rule (a plain 2-threshold rule, no compensation concept) —
        # omitted rather than invented (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-
        # TWEED-IMPA-FRANCFORT-4C).
        result = _make_result(impa_status="Compensated")
        result.metrics.analyse_dentaire.IMPA.plage_compensation = (85.0, 95.0)
        out = self.advisor.generate_diagnostic(result)
        assert "compensation dento-alvéolaire" not in out["analyse_dentaire"]


class TestTherapeuticStrategy:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_strategy_contains_objectives(self):
        out = self.advisor.generate_diagnostic(_make_result())
        assert "OBJECTIFS THÉRAPEUTIQUES" in out["strategie_therapeutique"]

    def test_adult_strategy(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Adulte"))
        assert "adulte" in out["strategie_therapeutique"].lower()

    def test_child_strategy(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Enfant (10 ans)"))
        assert "croissance" in out["strategie_therapeutique"].lower()

    def test_extreme_custom_ab_does_not_generate_treatment_strategy(self):
        for ab_value, ab_status in ((100.0, "High"), (-100.0, "Low")):
            out = self.advisor.generate_diagnostic(_make_result(ab_status=ab_status, ab_value=ab_value))
            strategy = out["strategie_therapeutique"]
            assert "propulsion mandibulaire" not in strategy
            assert "BSSO" not in strategy
            assert "Lefort" not in strategy
            assert "Masque facial" not in strategy
    def test_tweed_status_no_longer_drives_vertical_control_warning(self):
        out = self.advisor.generate_diagnostic(_make_result(tweed_status="High", tweed_value=35.0))
        assert "vertical" not in out["strategie_therapeutique"].lower()

    def test_impa_status_no_longer_drives_retroclinaison(self):
        out = self.advisor.generate_diagnostic(_make_result(impa_status="High", impa_value=98.0, cohort="Adulte"))
        assert "Rétroclinaison" not in out["strategie_therapeutique"]

    def test_means_section_present(self):
        out = self.advisor.generate_diagnostic(_make_result())
        assert "MOYENS PROPOSÉS" in out["strategie_therapeutique"]

    def test_child_functional_appliance(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Enfant (9 ans)"))
        assert "fonctionnel" in out["strategie_therapeutique"]

    def test_adult_multiattaches(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Adulte"))
        assert "Multi-attaches" in out["strategie_therapeutique"]

    def test_none_values_are_not_reported_as_normals(self):
        result = _make_result()
        result.metrics.analyse_osseuse.Decalage_A_B.valeur = None
        result.metrics.analyse_osseuse.Angle_de_Tweed.valeur = None
        result.metrics.analyse_dentaire.IMPA.valeur = None
        out = self.advisor.generate_diagnostic(result)
        assert "A-B = 2.3 mm" not in out["diagnostic_squelettique"]
        assert "Tweed = 26" not in out["diagnostic_squelettique"]
        assert "IMPA = 90" not in out["analyse_dentaire"]


# ============================================================
# Age/sex reach the normative service (CEPHALOMETRY-NORMATIVE-BACKEND-
# WIRING-TWEED-IMPA-FRANCFORT-4C) — mirrors TestSexReachesContext in
# test_cephalo_normative_steiner_wiring.py, at the ai_advisor.py call site.
# ============================================================

class TestAgeSexReachTheService:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def _spy_and_capture(self, monkeypatch):
        import backend.services.ai_advisor as advisor_module
        captured = {}
        original = advisor_module.evaluate_measurement

        def _spy(measurement_id, raw_value, definition_version, context):
            captured[measurement_id] = context
            return original(measurement_id, raw_value, definition_version, context)

        monkeypatch.setattr(advisor_module, "evaluate_measurement", _spy)
        return captured

    def test_age_and_sex_reach_normative_context(self, monkeypatch):
        from backend.schemas.cephalo_normative import Sex
        captured = self._spy_and_capture(monkeypatch)
        self.advisor.generate_diagnostic(_make_result(), age=30, sex="F")
        assert captured["Angle_de_Tweed"].age == 30
        assert captured["Angle_de_Tweed"].sex == Sex.FEMALE
        assert captured["IMPA"].age == 30
        assert captured["I_Francfort"].sex == Sex.FEMALE

    def test_missing_age_sex_default_to_none(self, monkeypatch):
        captured = self._spy_and_capture(monkeypatch)
        self.advisor.generate_diagnostic(_make_result())
        assert captured["Angle_de_Tweed"].age is None
        assert captured["Angle_de_Tweed"].sex is None

    def test_unrecognized_sex_code_never_guessed(self, monkeypatch):
        captured = self._spy_and_capture(monkeypatch)
        self.advisor.generate_diagnostic(_make_result(), age=30, sex="AUTRE")
        assert captured["Angle_de_Tweed"].sex is None

    def test_population_id_always_none(self, monkeypatch):
        captured = self._spy_and_capture(monkeypatch)
        self.advisor.generate_diagnostic(_make_result(), age=30, sex="M")
        assert captured["Angle_de_Tweed"].population_id is None


# ============================================================
# Synthetic VALIDATED_FOR_PROFILE path — proves the wiring actually works
# (same population_id=None caveat as cephalo_engine.py's equivalent tests:
# these patch evaluate_measurement directly rather than the registry).
# DO NOT mark any real profile validated.
# ============================================================

from backend.services.cephalo_normative_service import NormativeEvaluationResult, NormativeEvaluationStatus


def _canned_hyperdivergent_result(measurement_id, raw_value, definition_version, context):
    if measurement_id == "Angle_de_Tweed":
        return NormativeEvaluationResult(
            measurement_id="Angle_de_Tweed", raw_value=raw_value, unit="degree",
            status=NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH,
            reason="synthetic test fixture", matched_profile_id="TWEED_SYNTHETIC_VALIDATED_V1",
            classification="Hyperdivergent",
        )
    return NormativeEvaluationResult(
        measurement_id=measurement_id, raw_value=raw_value, unit=None,
        status=NormativeEvaluationStatus.NO_PROFILE, reason="not part of this synthetic fixture",
    )


class TestSyntheticValidatedPathPropagates:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_diagnostic_uses_authoritative_label_when_service_says_so(self, monkeypatch):
        import backend.services.ai_advisor as advisor_module
        monkeypatch.setattr(advisor_module, "evaluate_measurement", _canned_hyperdivergent_result)
        out = self.advisor.generate_diagnostic(_make_result(tweed_value=35.0))
        assert "typologie hyperdivergente" in out["diagnostic_squelettique"]

    def test_strategy_reacts_to_authoritative_hyperdivergent(self, monkeypatch):
        import backend.services.ai_advisor as advisor_module
        monkeypatch.setattr(advisor_module, "evaluate_measurement", _canned_hyperdivergent_result)
        out = self.advisor.generate_diagnostic(_make_result(tweed_value=35.0))
        assert "Contrôle vertical strict impératif" in out["strategie_therapeutique"]
