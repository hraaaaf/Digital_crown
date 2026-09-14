from datetime import datetime

from backend import models
from backend.models_patient_clinical_context import PatientClinicalContext


def _patient(db, employer_id: int, birth_year: int = 1980, suffix: str = "C2EVAL"):
    patient = models.Patient(
        numero_dossier=f"{suffix}-001",
        nom="RULE",
        prenom="Patient",
        date_naissance=datetime(birth_year, 1, 1),
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


def _request(patient_id: int, presentation_id: str = "cnops:test-amoxicillin"):
    return {
        "patient_id": patient_id,
        "procedure_date": "2026-09-15",
        "dental_procedure_qualifies": True,
        "oral_route_possible": True,
        "currently_taking_penicillin_or_amoxicillin": False,
        "presentation_id": presentation_id,
    }


def test_read_only_endpoint_returns_ready_only_for_exact_eligible_context(
    client, db, dentiste, auth_headers, monkeypatch
):
    patient = _patient(db, dentiste.id)
    context = _context(db, patient.id, dentiste.id, dentiste.id)
    before_updated_by = context.updated_by_user_id

    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {
            "presentation_id": presentation_id,
            "nom": "AMOXICILLINE TEST",
            "dci": "AMOXICILLINE",
            "dosage": "500",
            "unite": "MG",
            "forme": "GELULE",
        },
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=_request(patient.id),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "READY"
    assert data["active_ingredient_code"] == "AMOXICILLIN"
    assert data["total_dose_mg"] == 2000
    assert data["timing_min_minutes_before"] == 30
    assert data["timing_max_minutes_before"] == 60
    assert data["single_dose"] is True

    db.refresh(patient)
    db.refresh(context)
    assert patient.nom == "RULE"
    assert context.updated_by_user_id == before_updated_by
    assert context.ie_cardiac_risk_category == "PREVIOUS_INFECTIVE_ENDOCARDITIS"


def test_endpoint_fails_closed_when_structured_context_is_absent(
    client, db, dentiste, auth_headers, monkeypatch
):
    patient = _patient(db, dentiste.id, suffix="C2EMPTY")
    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {"presentation_id": presentation_id, "dci": "AMOXICILLINE"},
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=_request(patient.id),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["total_dose_mg"] is None
    assert "CARDIAC_RISK_UNKNOWN" in data["blockers"]
    assert "PENICILLIN_ALLERGY_UNKNOWN" in data["blockers"]


def test_endpoint_blocks_pediatric_patient_without_reusing_adult_dose(
    client, db, dentiste, auth_headers, monkeypatch
):
    patient = _patient(db, dentiste.id, birth_year=2012, suffix="C2CHILD")
    _context(db, patient.id, dentiste.id, dentiste.id)
    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {"presentation_id": presentation_id, "dci": "AMOXICILLINE"},
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=_request(patient.id),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["total_dose_mg"] is None
    assert "ADULT_RULE_ONLY" in data["blockers"]


def test_endpoint_resolves_presentation_server_side_and_blocks_association(
    client, db, dentiste, auth_headers, monkeypatch
):
    patient = _patient(db, dentiste.id, suffix="C2ASSOC")
    _context(db, patient.id, dentiste.id, dentiste.id)
    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {
            "presentation_id": presentation_id,
            "dci": "AMOXICILLINE / ACIDE CLAVULANIQUE",
        },
    )

    response = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=_request(patient.id, presentation_id="cnops:association"),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["total_dose_mg"] is None
    assert "ACTIVE_INGREDIENT_NOT_AMOXICILLIN" in data["blockers"]


def test_endpoint_rejects_unknown_request_fields_and_missing_session_facts(
    client, db, dentiste, auth_headers, monkeypatch
):
    patient = _patient(db, dentiste.id, suffix="C2STRICT")
    _context(db, patient.id, dentiste.id, dentiste.id)
    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {"presentation_id": presentation_id, "dci": "AMOXICILLINE"},
    )

    invalid = _request(patient.id)
    invalid["cardiac_risk_category"] = "PREVIOUS_INFECTIVE_ENDOCARDITIS"
    rejected = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=invalid,
    )
    assert rejected.status_code == 422

    incomplete = _request(patient.id)
    incomplete["dental_procedure_qualifies"] = None
    incomplete["oral_route_possible"] = None
    incomplete["currently_taking_penicillin_or_amoxicillin"] = None
    blocked = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=incomplete,
    )
    assert blocked.status_code == 200, blocked.text
    blockers = blocked.json()["blockers"]
    assert "DENTAL_PROCEDURE_ELIGIBILITY_UNKNOWN" in blockers
    assert "ORAL_ROUTE_UNKNOWN" in blockers
    assert "CURRENT_ANTIBIOTIC_EXPOSURE_UNKNOWN" in blockers


def test_endpoint_enforces_patient_tenant_isolation(
    client, db, dentiste, auth_headers, monkeypatch
):
    other = models.User(
        email="c2-other@cabinet.ma",
        hashed_password="not-used",
        role="DENTISTE",
        nom_complet="Dr Other",
        is_active=True,
        is_licensed=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    foreign_patient = _patient(db, other.id, suffix="C2FOREIGN")

    monkeypatch.setattr(
        "backend.routers.prescriptions.medication_dict.get_presentation",
        lambda presentation_id: {"presentation_id": presentation_id, "dci": "AMOXICILLINE"},
    )
    response = client.post(
        "/api/prescriptions/clinical-rules/ie-prophylaxis/evaluate",
        headers=auth_headers,
        json=_request(foreign_patient.id),
    )
    assert response.status_code in {403, 404}
