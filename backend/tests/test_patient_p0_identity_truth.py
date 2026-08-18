"""P0 Patient — identity truth and tenant-isolated duplicate detection."""
from datetime import datetime
import io
import uuid

import pytest
from pydantic import ValidationError

from backend import models
from backend.schemas.patient import PatientCreate, PatientUpdate
from backend.security import get_password_hash


def _make_user(db, *, email=None):
    user = models.User(
        email=email or f"p0-{uuid.uuid4().hex[:8]}@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr P0",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _make_patient(db, owner, *, nom="DUPONT", prenom="Alice", sexe="F"):
    patient = models.Patient(
        nom=nom,
        prenom=prenom,
        date_naissance=datetime(1990, 4, 12),
        sexe=sexe,
        employer_id=owner.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _identity_payload(**overrides):
    payload = {
        "nom": "DUPONT",
        "prenom": "Alice",
        "date_naissance": "1990-04-12",
        "sexe": "F",
    }
    payload.update(overrides)
    return payload


def test_duplicate_precheck_never_exposes_matching_patient_from_other_tenant(client, db, dentiste, auth_headers):
    tenant_b = _make_user(db)
    foreign_patient = _make_patient(db, tenant_b)

    response = client.post(
        "/api/patients/check-duplicate",
        json={"nom": "DUPONT", "prenom": "Alice", "date_naissance": "1990-04-12"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {"has_duplicate": False, "existing_patient": None}
    assert str(foreign_patient.id) not in response.text


def test_same_identity_is_allowed_in_two_tenants_and_detected_only_locally(client, db, dentiste, auth_headers):
    tenant_b = _make_user(db)
    foreign_patient = _make_patient(db, tenant_b)

    # Keep all tenant-A requests before logging tenant B into the shared TestClient.
    # The login endpoint may update client cookie state in addition to returning the
    # bearer token; interleaving logins would make this isolation test test its own
    # client state rather than the patient duplicate boundary.
    create_a = client.post("/api/patients/", json=_identity_payload(), headers=auth_headers)
    assert create_a.status_code == 200, create_a.text
    patient_a_id = create_a.json()["id"]
    assert patient_a_id != foreign_patient.id

    duplicate_a = client.post(
        "/api/patients/check-duplicate",
        json={"nom": "DUPONT", "prenom": "Alice", "date_naissance": "1990-04-12"},
        headers=auth_headers,
    )
    assert duplicate_a.status_code == 200
    assert duplicate_a.json()["existing_patient"]["id"] == patient_a_id

    headers_b = _headers(client, tenant_b)
    duplicate_b = client.post(
        "/api/patients/check-duplicate",
        json={"nom": "DUPONT", "prenom": "Alice", "date_naissance": "1990-04-12"},
        headers=headers_b,
    )

    assert duplicate_b.status_code == 200
    assert duplicate_b.json()["existing_patient"]["id"] == foreign_patient.id


def test_csv_import_duplicate_detection_is_tenant_scoped(client, db, dentiste, auth_headers):
    tenant_b = _make_user(db)
    _make_patient(db, tenant_b, nom="CSVOTHER", prenom="Tenant")

    csv_data = (
        "nom,prenom,date_naissance,sexe,telephone\n"
        "CSVOTHER,Tenant,1990-04-12,F,0600000000\n"
    ).encode("utf-8")
    response = client.post(
        "/api/patients/import-csv",
        files={"file": ("patients.csv", io.BytesIO(csv_data), "text/csv")},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["created"] == 1
    assert response.json()["skipped_duplicates"] == 0
    imported = db.query(models.Patient).filter(
        models.Patient.employer_id == dentiste.id,
        models.Patient.nom == "CSVOTHER",
    ).one()
    assert imported.prenom == "Tenant"


def test_csv_import_rejects_missing_or_invalid_sex_without_creating_rows(client, db, dentiste, auth_headers):
    csv_data = (
        "nom,prenom,date_naissance,sexe\n"
        "NOSEX,Patient,1991-01-01,\n"
        "BADSEX,Patient,1992-01-01,X\n"
    ).encode("utf-8")
    before = db.query(models.Patient).filter(models.Patient.employer_id == dentiste.id).count()

    response = client.post(
        "/api/patients/import-csv",
        files={"file": ("patients.csv", io.BytesIO(csv_data), "text/csv")},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 0
    assert len(body["errors"]) == 2
    assert db.query(models.Patient).filter(models.Patient.employer_id == dentiste.id).count() == before


@pytest.mark.parametrize("value", [None, "", " ", "X", "unknown"])
def test_patient_create_rejects_missing_blank_or_unknown_sex(value):
    payload = _identity_payload()
    if value is None:
        payload.pop("sexe")
    else:
        payload["sexe"] = value

    with pytest.raises(ValidationError):
        PatientCreate(**payload)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("M", "M"), ("homme", "M"), ("GARÇON", "M"), ("F", "F"), ("femme", "F"), ("féminin", "F")],
)
def test_patient_create_normalizes_only_explicit_unambiguous_sex_values(value, expected):
    patient = PatientCreate(**_identity_payload(sexe=value))
    assert patient.sexe == expected


def test_patient_update_can_omit_sex_but_rejects_blank_or_unknown_values():
    assert PatientUpdate(nom="MARTIN").sexe is None
    with pytest.raises(ValidationError):
        PatientUpdate(sexe="")
    with pytest.raises(ValidationError):
        PatientUpdate(sexe="X")
