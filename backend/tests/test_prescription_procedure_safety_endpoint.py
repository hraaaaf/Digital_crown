from datetime import datetime

from backend import models
from backend.models_patient_clinical_context import PatientClinicalContext


def _patient(db, employer_id: int, suffix: str):
    patient = models.Patient(
        numero_dossier=f"N43B-{suffix}",
        nom="N43B",
        prenom="Patient",
        date_naissance=datetime(1980, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _context(db, patient_id: int, employer_id: int, user_id: int):
    context = PatientClinicalContext(
        patient_id=patient_id,
        employer_id=employer_id,
        medication_allergy_status="NONE_KNOWN",
        medication_allergies=[],
        penicillin_allergy_status="NONE_KNOWN",
        ie_cardiac_risk_category="PREVIOUS_INFECTIVE_ENDOCARDITIS",
        renal_context_status="UNKNOWN",
        hepatic_context_status="UNKNOWN",
        updated_by_user_id=user_id,
    )
    db.add(context)
    db.commit()
    db.refresh(context)
    return context


def _payload(patient_id: int, **overrides):
    payload = {
        "patient_id": patient_id,
        "procedure_date": "2026-10-01",
        "procedure_bleeding_risk": "LOW_POSTOP_BLEEDING_RISK",
        "ie_procedure_qualifies": False,
        "antithrombotic_status": "NONE_REPORTED",
        "antithrombotic_classes": [],
        "combination_therapy": "NO",
        "warfarin_inr": None,
        "warfarin_inr_current": None,
        "lmwh_dose_class": "UNKNOWN",
        "oral_route_possible": None,
        "currently_taking_penicillin_or_amoxicillin": None,
        "presentation_id": None,
    }
    payload.update(overrides)
    return payload


def test_background_endpoint_returns_minimal_silent_ready_surface(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "READY")
    context = _context(db, patient.id, dentiste.id, dentiste.id)
    before_updated_by = context.updated_by_user_id

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(patient.id),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == {"status": "READY", "alert_key": None, "read_only": True}
    assert "blockers" not in data
    assert "internal_codes" not in data
    assert "source_ids" not in data
    assert "total_dose_mg" not in data

    db.refresh(context)
    assert context.updated_by_user_id == before_updated_by


def test_background_endpoint_surfaces_only_generic_doac_review_alert(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "DOAC")
    _context(db, patient.id, dentiste.id, dentiste.id)

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            procedure_bleeding_risk="HIGHER_POSTOP_BLEEDING_RISK",
            antithrombotic_status="PRESENT",
            antithrombotic_classes=["DOAC"],
            combination_therapy="NO",
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "CLINICAL_REVIEW_REQUIRED",
        "alert_key": "CLINICAL_REVIEW_RECOMMENDED",
        "read_only": True,
    }


def test_background_endpoint_escalates_combination_without_stop_instruction(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "COMBO")
    _context(db, patient.id, dentiste.id, dentiste.id)

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            antithrombotic_status="PRESENT",
            antithrombotic_classes=["DOAC", "ANTIPLATELET"],
            combination_therapy="YES",
        ),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "PRESCRIBER_REVIEW_REQUIRED"
    assert data["alert_key"] == "PRESCRIBER_REVIEW_RECOMMENDED"
    rendered = str(data).lower()
    for prohibited in ("stop ", "skip ", "hold ", "arrêt", "suspend"):
        assert prohibited not in rendered


def test_background_endpoint_reuses_ie_rule_and_fails_closed_when_prophylaxis_context_incomplete(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "IE")
    _context(db, patient.id, dentiste.id, dentiste.id)

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            ie_procedure_qualifies=True,
            oral_route_possible=True,
            currently_taking_penicillin_or_amoxicillin=False,
            presentation_id=None,
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "CONTEXT_REQUIRED",
        "alert_key": "CONTEXT_REQUIRED",
        "read_only": True,
    }


def test_background_endpoint_enforces_patient_tenant_isolation(
    client, db, dentiste, auth_headers
):
    other = models.User(
        email="n43b-other@cabinet.ma",
        hashed_password="not-used",
        role="DENTISTE",
        nom_complet="Dr Other",
        is_active=True,
        is_licensed=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    foreign_patient = _patient(db, other.id, "FOREIGN")

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(foreign_patient.id),
    )
    assert response.status_code in {403, 404}
