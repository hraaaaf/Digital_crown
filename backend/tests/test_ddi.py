import pytest
from backend.services.prescription_service import prescription_service


def test_normalize_to_molecule():
    assert prescription_service._normalize_to_molecule("Clamexyl") == "AMOXICILLINE"
    assert prescription_service._normalize_to_molecule("Augmentin") == "AMOXICILLINE/ACIDE_CLAVULANIQUE"
    assert prescription_service._normalize_to_molecule("Advil") == "IBUPROFENE"
    assert prescription_service._normalize_to_molecule("Profenid") == "KETOPROFENE"
    assert prescription_service._normalize_to_molecule("Tahor") == "SIMVASTATINE"


def test_ddi_macrolides_statines():
    warnings = prescription_service.check_drug_interactions(["Zeclar", "Tahor"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "high"
    assert "Simvastatine" in warnings[0]["message"]


def test_ddi_macrolides_amiodarone():
    warnings = prescription_service.check_drug_interactions(["Zeclar", "Cordarone"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "high"
    assert "Amiodarone" in warnings[0]["message"]


def test_ddi_metronidazole_alcool():
    warnings = prescription_service.check_drug_interactions(["Flagyl", "Alcool"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "high"
    assert "Alcool" in warnings[0]["message"]


def test_ddi_ains_ains():
    warnings = prescription_service.check_drug_interactions(["Advil", "Profenid"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "medium"
    assert "plusieurs AINS" in warnings[0]["message"]


def test_ddi_ains_aspirine():
    warnings = prescription_service.check_drug_interactions(["Advil", "Aspirine"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "medium"
    assert "Aspirine" in warnings[0]["message"]


def test_ddi_ains_anticoagulants():
    warnings = prescription_service.check_drug_interactions(["Voltarene", "Previscan"])
    assert len(warnings) == 1
    assert warnings[0]["severity"] == "medium"
    assert "Anticoagulant" in warnings[0]["message"]


def test_no_ddi_for_safe_drugs():
    warnings = prescription_service.check_drug_interactions(["Clamexyl", "Doliprane"])
    assert len(warnings) == 0
