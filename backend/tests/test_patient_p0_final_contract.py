from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_p0_clinicalhub_has_no_fabricated_clinical_truth():
    hub = _read("frontend/src/features/patients/components/ClinicalHub.tsx")
    for banned in (
        "Détartrage & Surfaçage",
        "scientificOrder",
        "pending_devis_plan",
        "Diagnostic intelligent, plan de traitement global et suivi automatisé.",
    ):
        assert banned not in hub
    assert "Aucune étape de traitement enregistrée." in hub
    assert "Proposition à valider" in hub
    assert "Une proposition d’assistant ne devient jamais une conclusion sans cette action explicite." in hub
    assert "patientClinicalPersistence.createConclusion" in hub


def test_p0_all_clinical_assistants_are_proposal_only():
    root = ROOT / "frontend/src/features/patients/components/wizards"

    # Standard assistants emit a narrative summary with an explicitly empty plan.
    standard_assistants = (
        "AssistantATM.tsx",
        "AssistantGeneral.tsx",
        "AssistantOrtho.tsx",
        "AssistantParo.tsx",
        "AssistantProthese.tsx",
        "AssistantEndo.tsx",
        "AssistantChirurgie.tsx",
        "AssistantPedo.tsx",
        "AssistantPatho.tsx",
    )
    for filename in standard_assistants:
        source = (root / filename).read_text(encoding="utf-8")
        assert "onComplete(summary, [])" in source
        assert "/prescriptions" not in source
        assert "/accounting" not in source
        assert "/master-plan" not in source

    # Complete examination returns observations with no treatment steps / next action.
    complete = (root / "AssistantExamenComplet.tsx").read_text(encoding="utf-8")
    assert "steps: [], next: null" in complete
    assert "ne pose pas automatiquement de diagnostic" in complete
    assert "décision du praticien" in complete
