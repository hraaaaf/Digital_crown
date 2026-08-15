from datetime import datetime

from backend import models


def _make_patient(db, dentiste):
    patient = models.Patient(
        nom="PAYMENT",
        prenom="Contract",
        date_naissance=datetime(1988, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def test_payment_amount_must_be_strictly_positive(client, db, auth_headers, dentiste):
    patient = _make_patient(db, dentiste)

    for amount in (0, -10):
        response = client.post(
            "/api/accounting/payments",
            json={
                "patient_id": patient.id,
                "amount": amount,
                "payment_method": "ESPECES",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422, response.text

    assert db.query(models.Payment).filter(models.Payment.patient_id == patient.id).count() == 0


def test_payment_method_must_be_known(client, db, auth_headers, dentiste):
    patient = _make_patient(db, dentiste)

    response = client.post(
        "/api/accounting/payments",
        json={
            "patient_id": patient.id,
            "amount": 250,
            "payment_method": "INVENTE",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422, response.text
    assert db.query(models.Payment).filter(models.Payment.patient_id == patient.id).count() == 0


def test_valid_explicit_payment_persists_exact_amount_and_method(client, db, auth_headers, dentiste):
    patient = _make_patient(db, dentiste)

    response = client.post(
        "/api/accounting/payments",
        json={
            "patient_id": patient.id,
            "amount": 375.5,
            "payment_method": "CHEQUE",
            "notes": "Encaissement explicite P2-B",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["amount"] == 375.5
    assert body["payment_method"] == "CHEQUE"

    payment = db.query(models.Payment).filter(models.Payment.patient_id == patient.id).one()
    assert payment.amount == 375.5
    method_value = payment.payment_method.value if hasattr(payment.payment_method, "value") else payment.payment_method
    assert method_value == "CHEQUE"
