"""Safety certification for the cephalometric treatment/normative boundary."""
from pathlib import Path

from backend import schemas
from backend.services.cephalo_service import CephaloService, _remove_autonomous_treatment


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE = REPO_ROOT / "backend/services/cephalo_service.py"
SAFE_ENGINE = REPO_ROOT / "backend/services/cephalo_safe_engine.py"


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


def test_service_uses_safe_engine_and_defense_in_depth_boundary():
    source = SERVICE.read_text(encoding="utf-8")
    safe_source = SAFE_ENGINE.read_text(encoding="utf-8")
    assert "from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine" in source
    assert "from backend.services.cephalo_engine import cephalo_engine" not in source
    assert source.count("_remove_autonomous_treatment(result.model_dump())") == 2
    assert "final_data_dict = result.model_dump()" not in source
    assert "from backend.services.cephalo_engine import cephalo_engine as _legacy_cephalo_engine" in safe_source
    assert 'narrative.pop("strategie_therapeutique", None)' in safe_source


def test_safe_engine_quarantines_legacy_normative_authority_and_growth_projection():
    safe_source = SAFE_ENGINE.read_text(encoding="utf-8")
    assert "_neutralize_legacy_norms(payload)" in safe_source
    assert 'measurement["status"] = "N/A"' in safe_source
    assert "aucune interprétation normative locale autoritative" in safe_source
    assert 'payload["t1_projection"] = {}' in safe_source
    assert 'payload["t2_projection"] = {}' in safe_source


def test_safe_engine_behavior_removes_legacy_treatment_norms_and_growth(monkeypatch):
    import backend.services.cephalo_safe_engine as safe_module

    class FakeResult:
        def __init__(self, payload):
            self.payload = payload

        def model_dump(self):
            import copy
            return copy.deepcopy(self.payload)

        @classmethod
        def model_validate(cls, payload):
            return cls(payload)

    legacy_payload = {
        "metrics": {
            "analyse_osseuse": {
                "SNA": {
                    "valeur": 83.0,
                    "norm_mean": 82.0,
                    "norm_min": 80.0,
                    "norm_max": 84.0,
                    "status": "High",
                    "interpretation": "Prognathie",
                    "z_score": 1.0,
                }
            }
        },
        "ai_narrative": {
            "diagnostic_squelettique": "legacy observation",
            "strategie_therapeutique": "Twin Block / Damon / chirurgie",
        },
        "t1_projection": {"A": [1.0, 2.0]},
        "t2_projection": {"B": [3.0, 4.0]},
        "clinical_data": {"plan_traitement": "Plan praticien"},
    }

    monkeypatch.setattr(
        safe_module._legacy_cephalo_engine,
        "calculate_metrics",
        lambda *args, **kwargs: FakeResult(legacy_payload),
    )

    result = safe_module.SafeCephaloEngine().calculate_metrics({}).payload
    measurement = result["metrics"]["analyse_osseuse"]["SNA"]

    assert measurement["valeur"] == 83.0
    assert measurement["status"] == "N/A"
    assert measurement["norm_mean"] is None
    assert measurement["norm_min"] is None
    assert measurement["norm_max"] is None
    assert measurement["z_score"] is None
    assert "strategie_therapeutique" not in result["ai_narrative"]
    assert result["t1_projection"] == {}
    assert result["t2_projection"] == {}
    assert result["clinical_data"]["plan_traitement"] == "Plan praticien"


def test_practitioner_payload_is_not_sanitized():
    source = SERVICE.read_text(encoding="utf-8")
    assert 'final_data_dict["ai_diagnostic"] = ai_diagnostic' in source
    assert "_remove_autonomous_treatment(ai_diagnostic" not in source
    assert 'clinical_data.pop("plan_traitement"' not in source


def test_clinical_ddm_is_not_modified_by_impa():
    clinical = schemas.ClinicalData(
        ddm_maxillaire=schemas.DDMComponent(espace_disponible=0, espace_necessaire=0, calcul_ddm=-2.5),
        ddm_mandibulaire=schemas.DDMComponent(espace_disponible=0, espace_necessaire=0, calcul_ddm=-3.0),
    )
    result = CephaloService._calculate_complex_ddm(None, None, clinical)
    assert result.ddm_maxillaire.calcul_ddm == -2.5
    assert result.ddm_mandibulaire.calcul_ddm == -3.0
    assert result.ddm_maxillaire.calcul_ddm_reelle is None
    assert result.ddm_mandibulaire.calcul_ddm_reelle is None
    assert result.ddm_reelle == -5.5


def test_service_contains_no_impa_space_conversion_formula():
    source = SERVICE.read_text(encoding="utf-8")
    assert "(impa - 90) / 2.5" not in source
    assert "2.5°" not in source
