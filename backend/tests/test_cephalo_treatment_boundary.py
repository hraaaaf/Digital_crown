"""Safety certification for the cephalometric treatment boundary."""
from pathlib import Path

from backend.services.cephalo_service import _remove_autonomous_treatment


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE = REPO_ROOT / "backend/services/cephalo_service.py"


def test_engine_strategy_is_removed_without_losing_observations_or_practitioner_data():
    payload = {
        "ai_narrative": {
            "diagnostic_squelettique": "observation",
            "strategie_therapeutique": "AUTO TREATMENT",
        },
        "clinical_data": {
            "plan_traitement": "Plan praticien",
            "ddm_reelle": -4.0,
        },
        "metrics": {"SNA": 82.0},
    }

    result = _remove_autonomous_treatment(payload)

    assert "strategie_therapeutique" not in result["ai_narrative"]
    assert result["ai_narrative"]["diagnostic_squelettique"] == "observation"
    assert result["clinical_data"]["plan_traitement"] == "Plan praticien"
    assert result["clinical_data"]["ddm_reelle"] == -4.0
    assert result["metrics"] == {"SNA": 82.0}


def test_service_applies_boundary_to_new_and_refined_analysis():
    source = SERVICE.read_text(encoding="utf-8")

    # Both process_new_radio and refine_analysis must sanitize the engine dump.
    assert source.count("_remove_autonomous_treatment(result.model_dump())") == 2
    assert "final_data_dict = result.model_dump()" not in source


def test_practitioner_payload_is_not_sanitized():
    source = SERVICE.read_text(encoding="utf-8")

    # Explicitly supplied practitioner content remains a separate payload.
    assert 'final_data_dict["ai_diagnostic"] = ai_diagnostic' in source
    assert "_remove_autonomous_treatment(ai_diagnostic" not in source
    assert 'clinical_data.pop("plan_traitement"' not in source
