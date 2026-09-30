from datetime import date, datetime

from backend import models
from backend.models_patient_clinical_context import PatientClinicalContext
from backend.routers.patient_clinical_context import _age_years
from backend.services import medication_dict


def _current_amoxicillin_id():
    rows = medication_dict.search_unified("AMOXICILLINE", limit=100)
    return next(r["presentation_id"] for r in rows if r.get("may_claim_current_marketing_status"))


def _patient(db, dentiste, born=datetime(1990, 10, 1)):
    p = models.Patient(
        nom="Neo", prenom="Patient", date_naissance=born, sexe="M",
        employer_id=dentiste.get_employer_id(),
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def test_age_years_is_calendar_correct():
    assert _age_years(datetime(2000, 10, 1), today=date(2026, 9, 30)) == 25
    assert _age_years(datetime(2000, 9, 30), today=date(2026, 9, 30)) == 26
    assert _age_years(datetime(2030, 1, 1), today=date(2026, 9, 30)) is None


def test_n5_api_requires_auth(client, db, dentiste):
    p = _patient(db, dentiste)
    r = client.get(f"/api/patients/{p.id}/neo-prescription-safety", params={"presentation_id": _current_amoxicillin_id()})
    assert r.status_code == 401


def test_n5_api_is_read_only_and_fail_closed(client, db, dentiste, auth_headers):
    p = _patient(db, dentiste)
    before = db.query(PatientClinicalContext).filter(PatientClinicalContext.patient_id == p.id).count()
    r = client.get(
        f"/api/patients/{p.id}/neo-prescription-safety",
        params={"presentation_id": _current_amoxicillin_id()}, headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["patient_id"] == p.id and body["read_only"] is True
    assert body["status"] == "BLOCKED"
    assert "INTERACTION_KNOWLEDGE_NOT_COMPLETE" in body["blockers"]
    assert "CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE" in body["blockers"]
    assert db.query(PatientClinicalContext).filter(PatientClinicalContext.patient_id == p.id).count() == before == 0


def test_n5_api_unresolved_presentation_fails_closed(client, db, dentiste, auth_headers):
    p = _patient(db, dentiste)
    r = client.get(
        f"/api/patients/{p.id}/neo-prescription-safety",
        params={"presentation_id": "not-a-real-presentation"}, headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "BLOCKED"
    assert body["blockers"] == ["MEDICATION_IDENTITY_UNRESOLVED"]
    assert body["medication_identity_verified"] is False


def test_n5_api_denies_cross_tenant_patient(client, db, dentiste, auth_headers):
    from backend.security import get_password_hash
    other = models.User(
        email="neo-other-cabinet@example.test", hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE", nom_complet="Dr Other", is_active=True, is_licensed=True,
    )
    db.add(other); db.commit(); db.refresh(other)
    p = models.Patient(
        nom="Other", prenom="Tenant", date_naissance=datetime(1990, 1, 1),
        sexe="F", employer_id=other.get_employer_id(),
    )
    db.add(p); db.commit(); db.refresh(p)
    r = client.get(
        f"/api/patients/{p.id}/neo-prescription-safety",
        params={"presentation_id": _current_amoxicillin_id()}, headers=auth_headers,
    )
    assert r.status_code == 403


def test_n5_api_exposes_structured_current_medication_resolution(client, db, dentiste, auth_headers):
    p = _patient(db, dentiste)
    ctx = PatientClinicalContext(
        patient_id=p.id, employer_id=dentiste.get_employer_id(),
        current_medications_status="PRESENT", current_medications=["Xarelto 20 mg"],
    )
    db.add(ctx); db.commit()
    r = client.get(
        f"/api/patients/{p.id}/neo-prescription-safety",
        params={"presentation_id": _current_amoxicillin_id()}, headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["current_medication_resolution"] == [
        {"input": "Xarelto 20 mg", "identity": "RIVAROXABAN", "resolved": True}
    ]
    assert r.json()["status"] == "BLOCKED"
