"""P0 Patient — financial link integrity.

A payment must never mutate or reference an Acte/Installment owned by another
patient, even inside the same cabinet. Rejections must be side-effect free.
"""
from datetime import datetime

from backend import models


def _make_patient(db, dentiste, nom: str):
    patient = models.Patient(
        nom=nom,
        prenom="P0",
        date_naissance=datetime(1985, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _make_acte(db, dentiste, patient, montant=700.0):
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin P0",
        montant=montant,
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
    )
    db.add(acte)
    db.commit()
    db.refresh(acte)
    return acte


def _make_installment(db, patient, amount=500.0):
    plan = models.InstallmentPlan(
        patient_id=patient.id,
        title="Plan P0",
        total_amount=amount,
    )
    db.add(plan)
    db.flush()
    installment = models.Installment(
        plan_id=plan.id,
        label="Acompte P0",
        amount=amount,
        due_date=datetime(2026, 9, 1),
        status="EN_ATTENTE",
    )
    db.add(installment)
    db.commit()
    db.refresh(installment)
    return installment


def _payment_count(db):
    return db.query(models.Payment).count()


def test_payment_rejects_acte_owned_by_another_patient_without_side_effects(
    client, db, auth_headers, dentiste
):
    patient_a = _make_patient(db, dentiste, "P0PAYA")
    patient_b = _make_patient(db, dentiste, "P0PAYB")
    acte_b = _make_acte(db, dentiste, patient_b)
    before = _payment_count(db)

    response = client.post(
        "/api/accounting/payments",
        json={
            "patient_id": patient_a.id,
            "acte_id": acte_b.id,
            "amount": 200.0,
            "payment_method": "ESPECES",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409, response.text
    assert _payment_count(db) == before
    db.refresh(acte_b)
    assert acte_b.statut_paiement == models.PaiementStatut.EN_ATTENTE


def test_payment_rejects_installment_owned_by_another_patient_without_side_effects(
    client, db, auth_headers, dentiste
):
    patient_a = _make_patient(db, dentiste, "P0INSTA")
    patient_b = _make_patient(db, dentiste, "P0INSTB")
    installment_b = _make_installment(db, patient_b)
    before = _payment_count(db)

    response = client.post(
        "/api/accounting/payments",
        json={
            "patient_id": patient_a.id,
            "installment_id": installment_b.id,
            "amount": 200.0,
            "payment_method": "VIREMENT",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409, response.text
    assert _payment_count(db) == before
    db.refresh(installment_b)
    assert installment_b.status == "EN_ATTENTE"


def test_payment_rejects_acte_and_installment_combination_without_side_effects(
    client, db, auth_headers, dentiste
):
    patient = _make_patient(db, dentiste, "P0DOUBLELINK")
    acte = _make_acte(db, dentiste, patient)
    installment = _make_installment(db, patient)
    before = _payment_count(db)

    response = client.post(
        "/api/accounting/payments",
        json={
            "patient_id": patient.id,
            "acte_id": acte.id,
            "installment_id": installment.id,
            "amount": 200.0,
            "payment_method": "CARTE",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422, response.text
    assert _payment_count(db) == before


def test_payment_requires_explicit_payment_method(client, db, auth_headers, dentiste):
    patient = _make_patient(db, dentiste, "P0METHOD")
    before = _payment_count(db)

    response = client.post(
        "/api/accounting/payments",
        json={"patient_id": patient.id, "amount": 200.0},
        headers=auth_headers,
    )

    assert response.status_code == 422, response.text
    assert _payment_count(db) == before
