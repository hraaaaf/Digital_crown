"""P0-E — installment plans linked to a billed Acte must stay reconciled."""
from datetime import datetime, timedelta

from backend import models


def _patient(db, dentiste, nom):
    patient = models.Patient(
        nom=nom,
        prenom="P0",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _acte(db, dentiste, patient, amount=1000.0):
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Acte lié P0",
        montant=amount,
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
    )
    db.add(acte)
    db.commit()
    db.refresh(acte)
    return acte


def _payload(patient_id, acte_id, amounts):
    due = (datetime.now() + timedelta(days=30)).isoformat()
    return {
        "patient_id": patient_id,
        "acte_id": acte_id,
        "title": "Échéancier acte P0",
        "total_amount": sum(amounts),
        "installments": [
            {"label": f"Versement {index + 1}", "amount": amount, "due_date": due}
            for index, amount in enumerate(amounts)
        ],
    }


def test_linked_plan_rejects_acte_from_another_patient(client, db, auth_headers, dentiste):
    patient_a = _patient(db, dentiste, "PLANLINKA")
    patient_b = _patient(db, dentiste, "PLANLINKB")
    acte_b = _acte(db, dentiste, patient_b)
    response = client.post("/api/installments/", json=_payload(patient_a.id, acte_b.id, [1000.0]), headers=auth_headers)
    assert response.status_code == 422, response.text
    assert db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_a.id).count() == 0


def test_linked_plan_must_cover_exact_current_remaining_due(client, db, auth_headers, dentiste):
    patient = _patient(db, dentiste, "PLANREMAIN")
    acte = _acte(db, dentiste, patient, amount=1000.0)
    db.add(models.Payment(patient_id=patient.id, acte_id=acte.id, amount=250.0, payment_method=models.PaymentMethod.ESPECES))
    db.commit()
    wrong = client.post("/api/installments/", json=_payload(patient.id, acte.id, [500.0]), headers=auth_headers)
    assert wrong.status_code == 422, wrong.text
    exact = client.post("/api/installments/", json=_payload(patient.id, acte.id, [375.0, 375.0]), headers=auth_headers)
    assert exact.status_code == 200, exact.text
    assert exact.json()["acte_id"] == acte.id
    assert exact.json()["total_amount"] == 750.0


def test_only_one_installment_plan_can_be_linked_to_same_acte(client, db, auth_headers, dentiste):
    patient = _patient(db, dentiste, "PLANDUP")
    acte = _acte(db, dentiste, patient)
    payload = _payload(patient.id, acte.id, [500.0, 500.0])
    first = client.post("/api/installments/", json=payload, headers=auth_headers)
    second = client.post("/api/installments/", json=payload, headers=auth_headers)
    assert first.status_code == 200, first.text
    assert second.status_code == 409, second.text
    assert db.query(models.InstallmentPlan).filter(models.InstallmentPlan.acte_id == acte.id).count() == 1


def test_installment_payments_keep_both_links_and_reconcile_acte_status(client, db, auth_headers, dentiste):
    patient = _patient(db, dentiste, "PLANPAY")
    acte = _acte(db, dentiste, patient)
    create = client.post("/api/installments/", json=_payload(patient.id, acte.id, [400.0, 600.0]), headers=auth_headers)
    assert create.status_code == 200, create.text
    installments = create.json()["installments"]
    first = client.put(f"/api/installments/{installments[0]['id']}", json={"status": "PAYE", "payment_method": "CARTE"}, headers=auth_headers)
    assert first.status_code == 200, first.text
    db.refresh(acte)
    assert acte.statut_paiement == models.PaiementStatut.PARTIEL
    assert acte.is_collected is False
    payment_one = db.query(models.Payment).filter(models.Payment.installment_id == installments[0]["id"]).one()
    assert payment_one.patient_id == patient.id
    assert payment_one.acte_id == acte.id
    second = client.put(f"/api/installments/{installments[1]['id']}", json={"status": "PAYE", "payment_method": "VIREMENT"}, headers=auth_headers)
    assert second.status_code == 200, second.text
    db.refresh(acte)
    assert acte.statut_paiement == models.PaiementStatut.PAYE
    assert acte.is_collected is True
    payment_two = db.query(models.Payment).filter(models.Payment.installment_id == installments[1]["id"]).one()
    assert payment_two.acte_id == acte.id
