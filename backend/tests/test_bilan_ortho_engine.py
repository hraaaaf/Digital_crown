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


def test_uncalibrated_partial_analysis_keeps_angular_information_only():
    analysis = _analysis(**{"analyse_osseuse.ANB": 5.0})
    result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData())
    assert "Classe II" in result["synthese_diagnostique"]
    assert "2.3" not in result["synthese_diagnostique"]
    assert "4.0" not in result["strategie_therapeutique"]


def test_complete_analysis_keeps_existing_classification_behavior():
    analysis = _analysis(**{
        "analyse_osseuse.Decalage_A_B": 8.0,
        "analyse_osseuse.ANB": 5.0,
        "analyse_osseuse.Angle_de_Tweed": 32.0,
        "analyse_dentaire.IMPA": 100.0,
    })
    result = BilanOrthoEngine().generate_bilan(analysis, schemas.ClinicalData(ddm_reelle=-8.0))
    assert "Classe II" in result["synthese_diagnostique"]
    assert "hyperdivergente" in result["diagnostic_squelettique"]
    assert "IMPA = 100.0" in result["diagnostic_squelettique"]