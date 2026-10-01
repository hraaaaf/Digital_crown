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


def _context(db, patient_id: int, employer_id: int, user_id: int, **overrides):
    values = dict(
        anticoagulant_status="NONE_REPORTED",
        anticoagulants=None,
        antiplatelet_status="NONE_REPORTED",
        antiplatelets=None,
        antithrombotic_classes=None,
        antithrombotic_combination_status="NO",
        warfarin_inr=None,
        warfarin_inr_current=None,
        lmwh_dose_class="UNKNOWN",
        mronj_medication_status="NONE_REPORTED",
        mronj_agents=None,
        mronj_agent_class="UNKNOWN",
        mronj_indication="UNKNOWN",
        mronj_route="UNKNOWN",
        mronj_duration_months=None,
        mronj_concurrent_risk_therapy=None,
        active_oral_infection_or_inflammation="NO",
        suspected_or_known_mronj="NO",
    )
    values.update(overrides)
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
        **values,
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
        "procedure_osseous_risk": "NO_OSSEOUS_INJURY",
        "procedure_is_implant": False,
        "ie_procedure_qualifies": False,
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
    _context(
        db,
        patient.id,
        dentiste.id,
        dentiste.id,
        anticoagulant_status="PRESENT",
        anticoagulants=["Rivaroxaban"],
        antithrombotic_classes=["DOAC"],
        antithrombotic_combination_status="NO",
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            procedure_bleeding_risk="HIGHER_POSTOP_BLEEDING_RISK",
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
    _context(
        db,
        patient.id,
        dentiste.id,
        dentiste.id,
        anticoagulant_status="PRESENT",
        anticoagulants=["Rivaroxaban"],
        antiplatelet_status="PRESENT",
        antiplatelets=["Aspirine"],
        antithrombotic_classes=["DOAC", "ANTIPLATELET"],
        antithrombotic_combination_status="YES",
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(patient.id),
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



def test_background_endpoint_surfaces_only_generic_nonmalignant_mronj_review(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "MRONJ-OSTEO")
    _context(
        db,
        patient.id,
        dentiste.id,
        dentiste.id,
        mronj_medication_status="PRESENT",
        mronj_agents=["Denosumab"],
        mronj_agent_class="DENOSUMAB",
        mronj_indication="OSTEOPOROSIS_NONMALIGNANT",
        mronj_route="PARENTERAL",
        mronj_duration_months=24,
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            procedure_osseous_risk="DENTOALVEOLAR_OSSEOUS_INJURY",
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "CLINICAL_REVIEW_REQUIRED",
        "alert_key": "CLINICAL_REVIEW_RECOMMENDED",
        "read_only": True,
    }


def test_background_endpoint_surfaces_only_generic_malignancy_implant_specialist_review(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "MRONJ-CANCER")
    _context(
        db,
        patient.id,
        dentiste.id,
        dentiste.id,
        mronj_medication_status="PRESENT",
        mronj_agents=["Zoledronate"],
        mronj_agent_class="BISPHOSPHONATE",
        mronj_indication="MALIGNANCY",
        mronj_route="PARENTERAL",
        mronj_concurrent_risk_therapy=["CHEMOTHERAPY"],
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(
            patient.id,
            procedure_osseous_risk="DENTOALVEOLAR_OSSEOUS_INJURY",
            procedure_is_implant=True,
        ),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == {
        "status": "SPECIALIST_REVIEW_REQUIRED",
        "alert_key": "SPECIALIST_REVIEW_RECOMMENDED",
        "read_only": True,
    }
    rendered = str(data).lower()
    for prohibited in ("mronj", "ctx", "drug holiday", "bisphosphonate", "denosumab"):
        assert prohibited not in rendered


def test_background_endpoint_does_not_diagnose_known_or_suspected_mronj(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "MRONJ-SUSPECT")
    _context(
        db,
        patient.id,
        dentiste.id,
        dentiste.id,
        suspected_or_known_mronj="YES",
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/procedure-safety/evaluate",
        headers=auth_headers,
        json=_payload(patient.id),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "SPECIALIST_REVIEW_REQUIRED",
        "alert_key": "SPECIALIST_REVIEW_RECOMMENDED",
        "read_only": True,
    }
