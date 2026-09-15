from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate


def _patient(db, employer_id: int):
    patient = models.Patient(
        numero_dossier="C2-IE-001",
        nom="C2",
        prenom="IE",
        date_naissance=datetime(1980, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_c2_ie_fields_default_fail_closed():
    payload = PatientClinicalContextUpdate()
    assert payload.penicillin_allergy_status == "UNKNOWN"
    assert payload.ie_cardiac_risk_category == "UNKNOWN"


def test_c2_ie_fields_reject_unrecognized_values():
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(penicillin_allergy_status="NO")
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(ie_cardiac_risk_category="MITRAL_VALVE_PROLAPSE")


def test_c2_ie_context_roundtrip(client, db, dentiste, auth_headers):
    patient = _patient(db, dentiste.id)

    initial = client.get(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert initial.status_code == 200, initial.text
    assert initial.json()["penicillin_allergy_status"] == "UNKNOWN"
    assert initial.json()["ie_cardiac_risk_category"] == "UNKNOWN"

    payload = {
        "weight_kg": None,
        "medication_allergy_status": "NONE_KNOWN",
        "medication_allergies": [],
        "penicillin_allergy_status": "NONE_KNOWN",
        "ie_cardiac_risk_category": "PREVIOUS_INFECTIVE_ENDOCARDITIS",
        "renal_context_status": "UNKNOWN",
        "renal_context_note": None,
        "hepatic_context_status": "UNKNOWN",
        "hepatic_context_note": None,
    }
    saved = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 200, saved.text
    data = saved.json()
    assert data["penicillin_allergy_status"] == "NONE_KNOWN"
    assert data["ie_cardiac_risk_category"] == "PREVIOUS_INFECTIVE_ENDOCARDITIS"
    assert "clinical_ready" not in data
    assert "dose" not in data
