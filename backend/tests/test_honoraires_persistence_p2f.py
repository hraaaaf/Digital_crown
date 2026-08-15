from datetime import datetime

import pytest

from backend import models
from backend.services.honoraires_persistence import (
    normalize_document_payment_method,
    persist_honoraires_lines,
)


def _make_patient(db, dentiste):
    patient = models.Patient(
        nom="PERSIST",
        prenom="P2F",
        date_naissance=datetime(1988, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.flush()
    return patient


def _make_document(db, patient, dentiste):
    doc = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename="p2f.pdf",
        original_filename="p2f.pdf",
        document_group_id="p2f-group",
        version_number=1,
        is_latest_version=True,
        file_hash="p2f-hash",
        file_size=1,
        file_path="/tmp/p2f.pdf",
        is_accounted=True,
        payment_status=models.PaiementStatut.PAYE,
        is_collected=True,
        clinical_data={},
    )
    db.add(doc)
    db.flush()
    return doc


def test_persist_honoraires_lines_links_exact_payment_to_each_acte(db, dentiste):
    patient = _make_patient(db, dentiste)
    doc = _make_document(db, patient, dentiste)

    actes, payments = persist_honoraires_lines(
        db,
        patient_id=patient.id,
        practitioner_id=dentiste.id,
        document_archive_id=doc.id,
        document_created_at=datetime(2026, 8, 15, 12, 0),
        items=[
            {"acte": "Détartrage", "montant": 400.0, "mode_reglement": "TPE"},
            {"acte": "Couronne céramique", "montant": 2500.0, "mode_reglement": "TPE"},
        ],
        payment_status=models.PaiementStatut.PAYE,
        is_accounted=True,
        validated_by="Dr Test",
    )
    db.flush()

    assert len(actes) == 2
    assert len(payments) == 2
    assert [payment.acte_id for payment in payments] == [actes[0].id, actes[1].id]
    assert [payment.amount for payment in payments] == [400.0, 2500.0]
    assert sum(payment.amount for payment in payments) == 2900.0
    assert all(
        (payment.payment_method.value if hasattr(payment.payment_method, "value") else payment.payment_method) == "CARTE"
        for payment in payments
    )


def test_persist_honoraires_lines_en_attente_creates_no_payment(db, dentiste):
    patient = _make_patient(db, dentiste)
    doc = _make_document(db, patient, dentiste)

    actes, payments = persist_honoraires_lines(
        db,
        patient_id=patient.id,
        practitioner_id=dentiste.id,
        document_archive_id=doc.id,
        document_created_at=datetime(2026, 8, 15, 12, 0),
        items=[{"acte": "Détartrage", "montant": 400.0, "mode_reglement": "Espèces"}],
        payment_status=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        validated_by="Dr Test",
    )
    db.flush()

    assert len(actes) == 1
    assert payments == []
    assert actes[0].statut_paiement == models.PaiementStatut.EN_ATTENTE


def test_unknown_document_payment_method_is_rejected():
    with pytest.raises(ValueError, match="Mode de paiement invalide"):
        normalize_document_payment_method("crypto")
