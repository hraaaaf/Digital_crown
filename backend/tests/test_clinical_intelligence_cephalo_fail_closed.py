"""Regression contract for the clinical-intelligence cephalometric boundary."""
from pathlib import Path

from backend.services.clinical_intelligence import _extract_raw_cephalo_measurements


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend/services/clinical_intelligence.py"


def test_clinical_intelligence_has_no_retired_cephalo_advisor_or_autonomous_strategy():
    source = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "backend.services.ai_advisor",
        "ai_advisor.generate_diagnostic",
        "Synthèse Diagnostique",
        "Stratégie Thérapeutique (COM)",
        "if age < 14",
    )
    for token in forbidden:
        assert token not in source, f"unsafe clinical-intelligence cephalo semantic reintroduced: {token}"


def test_raw_cephalo_extraction_ignores_normative_metadata():
    data = {
        "analyse_osseuse": {
            "ANB": {
                "valeur": 5.0,
                "norm_mean": 2.0,
                "norm_min": 0.0,
                "norm_max": 4.0,
                "z_score": 3.0,
                "status": "Pathologique",
                "interpretation": "Classe II",
            }
        }
    }
    values = _extract_raw_cephalo_measurements(data)
    assert values == ["ANB = 5.0"]


def test_full_diagnostic_contract_is_explicitly_fail_closed():
    source = SOURCE.read_text(encoding="utf-8")
    assert "Données céphalométriques brutes" in source
    assert "Aucune norme locale, classification diagnostique, indication ou stratégie thérapeutique" in source
    assert '"confidence": None' in source
    assert '"requires_validation": True' in source
