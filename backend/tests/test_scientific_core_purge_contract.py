from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dormant_treatment_plan_engine_is_removed():
    assert not (ROOT / "backend/services/treatment_plan_engine.py").exists()

    for relative in (
        "backend/services/elite_manager.py",
        "backend/routers/ia.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "treatment_plan_engine" not in source
        assert "TreatmentPlanEngine" not in source


def test_patient_plan_generation_remains_fail_closed():
    source = (ROOT / "backend/services/elite_manager.py").read_text(encoding="utf-8")
    assert "Génération automatique du plan de traitement désactivée" in source
