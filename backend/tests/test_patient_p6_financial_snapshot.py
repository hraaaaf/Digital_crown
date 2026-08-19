from datetime import date, datetime, timedelta

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
    assert empty.json()["remaining_due"] is None

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


def test_snapshot_exposes_next_real_installment(client, db):
    owner = _make_user(db, "p6-finance-installment-owner@test.ma")
    patient = _make_patient(db, owner, "P6-FIN-3")
    headers = _headers(client, owner)

    plan = models.InstallmentPlan(
        patient_id=patient.id,
        total_amount=600.0,
        installment_count=2,
        status="ACTIF",
    )
    db.add(plan)
    db.flush()
    later = models.Installment(
        plan_id=plan.id,
        label="Échéance 2",
        amount=300.0,
        due_date=date.today() + timedelta(days=20),
        status="EN_ATTENTE",
    )
    sooner = models.Installment(
        plan_id=plan.id,
        label="Échéance 1",
        amount=300.0,
        due_date=date.today() + timedelta(days=7),
        status="EN_ATTENTE",
    )
    db.add_all([later, sooner])
    db.commit()

    response = client.get(f"/api/patients/{patient.id}/financial-snapshot", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["upcoming_installments_count"] == 2
    assert body["next_installment"]["label"] == "Échéance 1"
    assert body["next_installment"]["amount"] == 300.0
    assert body["next_installment"]["due_date"] == (date.today() + timedelta(days=7)).isoformat()


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

    accounting_user = _make_user(
        db,
        "p6-finance-accounting@test.ma",
        employer_id=owner.id,
        permissions={"patients": True, "accounting": True},
    )
    allowed_accounting = client.get(url, headers=_headers(client, accounting_user))
    assert allowed_accounting.status_code == 200, allowed_accounting.text
