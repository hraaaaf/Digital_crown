from datetime import date, datetime

from backend import models
from backend.services.accounting_service import accounting_service
from backend.services.archive_service import ArchiveService
from backend.services.honoraires_persistence import persist_honoraires_lines
from backend.services.installment_reconciliation import reconcile_document_installments


def _patient(db, dentiste, suffix: str):
    patient = models.Patient(
        nom=f"RECON-{suffix}",
        prenom="Honoraires",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _document(db, patient, dentiste, suffix: str, payment_status):
    doc = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename=f"recon-{suffix}.pdf",
        original_filename=f"recon-{suffix}.pdf",
        document_group_id=f"recon-group-{suffix}",
        version_number=1,
        is_latest_version=True,
        file_hash=f"recon-hash-{suffix}",
        file_size=1,
        file_path=f"/tmp/recon-{suffix}.pdf",
        is_accounted=True,
        payment_status=payment_status,
        is_collected=payment_status == models.PaiementStatut.PAYE,
        status=models.DocumentStatus.ACTIF,
        clinical_data={},
    )
    db.add(doc)
    db.flush()
    return doc


def test_paid_note_trash_and_restore_reconciles_accounting_and_finance(
    client, auth_headers, db, dentiste
):
    patient = _patient(db, dentiste, "paid")
    doc = _document(db, patient, dentiste, "paid", models.PaiementStatut.PAYE)

    actes, _ = persist_honoraires_lines(
        db,
        patient_id=patient.id,
        practitioner_id=dentiste.id,
        document_archive_id=doc.id,
        document_created_at=datetime(2026, 9, 20, 10, 0),
        items=[
            {
                "acte": "Soin A",
                "montant": 600.0,
                "mode_reglement": "ESPECES",
                "date": "2026-09-20",
            },
            {
                "acte": "Soin B",
                "montant": 400.0,
                "mode_reglement": "ESPECES",
                "date": "2026-09-20",
            },
        ],
        payment_status=models.PaiementStatut.PAYE,
        is_accounted=True,
        validated_by="Dr Test",
    )
    db.commit()
    assert len(actes) == 2

    before = client.get(
        f"/api/accounting/honoraires?patient_id={patient.id}&year=2026&month=9",
        headers=auth_headers,
    )
    assert before.status_code == 200, before.text
    before_items = before.json()["items"]
    assert len(before_items) == 2
    assert {item["document_archive_id"] for item in before_items} == {doc.id}
    assert before.json()["total_amount"] == 1000.0
    assert before.json()["total_collected"] == 1000.0

    finance_before = accounting_service.get_finance_kpis(
        db, dentiste.id, date(2026, 9, 20)
    )
    assert finance_before["today_revenue"] == 1000.0
    assert finance_before["month_revenue"] == 1000.0

    ArchiveService(db).move_to_trash(doc.id)

    after_trash = client.get(
        f"/api/accounting/honoraires?patient_id={patient.id}&year=2026&month=9",
        headers=auth_headers,
    )
    assert after_trash.status_code == 200, after_trash.text
    assert after_trash.json()["items"] == []
    assert after_trash.json()["total_amount"] == 0.0
    assert after_trash.json()["total_collected"] == 0.0

    finance_after_trash = accounting_service.get_finance_kpis(
        db, dentiste.id, date(2026, 9, 20)
    )
    assert finance_after_trash["today_revenue"] == 0.0
    assert finance_after_trash["month_revenue"] == 0.0
    assert finance_after_trash["total_debt"] == 0.0

    ArchiveService(db).restore_from_trash(doc.id)

    restored = client.get(
        f"/api/accounting/honoraires?patient_id={patient.id}&year=2026&month=9",
        headers=auth_headers,
    )
    assert restored.status_code == 200, restored.text
    assert len(restored.json()["items"]) == 2
    assert restored.json()["total_amount"] == 1000.0
    assert restored.json()["total_collected"] == 1000.0

    finance_restored = accounting_service.get_finance_kpis(
        db, dentiste.id, date(2026, 9, 20)
    )
    assert finance_restored["today_revenue"] == 1000.0
    assert finance_restored["month_revenue"] == 1000.0


def test_note_trash_cancels_only_its_pending_installments_and_restore_is_exact(
    db, dentiste
):
    patient = _patient(db, dentiste, "schedule")
    doc = _document(db, patient, dentiste, "schedule", models.PaiementStatut.EN_ATTENTE)

    actes, _ = persist_honoraires_lines(
        db,
        patient_id=patient.id,
        practitioner_id=dentiste.id,
        document_archive_id=doc.id,
        document_created_at=datetime(2026, 9, 20, 10, 0),
        items=[
            {
                "acte": "Plan global",
                "montant": 1000.0,
                "date": "2026-09-20",
            }
        ],
        payment_status=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        validated_by="Dr Test",
    )
    db.flush()

    plan = reconcile_document_installments(
        db,
        patient_id=patient.id,
        anchor_acte_id=actes[0].id,
        total_amount=1000.0,
        installments=[
            {"label": "Acompte", "amount": 400.0, "date": "2000-01-01", "sendReminder": True},
            {"label": "Solde", "amount": 600.0, "date": "2030-01-01"},
        ],
    )
    assert plan is not None
    db.commit()

    first, second = sorted(plan.installments, key=lambda row: row.id)
    second.status = "ANNULE"
    second.notes = "annulation métier préalable"
    db.commit()

    before = accounting_service.get_treasury_summary(db, dentiste.id)
    assert any(alert["amount"] == 400.0 for alert in before["proactive_alerts"])

    service = ArchiveService(db)
    service.move_to_trash(doc.id)
    first_trash_at = doc.deleted_at
    service.move_to_trash(doc.id)
    db.refresh(doc)
    db.refresh(first)
    db.refresh(second)

    assert doc.deleted_at == first_trash_at
    assert first.status == "ANNULE"
    assert (first.notes or "").startswith(f"__DC_TRASH_DOC__:{doc.id}\n")
    assert second.status == "ANNULE"
    assert second.notes == "annulation métier préalable"

    trashed = accounting_service.get_treasury_summary(db, dentiste.id)
    assert not any(alert["amount"] == 400.0 for alert in trashed["proactive_alerts"])
    assert trashed["pending_count"] == 0

    # Défense pour bases historiques : même si une vieille échéance reste EN_ATTENTE,
    # le Treasury Hub doit l'ignorer tant que l'Acte parent est en corbeille.
    first.status = "EN_ATTENTE"
    db.commit()
    defensive = accounting_service.get_treasury_summary(db, dentiste.id)
    assert not any(alert["amount"] == 400.0 for alert in defensive["proactive_alerts"])
    first.status = "ANNULE"
    db.commit()

    ArchiveService(db).restore_from_trash(doc.id)
    db.refresh(first)
    db.refresh(second)

    assert first.status == "EN_ATTENTE"
    assert first.notes == '{"sendReminder": true}'
    assert second.status == "ANNULE"
    assert second.notes == "annulation métier préalable"

    restored = accounting_service.get_treasury_summary(db, dentiste.id)
    assert any(alert["amount"] == 400.0 for alert in restored["proactive_alerts"])
