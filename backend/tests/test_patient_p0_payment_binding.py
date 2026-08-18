from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers.accounting import record_payment
from backend.schemas.payments import PaymentCreate
from backend.tests.conftest import make_user


def _make_patient(db, owner, dossier: str, nom: str):
    patient = models.Patient(
        nom=nom,
        prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
        numero_dossier=dossier,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_payment_rejects_act_from_another_patient(db):
    owner = make_user(db, email="payment-act@cabinet.ma")
    patient_a = _make_patient(db, owner, "PA", "PATIENTA")
    patient_b = _make_patient(db, owner, "PB", "PATIENTB")
    acte_b = models.Acte(
        patient_id=patient_b.id,
        praticien_id=owner.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin B",
        montant=500,
    )
    db.add(acte_b)
    db.commit()
    db.refresh(acte_b)

    with pytest.raises(HTTPException) as exc:
        record_payment(
            PaymentCreate(
                patient_id=patient_a.id,
                amount=100,
                payment_method="CARTE",
                acte_id=acte_b.id,
            ),
            db=db,
            current_user=owner,
        )

    assert exc.value.status_code == 409
    assert db.query(models.Payment).count() == 0
    assert acte_b.statut_paiement == models.PaiementStatut.EN_ATTENTE


def test_payment_rejects_installment_from_another_patient(db):
    owner = make_user(db, email="payment-installment@cabinet.ma")
    patient_a = _make_patient(db, owner, "IA", "PATIENTA")
    patient_b = _make_patient(db, owner, "IB", "PATIENTB")
    plan_b = models.InstallmentPlan(
        patient_id=patient_b.id,
        title="Plan B",
        total_amount=600,
    )
    db.add(plan_b)
    db.flush()
    installment_b = models.Installment(
        plan_id=plan_b.id,
        label="Versement B",
        amount=200,
        due_date=datetime.now() + timedelta(days=30),
    )
    db.add(installment_b)
    db.commit()
    db.refresh(installment_b)

    with pytest.raises(HTTPException) as exc:
        record_payment(
            PaymentCreate(
                patient_id=patient_a.id,
                amount=100,
                payment_method="VIREMENT",
                installment_id=installment_b.id,
            ),
            db=db,
            current_user=owner,
        )

    assert exc.value.status_code == 409
    assert db.query(models.Payment).count() == 0


def test_payment_rejects_act_and_installment_together(db):
    owner = make_user(db, email="payment-both@cabinet.ma")
    patient = _make_patient(db, owner, "BOTH", "PATIENT")
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=owner.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin",
        montant=500,
    )
    plan = models.InstallmentPlan(
        patient_id=patient.id,
        title="Plan",
        total_amount=500,
    )
    db.add_all([acte, plan])
    db.flush()
    installment = models.Installment(
        plan_id=plan.id,
        label="Versement",
        amount=500,
        due_date=datetime.now() + timedelta(days=30),
    )
    db.add(installment)
    db.commit()
    db.refresh(acte)
    db.refresh(installment)

    with pytest.raises(HTTPException) as exc:
        record_payment(
            PaymentCreate(
                patient_id=patient.id,
                amount=100,
                payment_method="ESPECES",
                acte_id=acte.id,
                installment_id=installment.id,
            ),
            db=db,
            current_user=owner,
        )

    assert exc.value.status_code == 422
    assert db.query(models.Payment).count() == 0


def test_valid_act_payment_updates_only_bound_act(db):
    owner = make_user(db, email="payment-valid@cabinet.ma")
    patient = _make_patient(db, owner, "VALID", "PATIENT")
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=owner.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin",
        montant=500,
    )
    db.add(acte)
    db.commit()
    db.refresh(acte)

    payment = record_payment(
        PaymentCreate(
            patient_id=patient.id,
            amount=200,
            payment_method="CARTE",
            acte_id=acte.id,
        ),
        db=db,
        current_user=owner,
    )

    db.refresh(acte)
    assert payment.patient_id == patient.id
    assert payment.acte_id == acte.id
    assert payment.payment_method == models.PaymentMethod.CARTE
    assert acte.statut_paiement == models.PaiementStatut.PARTIEL
    assert acte.is_collected is False


def test_accounting_router_has_no_legacy_installment_routes():
    source = Path("backend/routers/accounting.py").read_text(encoding="utf-8")
    for banned in (
        '@router.post("/plans"',
        '@router.get("/plans/patient/{patient_id}"',
        '@router.put("/installments/{installment_id}"',
        '@router.delete("/plans/{plan_id}"',
    ):
        assert banned not in source
