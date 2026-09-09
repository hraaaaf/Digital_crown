from backend import schemas
from backend.services.bilan_ortho_engine import BilanOrthoEngine


def _analysis(**values):
    metrics = schemas.AnalysisMetrics()
    for name, value in values.items():
        section, metric = name.split(".")
        getattr(metrics, section).__getattribute__(metric).valeur = value
    return schemas.CephaloAnalysisResult(
        analysis_metadata=schemas.AnalysisMetadata(cohort="Adulte"),
        metrics=metrics,
        visual_debug={},
        t1_projection={},
        t2_projection={},
        clinical_data=schemas.ClinicalData(),
    )


def test_missing_linear_measurement_does_not_create_sagittal_conclusion():
    result = BilanOrthoEngine().generate_bilan(_analysis(), schemas.ClinicalData())
    assert "2.3" not in result["synthese_diagnostique"]
    assert "4.0" not in result["strategie_therapeutique"]
    assert "Classe I" not in result["synthese_diagnostique"]


def test_zero_values_are_preserved_without_clinical_fallbacks():
    analysis = _analysis(**{
        "analyse_osseuse.Decalage_A_B": 0.0,
        "analyse_osseuse.ANB": 0.0,
        "analyse_osseuse.Angle_de_Tweed": 0.0,
        "analyse_dentaire.IMPA": 0.0,
    })
    result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData(ddm_reelle=0.0))
    assert "IMPA = 0.0" in result["diagnostic_squelettique"]
    assert "Tweed = 0.0" in result["diagnostic_squelettique"]
    assert "IMPA = 90" not in result["diagnostic_squelettique"]
    assert "Tweed = 26" not in result["diagnostic_squelettique"]


def test_missing_angular_values_do_not_fabricate_normal_values():
    result = BilanOrthoEngine().generate_bilan(_analysis(), schemas.ClinicalData())
    assert "IMPA = 90" not in result["diagnostic_squelettique"]
    assert "Tweed = 26" not in result["diagnostic_squelettique"]
    assert "Classe I" not in result["synthese_diagnostique"]


def test_uncalibrated_partial_analysis_exposes_raw_anb_only():
    analysis = _analysis(**{"analyse_osseuse.ANB": 5.0})
    result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData())
    assert "Classe II" not in result["synthese_diagnostique"]
    assert "ANB = 5.0" in result["diagnostic_squelettique"]
    assert "normative" not in result["diagnostic_squelettique"].lower()
    assert "2.3" not in result["synthese_diagnostique"]
    assert "4.0" not in result["strategie_therapeutique"]


def test_complete_analysis_exposes_raw_anb_tweed_and_impa_only():
    analysis = _analysis(**{
        "analyse_osseuse.Decalage_A_B": 8.0,
        "analyse_osseuse.ANB": 5.0,
        "analyse_osseuse.Angle_de_Tweed": 32.0,
        "analyse_dentaire.IMPA": 100.0,
    })
    result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData(ddm_reelle=-8.0))
    assert "Classe II" not in result["synthese_diagnostique"]
    assert "ANB = 5.0" in result["diagnostic_squelettique"]
    assert "Tweed = 32.0" in result["diagnostic_squelettique"]
    assert "IMPA = 100.0" in result["diagnostic_squelettique"]
    assert "hyperdivergente" not in result["diagnostic_squelettique"]
    assert "normative" not in result["diagnostic_squelettique"].lower()


def test_extreme_custom_ab_does_not_create_diagnosis_or_treatment():
    for ab_value in (100.0, -100.0):
        analysis = _analysis(**{"analyse_osseuse.Decalage_A_B": ab_value})
        result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData())
        text = " ".join(value for value in result.values() if isinstance(value, str))
        assert "Classe II" not in text
        assert "Classe III" not in text
        assert "Twin Block" not in text
        assert "BSSO" not in text
        assert "Le Fort I" not in text
