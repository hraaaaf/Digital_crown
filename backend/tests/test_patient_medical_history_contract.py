"""P0-G — canonical medical-history contract for the Patient workspace.

The Patient API is the authoritative public contract for antecedents_medicaux.
DossierClinique currently retains a legacy database column, but that duplicate
must never be reintroduced into the public DossierOut contract while migration
is pending.
"""

from backend.schemas.patient import DossierOut, PatientCreate, PatientOut


def test_patient_contract_owns_medical_history():
    assert "antecedents_medicaux" in PatientCreate.model_fields
    assert "antecedents_medicaux" in PatientOut.model_fields


def test_dossier_contract_does_not_expose_duplicate_medical_history():
    assert "antecedents_medicaux" not in DossierOut.model_fields
