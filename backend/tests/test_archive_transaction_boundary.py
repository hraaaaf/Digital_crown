from datetime import datetime

from backend import models
from backend.services.archive_service import ArchiveService


def test_archive_can_join_caller_transaction_and_roll_back(db, dentiste):
    patient = models.Patient(
        nom='TEST',
        prenom='Transaction',
        date_naissance=datetime(1990, 1, 1),
        sexe='M',
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    service = ArchiveService(db)
    doc, _ = service.archive_document(
        patient_id=patient.id,
        file_content=b'%PDF-1.4\ntransaction-test',
        filename='transaction-test.pdf',
        doc_type=models.DocumentType.NOTE_HONORAIRES,
        uploaded_by_id=dentiste.id,
        clinical_data={'payments': [{'acte': 'Soin', 'montant': 1000}]},
        is_accounted=True,
        payment_status=models.PaiementStatut.EN_ATTENTE,
        commit=False,
    )
    doc_id = doc.id
    assert doc_id is not None
    assert db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).one().id == doc_id

    db.rollback()

    assert db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first() is None
