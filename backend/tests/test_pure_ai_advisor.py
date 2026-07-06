"""Unit tests for services/ai_advisor.py — pure NLG rule engine, no DB required."""
import pytest
from backend.services.ai_advisor import AIAdvisor, ClinicalNorms
from backend.schemas.clinical import (
    CephaloAnalysisResult, AnalysisMetrics, AnalysisMetadata,
    SkeletalAnalysis, DentalAnalysis, MeasureData,
)
from backend.schemas import ClinicalData


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
        assert norms["ab_mean"] == 2.3
        assert norms["tweed_default"] == 26

    def test_child_norms_returned(self):
        norms = ClinicalNorms.get(is_child=True)
        assert norms["ab_mean"] == 4.2
        assert norms["ab_dev"] == 3.2


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

    def test_class_i_normal(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="Normal", ab_value=2.3))
        assert "Classe I" in out["diagnostic_squelettique"]
        assert "normosquelettique" in out["diagnostic_squelettique"]

    def test_class_ii_moderate(self):
        # ab_value = 6.0 < severe_cl2 (2.3 + 2*3.1 = 8.5)
        out = self.advisor.generate_diagnostic(_make_result(ab_status="High", ab_value=6.0))
        assert "Classe II modérée" in out["diagnostic_squelettique"]

    def test_class_ii_severe(self):
        # ab_value = 10.0 > severe_cl2 (8.5)
        out = self.advisor.generate_diagnostic(_make_result(ab_status="High", ab_value=10.0))
        assert "Classe II sévère" in out["diagnostic_squelettique"]

    def test_class_iii_moderate(self):
        # ab_value = -1.0 > severe_cl3 (2.3 - 2*3.1 = -3.9)
        out = self.advisor.generate_diagnostic(_make_result(ab_status="Low", ab_value=-1.0))
        assert "Classe III modérée" in out["diagnostic_squelettique"]

    def test_class_iii_severe(self):
        # ab_value = -5.0 < severe_cl3 (-3.9)
        out = self.advisor.generate_diagnostic(_make_result(ab_status="Low", ab_value=-5.0))
        assert "Classe III sévère" in out["diagnostic_squelettique"]

    def test_hyperdivergent(self):
        out = self.advisor.generate_diagnostic(_make_result(tweed_status="High", tweed_value=35.0))
        assert "hyperdivergente" in out["diagnostic_squelettique"]

    def test_hypodivergent(self):
        out = self.advisor.generate_diagnostic(_make_result(tweed_status="Low", tweed_value=18.0))
        assert "hypodivergente" in out["diagnostic_squelettique"]

    def test_normodivergent(self):
        out = self.advisor.generate_diagnostic(_make_result(tweed_status="Normal", tweed_value=26.0))
        assert "normodivergent" in out["diagnostic_squelettique"]

    def test_prognathic_maxilla(self):
        # sit_a_value > sit_a_mean + sit_a_dev = 2.3 + 3.0 = 5.3
        out = self.advisor.generate_diagnostic(_make_result(sit_a_value=7.0))
        assert "prognathique" in out["diagnostic_squelettique"]

    def test_retrognathic_maxilla(self):
        # sit_a_value < sit_a_mean - sit_a_dev = 2.3 - 3.0 = -0.7
        out = self.advisor.generate_diagnostic(_make_result(sit_a_value=-2.0))
        assert "rétrognathique" in out["diagnostic_squelettique"]

    def test_prognathic_mandible(self):
        # sit_b_value > sit_b_mean + sit_b_dev = 0 + 4.9 = 4.9
        out = self.advisor.generate_diagnostic(_make_result(sit_b_value=6.0))
        assert "prognathique" in out["diagnostic_squelettique"]

    def test_normal_bases_message(self):
        out = self.advisor.generate_diagnostic(_make_result(sit_a_value=2.3, sit_b_value=0.0))
        assert "bases osseuses bien positionnées" in out["diagnostic_squelettique"]


class TestDentalDiagnostic:
    def setup_method(self):
        self.advisor = AIAdvisor()

    def test_impa_normal(self):
        out = self.advisor.generate_diagnostic(_make_result(impa_status="Normal", impa_value=90.0))
        assert "bien positionnées" in out["analyse_dentaire"]

    def test_impa_high_vestibuloversee(self):
        out = self.advisor.generate_diagnostic(_make_result(impa_status="High", impa_value=98.0))
        assert "vestibuloversée" in out["analyse_dentaire"]

    def test_impa_low_linguoversee(self):
        out = self.advisor.generate_diagnostic(_make_result(impa_status="Low", impa_value=82.0))
        assert "linguoversée" in out["analyse_dentaire"]

    def test_if_high_proalveolie(self):
        out = self.advisor.generate_diagnostic(_make_result(if_status="High", if_value=115.0))
        assert "proalvéolie maxillaire" in out["analyse_dentaire"]

    def test_if_low_retroalveolie(self):
        out = self.advisor.generate_diagnostic(_make_result(if_status="Low", if_value=99.0))
        assert "rétroalvéolie maxillaire" in out["analyse_dentaire"]

    def test_surplomb_increased(self):
        out = self.advisor.generate_diagnostic(_make_result(surplomb=5.0))
        assert "overjet" in out["analyse_dentaire"]

    def test_recouvrement_deep_bite(self):
        out = self.advisor.generate_diagnostic(_make_result(recouv=5.0))
        assert "deep bite" in out["analyse_dentaire"]

    def test_impa_compensated_mention(self):
        result = _make_result(impa_status="Compensated")
        # Add plage_compensation
        result.metrics.analyse_dentaire.IMPA.plage_compensation = (85.0, 95.0)
        out = self.advisor.generate_diagnostic(result)
        assert "compensation dento-alvéolaire" in out["analyse_dentaire"]


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

    def test_class_ii_child_propulsion(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="High", ab_value=6.0, cohort="Enfant (10 ans)"))
        assert "propulsion mandibulaire" in out["strategie_therapeutique"]

    def test_class_ii_adult_severe_surgical(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="High", ab_value=10.0, cohort="Adulte"))
        assert "chirurgicale" in out["strategie_therapeutique"]

    def test_class_ii_adult_moderate_compensation(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="High", ab_value=6.0, cohort="Adulte"))
        assert "extractions" in out["strategie_therapeutique"]

    def test_class_iii_child_mask(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="Low", ab_value=-1.0, cohort="Enfant (9 ans)"))
        assert "asque facial" in out["strategie_therapeutique"]

    def test_class_iii_adult_lefort(self):
        out = self.advisor.generate_diagnostic(_make_result(ab_status="Low", ab_value=-2.0, cohort="Adulte"))
        assert "Lefort" in out["strategie_therapeutique"]

    def test_hyperdivergent_vertical_control_warning(self):
        out = self.advisor.generate_diagnostic(_make_result(tweed_status="High", tweed_value=35.0))
        assert "vertical" in out["strategie_therapeutique"].lower()

    def test_impa_high_adult_retroclinaison(self):
        out = self.advisor.generate_diagnostic(_make_result(impa_status="High", impa_value=98.0, cohort="Adulte"))
        assert "Rétroclinaison" in out["strategie_therapeutique"]

    def test_means_section_present(self):
        out = self.advisor.generate_diagnostic(_make_result())
        assert "MOYENS PROPOSÉS" in out["strategie_therapeutique"]

    def test_child_functional_appliance(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Enfant (9 ans)"))
        assert "fonctionnel" in out["strategie_therapeutique"]

    def test_adult_multiattaches(self):
        out = self.advisor.generate_diagnostic(_make_result(cohort="Adulte"))
        assert "Multi-attaches" in out["strategie_therapeutique"]

    def test_none_values_use_defaults(self):
        result = _make_result()
        result.metrics.analyse_osseuse.Decalage_A_B.valeur = None
        result.metrics.analyse_osseuse.Angle_de_Tweed.valeur = None
        result.metrics.analyse_dentaire.IMPA.valeur = None
        out = self.advisor.generate_diagnostic(result)
        # Should not raise, should use defaults from norms
        assert "diagnostic_squelettique" in out
