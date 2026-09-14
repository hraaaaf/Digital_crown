from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate
from backend.tests.conftest import make_user


def _patient(db, employer_id: int, suffix: str = "C1"):
    patient = models.Patient(
        numero_dossier=f"{suffix}-001",
        nom="CONTEXT",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _headers(client, user, password="TestPass123!"):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_schema_accepts_unknown_fail_closed_state():
    payload = PatientClinicalContextUpdate()
    assert payload.weight_kg is None
    assert payload.medication_allergy_status == "UNKNOWN"
    assert payload.medication_allergies is None
    assert payload.renal_context_status == "UNKNOWN"
    assert payload.hepatic_context_status == "UNKNOWN"
    assert payload.prescription_indication is None


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("-inf"), float("nan")])
def test_schema_rejects_non_positive_or_non_finite_weight(value):
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(weight_kg=value)


def test_schema_requires_explicit_allergy_status_consistency():
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(
            medication_allergy_status="PRESENT",
            medication_allergies=[],
        )

    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(
            medication_allergy_status="UNKNOWN",
            medication_allergies=["Pénicilline"],
        )

    payload = PatientClinicalContextUpdate(
        medication_allergy_status="PRESENT",
        medication_allergies=[" Pénicilline ", "pénicilline", "Ibuprofène"],
    )
    assert payload.medication_allergies == ["Pénicilline", "Ibuprofène"]


def test_schema_rejects_organ_note_without_reported_impairment():
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(renal_context_note="Insuffisance rapportée")
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(hepatic_context_note="Atteinte rapportée")


def test_context_get_defaults_and_put_roundtrip(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste.id)

    initial = client.get(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert initial.status_code == 200, initial.text
    initial_data = initial.json()
    assert initial_data["weight_kg"] is None
    assert initial_data["medication_allergy_status"] == "UNKNOWN"
    assert initial_data["renal_context_status"] == "UNKNOWN"
    assert initial_data["hepatic_context_status"] == "UNKNOWN"
    assert "clinical_ready" not in initial_data
    assert "dose" not in initial_data

    payload = {
        "weight_kg": 72.5,
        "medication_allergy_status": "PRESENT",
        "medication_allergies": ["Pénicilline"],
        "renal_context_status": "IMPAIRMENT_REPORTED",
        "renal_context_note": "Atteinte rénale rapportée par le praticien",
        "hepatic_context_status": "NO_KNOWN_IMPAIRMENT",
        "hepatic_context_note": None,
        "prescription_indication": "Indication saisie explicitement",
    }
    saved = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 200, saved.text
    saved_data = saved.json()
    assert saved_data["weight_kg"] == 72.5
    assert saved_data["medication_allergies"] == ["Pénicilline"]
    assert saved_data["updated_by_user_id"] == dentiste.id
    assert "clinical_ready" not in saved_data

    read_back = client.get(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert read_back.status_code == 200, read_back.text
    assert read_back.json()["prescription_indication"] == "Indication saisie explicitement"


def test_context_is_tenant_isolated(client, db, dentiste, auth_headers):
    other = make_user(db, email="other-context@cabinet.ma")
    foreign_patient = _patient(db, other.id, suffix="OTHER")

    response = client.get(
        f"/api/patients/{foreign_patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert response.status_code in {403, 404}


def test_context_rejects_unknown_fields(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste.id, suffix="STRICT")
    response = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json={"clinical_ready": True},
    )
    assert response.status_code == 422
