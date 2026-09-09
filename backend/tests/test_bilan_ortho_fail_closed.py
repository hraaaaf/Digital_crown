"""Regression tests for the fail-closed orthodontic summary adapter."""

from backend import schemas
from backend.services.bilan_ortho_engine import BilanOrthoEngine


def _cephalo_result():
    return schemas.CephaloAnalysisResult.model_validate({
        "analysis_metadata": {
            "unit": "mm",
            "pixel_ratio": 0.2,
            "type": "COM_Skeletal",
            "cohort": "Non classé",
        },
        "metrics": {
            "analyse_dentaire": {"IMPA": {"valeur": 110.0}},
            "analyse_osseuse": {
                "SNA": {"valeur": 90.0},
                "SNB": {"valeur": 70.0},
                "ANB": {"valeur": 20.0},
                "Angle_de_Tweed": {"valeur": 45.0},
            },
            "analyse_esthetique": {},
        },
        "visual_debug": {},
        "t1_projection": {},
        "t2_projection": {},
        "ai_narrative": {},
        "clinical_data": {},
    })


def test_bilan_restates_raw_values_without_autonomous_diagnosis():
    result = BilanOrthoEngine().generate_bilan(
        _cephalo_result(),
        schemas.ClinicalData(ddm_reelle=-9.0),
        age=9,
        sex="M",
    )

    text = " ".join(
        result[key]
        for key in (
            "diagnostic_squelettique",
            "analyse_moulages",
            "synthese_diagnostique",
            "strategie_therapeutique",
        )
    ).lower()
    assert "anb = 20.0°" in text
    assert "impa = 110.0°" in text
    assert "classe ii" not in text
    assert "classe iii" not in text
    assert "hyperdiverg" not in text
    assert "hypodiverg" not in text
    assert "sévère" not in text
    assert "modérée" not in text
    assert "proalvéol" not in text
    assert "rétroalvéol" not in text


def test_bilan_never_invents_treatment():
    generated = BilanOrthoEngine().generate_bilan(_cephalo_result(), schemas.ClinicalData())
    assert "Aucune stratégie thérapeutique n'est générée automatiquement" in generated["strategie_therapeutique"]

    authored = BilanOrthoEngine().generate_bilan(
        _cephalo_result(),
        schemas.ClinicalData(plan_traitement="Plan saisi par le praticien"),
    )
    assert authored["strategie_therapeutique"] == "Plan saisi par le praticien"
