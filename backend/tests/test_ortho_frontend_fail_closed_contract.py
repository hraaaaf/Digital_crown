"""Static safety contract for the orthodontic frontend scientific boundary.

The frontend may display measurements and practitioner-authored clinical text,
but it must not turn measurements into an autonomous diagnosis or treatment.
"""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERT_SYSTEM = REPO_ROOT / "frontend/src/features/ortho/orthoExpertSystem.ts"
STEP3 = REPO_ROOT / "frontend/src/features/ortho/components/Step3Clinical.tsx"
STEP4 = REPO_ROOT / "frontend/src/features/ortho/components/Step4Documents.tsx"
CEPHALO_UTILS = REPO_ROOT / "frontend/src/features/ortho/cephaloUtils.ts"
ORTHO_STORE = REPO_ROOT / "frontend/src/features/ortho/stores/useOrthoStore.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_expert_system_contains_no_autonomous_treatment_rules():
    source = _read(EXPERT_SYSTEM)
    forbidden = (
        "extrRecommandee", "High Torque", "Low Torque", "bite blocks", "Bite-Block",
        "élastiques de Classe II", "Distalisation", "CBCT/IRM", "Dents concernées",
        "EXTRACTIONNEL", "SANS EXTRACTION", "Prescription Autoligaturante",
    )
    for token in forbidden:
        assert token not in source, f"autonomous orthodontic treatment token reintroduced: {token}"
    assert "Décision thérapeutique : à documenter et valider par le praticien." in source
    assert "return { rapportMarkdown }" in source


def test_growth_and_class_ii_helpers_fail_closed():
    source = _read(EXPERT_SYSTEM)
    assert "export function deriveDentureFromAge" in source
    assert "export function deriveDivision" in source
    assert "return '';" in source
    assert "return null;" in source
    assert "surplomb >" not in source


def test_step3_is_practitioner_controlled_and_contains_no_local_clinical_thresholds():
    source = _read(STEP3)
    forbidden = (
        "evaluateCase(", "calcDDMReelle(", "deriveDivision(", "deriveDentureFromAge(",
        "autoSeverite", "autoDivision", "Morphologie Dentaire (Auto-Déduit)",
        "Bot Expert ODF", "Générer", "handleDiagChange('strategie_therapeutique', expertReport",
        "> 3.5 ? 'Supraclusie'", "> 4 ? 'Proalvéolie'", "DDM RÉELLE",
        "normal=", "mean=", "tol=", "Plan thérapeutique — décision praticien",
    )
    for token in forbidden:
        assert token not in source, f"unsafe Step3 semantic reintroduced: {token}"
    assert "Note thérapeutique libre legacy — hors R13/R14" in source
    assert "elle ne sélectionne aucune option R13 et ne valide aucune stratégie R14." in source
    assert "Stade CVM — saisie manuelle" in source
    assert "Le stade CVM n'est jamais déduit de l'âge ou du sexe" in source


def test_step4_has_no_local_normative_ranges_or_default_appliance():
    source = _read(STEP4)
    forbidden = (
        "lo: 76", "hi: 88", "flo:", "fhi:", "getAngleStatus", "norme {card.lo}",
        "preference_technique || 'DAMON'", "Damon Passive", "d-gainer", "quadhelix",
        "disjoncteur", "activateur", "perle-tuca", "Technique choisie par le praticien",
    )
    for token in forbidden:
        assert token not in source, f"unsafe Step4 semantic reintroduced: {token}"
    assert "Valeur brute · aucune norme locale" in source
    assert "Préférence technique — saisie manuelle hors R13" in source
    assert "Aucune stratégie R14 n'est générée ou validée ici." in source
    assert "Prévisualiser ou archiver un PDF ne valide jamais R14." in source


def test_cephalo_utils_must_not_reintroduce_age_cvm_or_impa_space_conversion():
    source = _read(CEPHALO_UTILS)
    assert "age < 9.5" not in source
    assert "age < 10.5" not in source
    assert "(impa - 90) / 2.5" not in source
    assert "(valeurActuelle - norme) / 2.5" not in source
    assert "TOOTH_LENGTH" not in source
    assert "export function initializeDefaultApexes" in source
    assert "return[...landmarks];" in source.replace(" ", "")


def test_missing_ddm_is_never_serialized_as_zero():
    source = _read(CEPHALO_UTILS)
    compact = source.replace(" ", "")
    assert "calcul_ddm:max??0" not in compact
    assert "calcul_ddm:mand??0" not in compact
    assert "ddm_reelle:real??0" not in compact
    assert "ddm_maxillaire:max!==null?" in compact
    assert "ddm_mandibulaire:mand!==null?" in compact
    assert "ddm_reelle:real" in compact


def test_patient_sex_remains_unknown_until_explicitly_documented():
    source = _read(ORTHO_STORE)
    assert "sexePatient: 'M' | 'F' | null;" in source
    assert "setSexePatient: (sexe: 'M' | 'F' | null) => void;" in source
    assert "sexePatient: null," in source
    assert "set({ patientId: id, patientName: name, sexePatient: null });" in source
    assert "parsed.sexePatient === 'M' || parsed.sexePatient === 'F' ? parsed.sexePatient : null" in source
    compact = source.replace(" ", "")
    assert "sexePatient:'M'," not in compact
    assert "parsed.sexePatient||'M'" not in compact
