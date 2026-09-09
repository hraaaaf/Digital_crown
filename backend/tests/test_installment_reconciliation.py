from datetime import datetime

import pytest

from backend import models
from backend.services.installment_reconciliation import reconcile_document_installments


def _patient(db, dentiste):
    patient = models.Patient(
        nom='TEST', prenom='Echeancier', date_naissance=datetime(1990, 1, 1),
        sexe='M', employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _acte(db, patient, dentiste):
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle='Plan global',
        montant=1000,
        date_debut=datetime(2026, 9, 9),
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        document_archive_id=None,
    )
    db.add(acte)
    db.commit()
    db.refresh(acte)
    return acte


def test_reconcile_reuses_plan_and_never_resurrects_cancelled_installments(db, dentiste):
    patient = _patient(db, dentiste)
    acte = _acte(db, patient, dentiste)

    plan = reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=1000,
        installments=[
            {'label': 'Acompte', 'amount': 400, 'date': '2026-09-10'},
            {'label': 'Solde', 'amount': 600, 'date': '2026-10-10'},
        ],
    )
    db.commit()
    assert plan is not None
    plan_id = plan.id
    original_ids = [row.id for row in plan.installments]

    reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=700,
        installments=[{'label': 'Acompte corrigé', 'amount': 700, 'date': '2026-09-15'}],
    )
    db.commit()

    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).one()
    active = [row for row in plan.installments if row.status == 'EN_ATTENTE']
    cancelled = [row for row in plan.installments if row.status == 'ANNULE']
    assert len(active) == 1
    assert active[0].id == original_ids[0]
    assert active[0].amount == 700
    assert [row.id for row in cancelled] == [original_ids[1]]

    reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=1000,
        installments=[
            {'label': 'Acompte corrigé', 'amount': 700, 'date': '2026-09-15'},
            {'label': 'Nouveau solde', 'amount': 300, 'date': '2026-10-20'},
        ],
    )
    db.commit()

    plans = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.acte_id == acte.id).all()
    assert len(plans) == 1
    active = [row for row in plans[0].installments if row.status == 'EN_ATTENTE']
    assert len(active) == 2
    assert active[0].id == original_ids[0]
    assert active[1].id not in original_ids
    assert any(row.id == original_ids[1] and row.status == 'ANNULE' for row in plans[0].installments)


def test_reconcile_empty_schedule_cancels_pending_without_creating_empty_plan(db, dentiste):
    patient = _patient(db, dentiste)
    acte_without_plan = _acte(db, patient, dentiste)
    assert reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte_without_plan.id,
        total_amount=1000,
        installments=[],
    ) is None

    acte = _acte(db, patient, dentiste)
    plan = reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=1000,
        installments=[{'label': 'Solde', 'amount': 1000, 'date': '2026-10-10'}],
    )
    db.commit()
    assert plan is not None

    reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=1000,
        installments=[],
    )
    db.commit()

    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan.id).one()
    assert [row.status for row in plan.installments] == ['ANNULE']


def test_reconcile_refuses_mutating_paid_installment(db, dentiste):
    patient = _patient(db, dentiste)
    acte = _acte(db, patient, dentiste)
    plan = reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=acte.id,
        total_amount=1000,
        installments=[
            {'label': 'Acompte', 'amount': 400, 'date': '2026-09-10'},
            {'label': 'Solde', 'amount': 600, 'date': '2026-10-10'},
        ],
    )
    db.commit()
    assert plan is not None
    first = sorted(plan.installments, key=lambda row: row.id)[0]
    first.status = 'PAYE'
    db.commit()

    with pytest.raises(ValueError, match='déjà réglée'):
        reconcile_document_installments(
            db,
            patient_id=patient.id,
            anchor_acte_id=acte.id,
            total_amount=900,
            installments=[
                {'label': 'Acompte modifié', 'amount': 300, 'date': '2026-09-11'},
                {'label': 'Solde', 'amount': 600, 'date': '2026-10-10'},
            ],
        )
