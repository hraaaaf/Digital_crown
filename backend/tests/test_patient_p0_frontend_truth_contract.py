"""Static P0 contracts for Patient frontend safety boundaries.

These assertions deliberately protect high-risk architectural invariants that do
not require a browser to verify: clinical truth must not silently fall back to
localStorage, assistant output must remain practitioner-gated, and commercial
patient scoring must not re-enter the clinical header.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLINICAL_HUB = ROOT / "frontend/src/features/patients/components/ClinicalHub.tsx"
PATIENT_DETAILS = ROOT / "frontend/src/features/patients/PatientDetailsInner.tsx"
RVG_SERVICE = ROOT / "frontend/src/services/rvgService.ts"
RVG_CARD = ROOT / "frontend/src/features/patients/components/RvgCard.tsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_clinical_hub_has_no_authoritative_clinical_localstorage_fallbacks():
    source = _read(CLINICAL_HUB)

    assert "master_plan_" not in source
    assert "diag_${patientId}" not in source
    assert "pending_devis_plan" not in source
    assert "scientificOrder" not in source
    assert "Consultation & Bilan complet" not in source
    assert "Détartrage & Surfaçage" not in source


def test_clinical_hub_assistant_output_is_practitioner_gated_and_does_not_mutate_plan():
    source = _read(CLINICAL_HUB)

    assert "Validation du praticien requise" in source
    assert "Proposition clinique à valider" in source
    assert "const handleWizardComplete" in source
    assert "_steps: any[]" in source
    assert "savePlan(combined)" not in source
    assert "setTreatmentPlan(combined)" not in source


def test_clinical_hub_backend_plan_is_truthful_on_load_save_error_and_empty_state():
    source = _read(CLINICAL_HUB)

    assert "api.get(`/patients/${patientId}/master-plan`)" in source
    assert "await api.put(`/patients/${patientId}/master-plan`, payload)" in source
    assert "Aucune donnée locale n'est utilisée comme remplacement" in source
    assert "La modification n'a pas été enregistrée" in source
    assert "Aucune étape de traitement enregistrée" in source


def test_odontogram_local_state_is_explicitly_draft_only_until_backend_contract_exists():
    source = _read(CLINICAL_HUB)

    assert "odontogram_state_${patientId}" in source
    assert "Brouillon local non enregistré au dossier" in source


def test_commercial_patient_score_is_absent_from_clinical_header():
    source = _read(PATIENT_DETAILS)

    assert "PatientScoreBadge" not in source
    assert "show_patient_badges" not in source


def test_rvg_frontend_never_builds_tokenized_download_urls():
    service = _read(RVG_SERVICE)
    card = _read(RVG_CARD)

    assert "?token=" not in service
    assert "?token=" not in card
    assert "fetchRVGBlob" in service
    assert "useAuthenticatedImage" in card
