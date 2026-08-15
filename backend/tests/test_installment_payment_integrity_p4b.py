from backend import models


def _make_patient(client, auth_headers):
    response = client.post(
        "/api/patients/",
        json={
            "nom": "ECHEANCIER",
            "prenom": "P4B",
            "date_naissance": "1988-04-20",
            "sexe": "M",
            "telephone": "0612345680",
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _create_plan(client, auth_headers, patient_id, amount=400.0):
    response = client.post(
        "/api/installments/",
        json={
            "patient_id": patient_id,
            "title": "Plan P4-B",
            "total_amount": amount,
            "installments": [
                {
                    "label": "Échéance 1",
                    "amount": amount,
                    "due_date": "2026-09-01T00:00:00",
                    "status": "EN_ATTENTE",
                }
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_create_installment_plan_uses_one_commit(client, auth_headers, db, monkeypatch):
    patient_id = _make_patient(client, auth_headers)
    original_commit = db.commit
    commit_count = 0

    def counting_commit():
        nonlocal commit_count
        commit_count += 1
        return original_commit()

    monkeypatch.setattr(db, "commit", counting_commit)
    plan = _create_plan(client, auth_headers, patient_id)

    assert plan["patient_id"] == patient_id
    assert len(plan["installments"]) == 1
    assert commit_count == 1


def test_mark_paid_requires_explicit_method_and_uses_updated_amount(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers)
    plan = _create_plan(client, auth_headers, patient_id, amount=400.0)
    installment_id = plan["installments"][0]["id"]

    missing_method = client.put(
        f"/api/installments/{installment_id}",
        json={"status": "PAYE", "amount": 450.0},
        headers=auth_headers,
    )
    assert missing_method.status_code == 422, missing_method.text
    assert db.query(models.Payment).filter(models.Payment.installment_id == installment_id).count() == 0

    paid = client.put(
        f"/api/installments/{installment_id}",
        json={"status": "PAYE", "amount": 450.0, "payment_method": "CARTE"},
        headers=auth_headers,
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["amount"] == 450.0
    assert paid.json()["status"] == "PAYE"

    payment = db.query(models.Payment).filter(models.Payment.installment_id == installment_id).one()
    assert payment.amount == 450.0
    method = payment.payment_method.value if hasattr(payment.payment_method, "value") else payment.payment_method
    assert method == "CARTE"


def test_paid_installment_cannot_be_reopened_or_repriced(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers)
    plan = _create_plan(client, auth_headers, patient_id, amount=400.0)
    installment_id = plan["installments"][0]["id"]

    paid = client.put(
        f"/api/installments/{installment_id}",
        json={"status": "PAYE", "payment_method": "VIREMENT"},
        headers=auth_headers,
    )
    assert paid.status_code == 200, paid.text

    reopen = client.put(
        f"/api/installments/{installment_id}",
        json={"status": "EN_ATTENTE"},
        headers=auth_headers,
    )
    assert reopen.status_code == 409, reopen.text

    reprice = client.put(
        f"/api/installments/{installment_id}",
        json={"amount": 500.0},
        headers=auth_headers,
    )
    assert reprice.status_code == 409, reprice.text

    payment = db.query(models.Payment).filter(models.Payment.installment_id == installment_id).one()
    assert payment.amount == 400.0
