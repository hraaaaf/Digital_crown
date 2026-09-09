"""Static safety contract for the orthodontic frontend scientific boundary.

The frontend may display measurements and practitioner-authored clinical text,
but it must not turn measurements into an autonomous therapeutic decision.
"""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERT_SYSTEM = REPO_ROOT / "frontend/src/features/ortho/orthoExpertSystem.ts"
STEP3 = REPO_ROOT / "frontend/src/features/ortho/components/Step3Clinical.tsx"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_expert_system_contains_no_autonomous_treatment_rules():
    source = _read(EXPERT_SYSTEM)

    # The compatibility adapter must remain descriptive only.
    forbidden = (
        "extrRecommandee",
        "High Torque",
        "Low Torque",
        "bite blocks",
        "Bite-Block",
        "élastiques de Classe II",
        "Distalisation",
        "CBCT/IRM",
        "Dents concernées",
        "EXTRACTIONNEL",
        "SANS EXTRACTION",
        "Prescription Autoligaturante",
    )
    for token in forbidden:
        assert token not in source, f"autonomous orthodontic treatment token reintroduced: {token}"

    assert "Décision thérapeutique : à documenter et valider par le praticien." in source
    assert "return { rapportMarkdown }" in source


def test_growth_and_class_ii_helpers_fail_closed():
    source = _read(EXPERT_SYSTEM)

    # Age alone must not be converted into dentition stage, and overjet alone
    # must not be converted into a Class II division.
    assert "export function deriveDentureFromAge" in source
    assert "export function deriveDivision" in source
    assert "return '';" in source
    assert "return null;" in source
    assert "surplomb >" not in source


def test_step3_does_not_directly_encode_named_appliance_or_extraction_rules():
    source = _read(STEP3)

    # Step 3 still has legacy UI semantics to migrate, but direct therapeutic
    # decision code must not be reintroduced here.
    forbidden = (
        "14, 24, 34, 44",
        "extrRecommandee",
        "High Torque",
        "Low Torque",
        "CBCT/IRM",
        "élastiques de Classe II",
    )
    for token in forbidden:
        assert token not in source, f"direct treatment rule found in Step3Clinical: {token}"
