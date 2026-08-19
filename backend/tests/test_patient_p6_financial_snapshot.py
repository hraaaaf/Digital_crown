from datetime import datetime

from backend import models
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _make_user(db, email, *, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet="P6 Finance Test",
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
        nom="FINANCE",
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


def test_snapshot_distinguishes_absent_billing_base_from_real_zero(client, db):
    owner = _make_user(db, "p6-finance-owner@test.ma")
    patient = _make_patient(db, owner, "P6-FIN-1")
    headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/financial-snapshot"

    empty = client.get(url, headers=headers)
    assert empty.status_code == 200, empty.text
    assert empty.json()["has_billing_data"] is False
    assert empty.json()["total_billed"] == 0
    assert empty.json()["remaining_due"] == 0

    db.add(models.Acte(
        patient_id=patient.id,
        praticien_id=owner.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin conservateur",
        montant=250.0,
    ))
    db.commit()

    billed = client.get(url, headers=headers)
    assert billed.status_code == 200, billed.text
    body = billed.json()
    assert body["has_billing_data"] is True
    assert body["total_billed"] == 250.0
    assert body["total_collected"] == 0.0
    assert body["remaining_due"] == 250.0


def test_snapshot_requires_accounting_or_payments_for_subaccount(client, db):
    owner = _make_user(db, "p6-finance-practice@test.ma")
    patient = _make_patient(db, owner, "P6-FIN-2")
    url = f"/api/patients/{patient.id}/financial-snapshot"

    patients_only = _make_user(
        db,
        "p6-finance-patients-only@test.ma",
        employer_id=owner.id,
        permissions={"patients": True},
    )
    denied = client.get(url, headers=_headers(client, patients_only))
    assert denied.status_code == 403, denied.text

    payments_user = _make_user(
        db,
        "p6-finance-payments@test.ma",
        employer_id=owner.id,
        permissions={"patients": True, "payments": True},
    )
    allowed = client.get(url, headers=_headers(client, payments_user))
    assert allowed.status_code == 200, allowed.text
