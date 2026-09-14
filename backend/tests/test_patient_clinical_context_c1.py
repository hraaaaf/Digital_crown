from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate
from backend.security import get_password_hash


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


def _other_practitioner(db):
    user = models.User(
        email="other-context@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr. Other Context",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_schema_accepts_unknown_fail_closed_state():
    payload = PatientClinicalContextUpdate()
    assert payload.weight_kg is None
    assert payload.medication_allergy_status == "UNKNOWN"
    assert payload.medication_allergies is None
    assert payload.renal_context_status == "UNKNOWN"
    assert payload.hepatic_context_status == "UNKNOWN"
    assert "prescription_indication" not in payload.model_dump()


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
    assert "prescription_indication" not in initial_data
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
    assert "prescription_indication" not in saved_data
    assert "clinical_ready" not in saved_data


def test_context_is_tenant_isolated(client, db, dentiste, auth_headers):
    other = _other_practitioner(db)
    foreign_patient = _patient(db, other.id, suffix="OTHER")

    response = client.get(
        f"/api/patients/{foreign_patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert response.status_code in {403, 404}


def test_context_rejects_unknown_fields(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste.id, suffix="STRICT")
    for forbidden in ({"clinical_ready": True}, {"prescription_indication": "document-scoped"}):
        response = client.put(
            f"/api/patients/{patient.id}/clinical-context",
            headers=auth_headers,
            json=forbidden,
        )
        assert response.status_code == 422
