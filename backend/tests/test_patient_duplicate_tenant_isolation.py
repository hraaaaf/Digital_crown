from datetime import datetime
import uuid

from backend import models
from backend.routers.patients import check_duplicate_patient
from backend.security import get_password_hash


def _patient(db, owner_id, nom="DUPONT", prenom="Alice"):
    patient = models.Patient(
        nom=nom,
        prenom=prenom,
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=owner_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_duplicate_lookup_is_scoped_to_employer(db, dentiste):
    foreign = models.User(
        email=f"foreign-{uuid.uuid4().hex[:8]}@test.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        is_active=True,
        is_licensed=True,
    )
    db.add(foreign)
    db.commit()
    db.refresh(foreign)

    own_patient = _patient(db, dentiste.id)
    foreign_patient = _patient(db, foreign.id)

    own = check_duplicate_patient(
        db, "DUPONT", "Alice", datetime(1990, 1, 1), dentiste.id
    )
    other = check_duplicate_patient(
        db, "DUPONT", "Alice", datetime(1990, 1, 1), foreign.id
    )
    assert own.id == own_patient.id
    assert other.id == foreign_patient.id


def test_same_identity_in_other_tenant_does_not_block_creation(client, db, dentiste):
    _patient(db, dentiste.id)

    foreign_email = f"foreign-{uuid.uuid4().hex[:8]}@test.ma"
    foreign = models.User(
        email=foreign_email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Foreign",
        is_active=True,
        is_licensed=True,
    )
    db.add(foreign)
    db.commit()

    login = client.post(
        "/api/auth/login",
        data={"username": foreign_email, "password": "TestPass123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        "/api/patients/",
        json={
            "nom": "DUPONT",
            "prenom": "Alice",
            "date_naissance": "1990-01-01T00:00:00",
            "sexe": "F",
        },
        headers=headers,
    )
    assert response.status_code in (200, 201), response.text
    assert response.json()["employer_id"] == foreign.id
