from datetime import datetime

from backend import models
from backend.models_clinical_p3 import ClinicalConclusion  # noqa: F401 — registers metadata
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _make_user(db, email, *, role="DENTISTE", employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role=role,
        nom_complet="P3 Clinical Test",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, owner, dossier):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="CONCLUSION",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_practitioner_can_append_and_read_clinical_conclusions(client, db):
    owner = _make_user(db, "p3-conclusion-owner@test.ma")
    patient = _make_patient(db, owner, "P3-CONCLUSION-1")
    headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/clinical-conclusions"

    first = client.post(
        url,
        headers=headers,
        json={"conclusion_text": "Conclusion retenue par le praticien."},
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["patient_id"] == patient.id
    assert body["validated_by"] == owner.id
    assert body["proposal_text"] is None

    second = client.post(
        url,
        headers=headers,
        json={
            "conclusion_text": "Conclusion corrigée et retenue après examen.",
            "proposal_text": "Proposition structurée issue du questionnaire.",
            "proposal_source": "Examen clinique complet",
        },
    )
    assert second.status_code == 201, second.text

    history = client.get(url, headers=headers)
    assert history.status_code == 200, history.text
    rows = history.json()
    assert len(rows) == 2
    assert {row["conclusion_text"] for row in rows} == {
        "Conclusion retenue par le praticien.",
        "Conclusion corrigée et retenue après examen.",
    }
    assert next(row for row in rows if row["proposal_text"])["proposal_source"] == "Examen clinique complet"


def test_conclusions_are_append_only(client, db):
    owner = _make_user(db, "p3-conclusion-append@test.ma")
    patient = _make_patient(db, owner, "P3-CONCLUSION-2")
    headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/clinical-conclusions"

    created = client.post(url, headers=headers, json={"conclusion_text": "Conclusion initiale."})
    assert created.status_code == 201
    conclusion_id = created.json()["id"]

    assert client.put(f"{url}/{conclusion_id}", headers=headers, json={"conclusion_text": "Overwrite"}).status_code == 405
    assert client.delete(f"{url}/{conclusion_id}", headers=headers).status_code == 405

    history = client.get(url, headers=headers).json()
    assert len(history) == 1
    assert history[0]["conclusion_text"] == "Conclusion initiale."


def test_secretary_cannot_retain_conclusion_even_with_clinical_permission(client, db):
    owner = _make_user(db, "p3-conclusion-practice@test.ma")
    patient = _make_patient(db, owner, "P3-CONCLUSION-3")
    secretary = _make_user(
        db,
        "p3-conclusion-secretary@test.ma",
        role="SECRETAIRE",
        employer_id=owner.id,
        permissions={"patients": True, "clinical": True},
    )
    headers = _headers(client, secretary)
    url = f"/api/patients/{patient.id}/clinical-conclusions"

    response = client.post(url, headers=headers, json={"conclusion_text": "Ne doit pas être retenue."})
    assert response.status_code == 403, response.text


def test_conclusions_are_tenant_scoped(client, db):
    owner = _make_user(db, "p3-conclusion-tenant-a@test.ma")
    patient = _make_patient(db, owner, "P3-CONCLUSION-4")
    foreign_owner = _make_user(db, "p3-conclusion-tenant-b@test.ma")
    foreign_headers = _headers(client, foreign_owner)
    url = f"/api/patients/{patient.id}/clinical-conclusions"

    assert client.get(url, headers=foreign_headers).status_code == 403
    assert client.post(url, headers=foreign_headers, json={"conclusion_text": "Cross tenant"}).status_code == 403


def test_conclusion_requires_non_empty_practitioner_text(client, db):
    owner = _make_user(db, "p3-conclusion-validation@test.ma")
    patient = _make_patient(db, owner, "P3-CONCLUSION-5")
    headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/clinical-conclusions"

    response = client.post(url, headers=headers, json={"conclusion_text": "   "})
    assert response.status_code == 422, response.text
