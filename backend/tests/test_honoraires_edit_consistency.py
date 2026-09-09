from datetime import date, datetime

from backend import models
from backend.services.accounting_service import accounting_service
from backend.services.honoraires_persistence import persist_honoraires_lines


def _patient(db, dentiste):
    patient = models.Patient(
        nom="TEST",
        prenom="Honoraires",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _persist(db, *, patient, dentiste, document_id, items):
    return persist_honoraires_lines(
        db,
        patient_id=patient.id,
        practitioner_id=dentiste.id,
        document_archive_id=document_id,
        document_created_at=datetime(2026, 8, 20, 10, 0),
        items=items,
        payment_status=models.PaiementStatut.PAYE,
        is_accounted=True,
        validated_by="Dr. Test",
    )


def test_edit_honoraires_replaces_amount_lines_and_business_date(db, dentiste):
    patient = _patient(db, dentiste)
    document_id = 99101

    _persist(
        db,
        patient=patient,
        dentiste=dentiste,
        document_id=document_id,
        items=[
            {"acte": "Soin A", "montant": 600, "mode_reglement": "Espèces", "date": "2026-08-20"},
            {"acte": "Soin B", "montant": 400, "mode_reglement": "Espèces", "date": "2026-08-20"},
        ],
    )
    db.commit()

    original_acte_ids = [a.id for a in db.query(models.Acte).order_by(models.Acte.id).all()]
    original_payment_ids = [p.id for p in db.query(models.Payment).order_by(models.Payment.id).all()]
    assert sum(a.montant for a in db.query(models.Acte).filter(models.Acte.deleted_at.is_(None)).all()) == 1000
    assert sum(p.amount for p in db.query(models.Payment).all()) == 1000

    # Deux semaines plus tard, le même document est corrigé : montant plus élevé
    # ET date déplacée vers le mois suivant. Aucun nouveau document comptable logique.
    _persist(
        db,
        patient=patient,
        dentiste=dentiste,
        document_id=document_id,
        items=[
            {"acte": "Soin A corrigé", "montant": 800, "mode_reglement": "Espèces", "date": "2026-09-03"},
            {"acte": "Soin B", "montant": 500, "mode_reglement": "Espèces", "date": "2026-09-03"},
        ],
    )
    db.commit()

    active_actes = db.query(models.Acte).filter(models.Acte.deleted_at.is_(None)).order_by(models.Acte.id).all()
    payments = db.query(models.Payment).order_by(models.Payment.id).all()
    assert [a.id for a in active_actes] == original_acte_ids
    assert [p.id for p in payments] == original_payment_ids
    assert sum(a.montant for a in active_actes) == 1300
    assert sum(p.amount for p in payments) == 1300
    assert {a.date_debut.date() for a in active_actes} == {date(2026, 9, 3)}
    assert {p.payment_date.date() for p in payments} == {date(2026, 9, 3)}

    september = accounting_service.get_finance_kpis(db, dentiste.id, date(2026, 9, 3))
    assert september["today_revenue"] == 1300
    assert september["month_revenue"] == 1300

    # Une nouvelle correction diminue le total et supprime une ligne : l'ancienne
    # ligne reste auditable mais sort des comptes, son paiement généré est annulé.
    _persist(
        db,
        patient=patient,
        dentiste=dentiste,
        document_id=document_id,
        items=[
            {"acte": "Soin A corrigé", "montant": 700, "mode_reglement": "Espèces", "date": "2026-09-03"},
        ],
    )
    db.commit()

    active_actes = db.query(models.Acte).filter(models.Acte.deleted_at.is_(None)).all()
    assert len(active_actes) == 1
    assert active_actes[0].id == original_acte_ids[0]
    assert active_actes[0].montant == 700

    september = accounting_service.get_finance_kpis(db, dentiste.id, date(2026, 9, 3))
    assert september["today_revenue"] == 700
    assert september["month_revenue"] == 700

    august = accounting_service.get_finance_kpis(db, dentiste.id, date(2026, 8, 20))
    assert august["today_revenue"] == 0
    assert august["month_revenue"] == 0
