from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionShareGrant
from backend.services.patient_companion_finance import project_finance, resolve_shared_invoice


def _access(db, dentiste, suffix: str):
    patient = models.Patient(
        numero_dossier=f"PC06-{suffix}-{uuid.uuid4().hex[:6]}",
        nom=f"Finance-{suffix}",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"pc06:{suffix}:{uuid.uuid4()}")
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    return patient, access


def _invoice(db, dentiste, patient, tmp_path, amount: float):
    raw = b"%PDF-1.4\nPC06 invoice\n%%EOF\n"
    path = tmp_path / f"{uuid.uuid4()}.pdf"
    path.write_bytes(raw)
    doc = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename=path.name,
        original_filename=path.name,
        document_group_id=uuid.uuid4().hex,
        version_number=1,
        is_latest_version=True,
        file_hash=hashlib.sha256(raw).hexdigest(),
        file_size=len(raw),
        file_path=str(path),
        title="Note d'honoraires",
        status=models.DocumentStatus.ACTIF,
        clinical_data={"doc_date": "2026-09-01", "total_amount": amount},
        is_accounted=True,
        is_collected=False,
    )
    db.add(doc)
    db.flush()
    share = PatientCompanionShareGrant(
        employer_id=dentiste.id,
        patient_id=patient.id,
        resource_type="document",
        resource_id=doc.id,
        granted_by_user_id=dentiste.id,
    )
    db.add(share)
    db.flush()
    return doc, share


def test_pc06_projection_uses_active_accounting_truth_and_no_persistence(db, dentiste):
    patient, access = _access(db, dentiste, "A")
    active = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin",
        montant=1000,
        statut_paiement=models.PaiementStatut.PARTIEL,
        is_accounted=True,
    )
    trashed = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Ancien soin",
        montant=900,
        statut_paiement=models.PaiementStatut.PAYE,
        is_accounted=True,
        deleted_at=datetime.utcnow(),
    )
    db.add_all([active, trashed])
    db.flush()
    db.add_all([
        models.Payment(
            patient_id=patient.id,
            acte_id=active.id,
            amount=300,
            payment_method=models.PaymentMethod.CARTE,
            payment_date=datetime.utcnow(),
        ),
        models.Payment(
            patient_id=patient.id,
            acte_id=trashed.id,
            amount=900,
            payment_method=models.PaymentMethod.CARTE,
            payment_date=datetime.utcnow(),
            notes="Lien Doc ID: 999",
        ),
    ])
    db.commit()

    finance = project_finance(db, access)

    assert finance["summary"] == {"billed": 1000.0, "collected": 300.0, "remaining_due": 700.0}
    assert len(finance["payments"]) == 1
    assert finance["payments"][0]["amount"] == 300.0
    assert finance["online_payment"] == {"available": False}
    assert not db.new
    assert not db.dirty
    assert not db.deleted


def test_pc06_projection_is_patient_isolated(db, dentiste):
    patient_a, access_a = _access(db, dentiste, "A")
    patient_b, _access_b = _access(db, dentiste, "B")
    db.add_all([
        models.Acte(
            patient_id=patient_a.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="A",
            montant=500,
            is_accounted=True,
        ),
        models.Acte(
            patient_id=patient_b.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="B",
            montant=8000,
            is_accounted=True,
        ),
    ])
    db.commit()

    finance = project_finance(db, access_a)
    assert finance["summary"]["billed"] == 500.0
    assert finance["summary"]["remaining_due"] == 500.0



def test_pc06_projection_rejects_tenant_mismatch_even_for_existing_patient(db, dentiste):
    patient, _access_ok = _access(db, dentiste, "TENANT")
    db.add(models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Secret tenant A",
        montant=900,
        is_accounted=True,
    ))
    db.commit()

    forged = PatientCompanionAccess(
        identity_id=_access_ok.identity_id,
        employer_id=dentiste.id + 999,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    finance = project_finance(db, forged)
    assert finance["summary"] == {"billed": 0.0, "collected": 0.0, "remaining_due": 0.0}
    assert finance["payments"] == []
    assert finance["schedules"] == []
    assert finance["invoices"] == []


def test_pc06_installments_bound_to_trashed_acte_are_hidden(db, dentiste):
    patient, access = _access(db, dentiste, "PLAN")
    active = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.PROTHESE,
        libelle="Actif",
        montant=1200,
        is_accounted=True,
    )
    trashed = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.PROTHESE,
        libelle="Corbeille",
        montant=1500,
        is_accounted=True,
        deleted_at=datetime.utcnow(),
    )
    db.add_all([active, trashed])
    db.flush()
    plan_active = models.InstallmentPlan(patient_id=patient.id, acte_id=active.id, title="Actif", total_amount=1200)
    plan_hidden = models.InstallmentPlan(patient_id=patient.id, acte_id=trashed.id, title="Masqué", total_amount=1500)
    db.add_all([plan_active, plan_hidden])
    db.flush()
    db.add_all([
        models.Installment(plan_id=plan_active.id, label="A1", amount=600, due_date=datetime.utcnow() + timedelta(days=10)),
        models.Installment(plan_id=plan_hidden.id, label="H1", amount=750, due_date=datetime.utcnow() + timedelta(days=10)),
    ])
    db.commit()

    finance = project_finance(db, access)
    assert [plan["title"] for plan in finance["schedules"]] == ["Actif"]


def test_pc06_invoice_requires_active_exact_share_and_uses_business_date(db, dentiste, tmp_path):
    patient, access = _access(db, dentiste, "INV")
    doc, share = _invoice(db, dentiste, patient, tmp_path, 650)
    db.commit()

    finance = project_finance(db, access)
    assert len(finance["invoices"]) == 1
    invoice = finance["invoices"][0]
    assert invoice["document_id"] == doc.id
    assert invoice["amount"] == 650.0
    assert invoice["issued_at"].date().isoformat() == "2026-09-01"
    assert resolve_shared_invoice(db, access, share.public_id)[1].id == doc.id

    share.revoked_at = datetime.utcnow()
    db.commit()
    assert project_finance(db, access)["invoices"] == []
    assert resolve_shared_invoice(db, access, share.public_id) is None


def test_pc06_standalone_invoice_counts_once_and_linked_invoice_does_not_double_count(db, dentiste, tmp_path):
    patient, access = _access(db, dentiste, "COUNT")
    standalone, _share = _invoice(db, dentiste, patient, tmp_path, 400)
    linked, _share2 = _invoice(db, dentiste, patient, tmp_path, 700)
    db.flush()
    db.add(models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Depuis note",
        montant=700,
        is_accounted=True,
        document_archive_id=linked.id,
    ))
    db.commit()

    finance = project_finance(db, access)
    assert finance["summary"]["billed"] == 1100.0
    assert {item["document_id"] for item in finance["invoices"]} == {standalone.id, linked.id}
