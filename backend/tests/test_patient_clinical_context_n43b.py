from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate


def _patient(db, employer_id: int):
    patient = models.Patient(
        numero_dossier="N43B-CTX-001",
        nom="N43B",
        prenom="Context",
        date_naissance=datetime(1980, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _hidden_context_payload():
    return {
        "anticoagulant_status": "PRESENT",
        "anticoagulants": ["Rivaroxaban"],
        "antiplatelet_status": "NONE_REPORTED",
        "antiplatelets": None,
        "antithrombotic_classes": ["DOAC"],
        "antithrombotic_combination_status": "NO",
        "warfarin_inr": None,
        "warfarin_inr_checked_at": None,
        "warfarin_inr_current": None,
        "lmwh_dose_class": "UNKNOWN",
    }


def test_n43b_antithrombotic_context_defaults_fail_closed():
    payload = PatientClinicalContextUpdate()
    assert payload.anticoagulant_status == "UNKNOWN"
    assert payload.antiplatelet_status == "UNKNOWN"
    assert payload.antithrombotic_classes is None
    assert payload.antithrombotic_combination_status == "UNKNOWN"
    assert payload.warfarin_inr is None
    assert payload.warfarin_inr_current is None
    assert payload.lmwh_dose_class == "UNKNOWN"


def test_n43b_hidden_context_roundtrip_and_partial_update_preserves_it(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id)

    visible_before = client.get(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
    )
    assert visible_before.status_code == 200, visible_before.text
    assert "anticoagulant_status" not in visible_before.json()
    assert "antithrombotic_classes" not in visible_before.json()

    saved = client.put(
        f"/api/patients/{patient.id}/procedure-safety-context",
        headers=auth_headers,
        json=_hidden_context_payload(),
    )
    assert saved.status_code == 200, saved.text
    data = saved.json()
    assert data["anticoagulant_status"] == "PRESENT"
    assert data["anticoagulants"] == ["Rivaroxaban"]
    assert data["antithrombotic_classes"] == ["DOAC"]
    assert data["antithrombotic_combination_status"] == "NO"

    partial = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json={"weight_kg": 72.0},
    )
    assert partial.status_code == 200, partial.text
    assert "anticoagulant_status" not in partial.json()
    assert "antithrombotic_classes" not in partial.json()

    persisted = client.get(
        f"/api/patients/{patient.id}/procedure-safety-context",
        headers=auth_headers,
    )
    assert persisted.status_code == 200, persisted.text
    hidden = persisted.json()
    assert hidden["anticoagulant_status"] == "PRESENT"
    assert hidden["anticoagulants"] == ["Rivaroxaban"]
    assert hidden["antithrombotic_classes"] == ["DOAC"]


def test_n43b_context_rejects_implicit_or_inconsistent_antithrombotic_facts():
    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(
            anticoagulant_status="NONE_REPORTED",
            anticoagulants=["Rivaroxaban"],
        )

    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(
            anticoagulant_status="PRESENT",
            anticoagulants=["Warfarine"],
            antithrombotic_classes=["VKA"],
            warfarin_inr=float("nan"),
        )

    with pytest.raises(ValidationError):
        PatientClinicalContextUpdate(
            anticoagulant_status="PRESENT",
            anticoagulants=["Enoxaparine"],
            antithrombotic_classes=["LMWH"],
            lmwh_dose_class="TREATMENT",
            antithrombotic_combination_status="YES",
        )
