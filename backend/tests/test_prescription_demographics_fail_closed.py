from pathlib import Path

from backend.services.clinical_rules_engine import ClinicalRulesEngine


ROOT = Path(__file__).resolve().parents[2]


def _by_molecule(result):
    return {
        item["molecule"]: item
        for item in result["recommandations_moleculaires"]
    }


def test_missing_age_never_falls_back_to_synthetic_adult_demographics():
    result = ClinicalRulesEngine().analyze_case({"antecedents": ""}, ["PULPITE"])

    assert result["is_child"] is None
    assert "Âge patient requis" in result["dosage_note"]
    assert result["recommandations_moleculaires"]
    assert all(
        item["dosage_defaut"] == "Dosage non calculé (âge requis)"
        for item in result["recommandations_moleculaires"]
    )


def test_child_without_weight_does_not_receive_a_calculated_dose():
    result = ClinicalRulesEngine().analyze_case(
        {"age": 10, "poids": None, "antecedents": ""},
        ["PULPITE"],
    )

    assert result["is_child"] is True
    assert "Poids patient requis" in result["dosage_note"]
    assert result["recommandations_moleculaires"]
    assert all(
        item["dosage_defaut"] == "Dosage pédiatrique non calculé (poids requis)"
        for item in result["recommandations_moleculaires"]
    )


def test_child_with_explicit_weight_uses_that_weight_for_calculation():
    result = ClinicalRulesEngine().analyze_case(
        {"age": 10, "poids": 30, "antecedents": ""},
        ["PULPITE"],
    )
    by_molecule = _by_molecule(result)

    assert result["is_child"] is True
    assert by_molecule["PARACETAMOL"]["dosage_defaut"] == "450mg x 4/jour (60mg/kg/j)"
    assert by_molecule["IBUPROFENE"]["dosage_defaut"] == "300mg x 3/jour (30mg/kg/j)"


def test_adult_without_weight_keeps_adult_standard_dosing_path():
    result = ClinicalRulesEngine().analyze_case(
        {"age": 30, "poids": None, "antecedents": ""},
        ["PULPITE"],
    )

    assert result["is_child"] is False
    assert result["dosage_note"] == "Posologie adulte standard."
    assert all(
        "non calculé" not in item["dosage_defaut"]
        for item in result["recommandations_moleculaires"]
    )


def test_no_synthetic_age_or_weight_defaults_remain_in_prescription_sources():
    rules = (ROOT / "backend/services/clinical_rules_engine.py").read_text(encoding="utf-8")
    legacy = (ROOT / "backend/services/prescription_service_legacy.py").read_text(encoding="utf-8")

    assert 'get("age", 30)' not in rules
    assert 'get("poids", 70)' not in rules
    assert '"poids": 70' not in legacy


def test_legacy_prescription_service_has_no_unguarded_runtime_consumer():
    allowed = {"backend/services/prescription_service.py"}
    consumers = []

    for path in (ROOT / "backend").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if relative == "backend/services/prescription_service_legacy.py" or relative.startswith("backend/tests/"):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if "prescription_service_legacy" in source or "LegacyPrescriptionService" in source:
            consumers.append(relative)

    assert consumers == sorted(allowed), consumers
