from backend import models


def _make_patient(client, auth_headers):
    response = client.post(
        "/api/patients/",
        json={
            "nom": "ALLOCATION",
            "prenom": "P2F",
            "date_naissance": "1988-04-20",
            "sexe": "M",
            "telephone": "0612345679",
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def test_paid_honoraires_allocates_exact_payment_to_each_created_acte(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers)
    response = client.post(
        "/api/documents/generate",
        json={
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [
                    {"acte": "Détartrage", "dent": "-", "montant": 400.0, "mode_reglement": "TPE"},
                    {"acte": "Couronne céramique", "dent": "36", "montant": 2500.0, "mode_reglement": "TPE"},
                ],
                "teeth_data": [],
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text

    actes = (
        db.query(models.Acte)
        .filter(models.Acte.patient_id == patient_id)
        .order_by(models.Acte.montant)
        .all()
    )
    assert len(actes) == 2

    payments = (
        db.query(models.Payment)
        .filter(models.Payment.patient_id == patient_id)
        .order_by(models.Payment.amount)
        .all()
    )
    assert len(payments) == 2
    assert [payment.amount for payment in payments] == [400.0, 2500.0]
    assert [payment.acte_id for payment in payments] == [actes[0].id, actes[1].id]
    assert sum(payment.amount for payment in payments) == 2900.0
    assert all(
        (payment.payment_method.value if hasattr(payment.payment_method, "value") else payment.payment_method) == "CARTE"
        for payment in payments
    )
