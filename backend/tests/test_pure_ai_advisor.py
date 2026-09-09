"""Safety contract for the legacy cephalometric AIAdvisor compatibility adapter."""

from backend.services.ai_advisor import AIAdvisor
from backend.schemas.clinical import (
    AnalysisMetadata,
    AnalysisMetrics,
    CephaloAnalysisResult,
    ClinicalData,
    DentalAnalysis,
    MeasureData,
    SkeletalAnalysis,
)


def _make_result() -> CephaloAnalysisResult:
    return CephaloAnalysisResult(
        analysis_metadata=AnalysisMetadata(pixel_ratio=1.0, cohort="Adulte"),
        metrics=AnalysisMetrics(
            analyse_osseuse=SkeletalAnalysis(
                ANB=MeasureData(valeur=12.0, status="High"),
                Angle_de_Tweed=MeasureData(valeur=40.0, status="High"),
            ),
            analyse_dentaire=DentalAnalysis(
                IMPA=MeasureData(valeur=120.0, status="High"),
                I_Francfort=MeasureData(valeur=125.0, status="High"),
                Surplomb=MeasureData(valeur=12.0, status="High"),
                Recouvrement=MeasureData(valeur=-4.0, status="Low"),
            ),
        ),
        visual_debug={},
        t1_projection={},
        t2_projection={},
        clinical_data=ClinicalData(),
    )


def test_model_identifies_fail_closed_compatibility_mode():
    assert AIAdvisor().model_name == "scientific-core-fail-closed"


def test_generate_diagnostic_preserves_raw_measurements_without_autonomous_diagnosis():
    out = AIAdvisor().generate_diagnostic(_make_result(), age=30, sex="F")
    assert "ANB = 12.0" in out["diagnostic_squelettique"]
    assert "Tweed = 40.0" in out["diagnostic_squelettique"]
    assert "IMPA = 120.0" in out["analyse_dentaire"]
    assert "Aucune interprétation diagnostique autonome" in out["diagnostic_squelettique"]


def test_generate_diagnostic_never_selects_treatment_appliance_mechanics_imaging_or_surgery():
    out = AIAdvisor().generate_diagnostic(_make_result())
    text = " ".join(str(value) for value in out.values()).lower()
    forbidden = (
        "damon", "invisalign", "twin block", "tad", "mini-vis", "cbct", "irm",
        "bsso", "ostéotomie", "extraction de", "élastiques de classe",
    )
    for term in forbidden:
        assert term not in text
    assert "aucune stratégie thérapeutique n'est générée automatiquement" in out["strategie_therapeutique"].lower()


def test_missing_measurements_remain_missing_not_normalized_to_norms():
    result = _make_result()
    result.metrics.analyse_osseuse.ANB.valeur = None
    result.metrics.analyse_osseuse.Angle_de_Tweed.valeur = None
    result.metrics.analyse_dentaire.IMPA.valeur = None
    result.metrics.analyse_dentaire.I_Francfort.valeur = None
    result.metrics.analyse_dentaire.Surplomb.valeur = None
    result.metrics.analyse_dentaire.Recouvrement.valeur = None
    out = AIAdvisor().generate_diagnostic(result)
    assert "Aucune mesure céphalométrique exploitable documentée." in out["diagnostic_squelettique"]
    assert "90" not in out["analyse_dentaire"]
    assert "107" not in out["analyse_dentaire"]


def test_use_slm_flag_cannot_change_deterministic_fail_closed_output():
    advisor = AIAdvisor()
    result = _make_result()
    assert advisor.generate_diagnostic(result, use_slm=False) == advisor.generate_diagnostic(result, use_slm=True)
