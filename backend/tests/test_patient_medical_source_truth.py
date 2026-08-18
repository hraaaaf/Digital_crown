"""P0-G — medical history has one authoritative persistence source.

The canonical raw medical-history field is Patient.antecedents_medicaux.
DossierClinique must not reintroduce a competing copy.
"""

from backend import models, schemas


def test_patient_is_only_persistent_medical_history_source():
    assert "antecedents_medicaux" in models.Patient.__table__.columns
    assert "antecedents_medicaux" not in models.DossierClinique.__table__.columns


def test_patient_api_contract_exposes_single_medical_history_source():
    assert "antecedents_medicaux" in schemas.PatientBase.model_fields
    assert "antecedents_medicaux" in schemas.PatientUpdate.model_fields
    assert "antecedents_medicaux" not in schemas.DossierOut.model_fields
