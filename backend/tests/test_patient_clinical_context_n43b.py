from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient_clinical_context import PatientProcedureSafetyContextUpdate


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
        "mronj_medication_status": "PRESENT",
        "mronj_agents": ["Denosumab"],
        "mronj_agent_class": "DENOSUMAB",
        "mronj_indication": "OSTEOPOROSIS_NONMALIGNANT",
        "mronj_route": "PARENTERAL",
        "mronj_duration_months": 24,
        "mronj_concurrent_risk_therapy": [],
        "active_oral_infection_or_inflammation": "NO",
        "suspected_or_known_mronj": "NO",
        "procedure_date": "2026-10-01",
        "procedure_bleeding_risk": "HIGHER_POSTOP_BLEEDING_RISK",
        "procedure_osseous_risk": "DENTOALVEOLAR_OSSEOUS_INJURY",
        "procedure_is_implant": True,
        "ie_procedure_qualifies": True,
        "oral_route_possible": True,
        "currently_taking_penicillin_or_amoxicillin": False,
    }


def test_n43b_antithrombotic_context_defaults_fail_closed():
    payload = PatientProcedureSafetyContextUpdate()
    assert payload.anticoagulant_status == "UNKNOWN"
    assert payload.antiplatelet_status == "UNKNOWN"
    assert payload.antithrombotic_classes is None
    assert payload.antithrombotic_combination_status == "UNKNOWN"
    assert payload.warfarin_inr is None
    assert payload.warfarin_inr_current is None
    assert payload.lmwh_dose_class == "UNKNOWN"
    assert payload.mronj_medication_status == "UNKNOWN"
    assert payload.mronj_agent_class == "UNKNOWN"
    assert payload.mronj_indication == "UNKNOWN"
    assert payload.suspected_or_known_mronj == "UNKNOWN"
    assert payload.procedure_date is None
    assert payload.procedure_bleeding_risk == "UNKNOWN"
    assert payload.procedure_osseous_risk == "UNKNOWN"
    assert payload.procedure_is_implant is None


def test_practitioner_context_api_rejects_hidden_n43b_fields(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id)
    response = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json={"anticoagulant_status": "PRESENT", "anticoagulants": ["Rivaroxaban"]},
    )
    assert response.status_code == 422


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
    assert "mronj_medication_status" not in visible_before.json()
    assert "mronj_indication" not in visible_before.json()
    assert "procedure_date" not in visible_before.json()
    assert "procedure_bleeding_risk" not in visible_before.json()
    assert "procedure_osseous_risk" not in visible_before.json()

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
    assert data["mronj_medication_status"] == "PRESENT"
    assert data["mronj_agents"] == ["Denosumab"]
    assert data["mronj_indication"] == "OSTEOPOROSIS_NONMALIGNANT"
    assert data["procedure_date"] == "2026-10-01"
    assert data["procedure_bleeding_risk"] == "HIGHER_POSTOP_BLEEDING_RISK"
    assert data["procedure_osseous_risk"] == "DENTOALVEOLAR_OSSEOUS_INJURY"
    assert data["procedure_is_implant"] is True

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
    assert hidden["mronj_medication_status"] == "PRESENT"
    assert hidden["mronj_agents"] == ["Denosumab"]
    assert hidden["procedure_date"] == "2026-10-01"
    assert hidden["procedure_is_implant"] is True


def test_n43b_context_rejects_implicit_or_inconsistent_antithrombotic_facts():
    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            anticoagulant_status="NONE_REPORTED",
            anticoagulants=["Rivaroxaban"],
        )

    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            anticoagulant_status="PRESENT",
            anticoagulants=["Warfarine"],
            antithrombotic_classes=["VKA"],
            warfarin_inr=float("nan"),
        )

    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            anticoagulant_status="PRESENT",
            anticoagulants=["Enoxaparine"],
            antithrombotic_classes=["LMWH"],
            lmwh_dose_class="TREATMENT",
            antithrombotic_combination_status="YES",
        )



def test_practitioner_context_api_rejects_hidden_mronj_fields(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id)
    response = client.put(
        f"/api/patients/{patient.id}/clinical-context",
        headers=auth_headers,
        json={
            "mronj_medication_status": "PRESENT",
            "mronj_agents": ["Denosumab"],
            "mronj_indication": "OSTEOPOROSIS_NONMALIGNANT",
        },
    )
    assert response.status_code == 422


def test_n43b_context_rejects_inconsistent_mronj_facts():
    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            mronj_medication_status="NONE_REPORTED",
            mronj_agents=["Denosumab"],
        )

    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            mronj_medication_status="PRESENT",
            mronj_agents=["Denosumab"],
            mronj_agent_class="DENOSUMAB",
            mronj_indication="OSTEOPOROSIS_NONMALIGNANT",
            mronj_duration_months=-1,
        )

    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            mronj_medication_status="NONE_REPORTED",
            mronj_agent_class="DENOSUMAB",
        )



def test_n43b_context_rejects_inconsistent_hidden_procedure_facts():
    with pytest.raises(ValidationError):
        PatientProcedureSafetyContextUpdate(
            procedure_date="2026-10-01",
            procedure_bleeding_risk="HIGHER_POSTOP_BLEEDING_RISK",
            procedure_osseous_risk="NO_OSSEOUS_INJURY",
            procedure_is_implant=True,
        )
