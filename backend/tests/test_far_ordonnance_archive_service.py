from types import SimpleNamespace

import pytest

from backend import models
from backend.schemas.documents import MedicationItem, OrdonnanceData
from backend.services.far_ordonnance_archive_service import archive_far_ordonnance_from_source


def _patient(*, assurance="MUTUELLE_FAR"):
    return SimpleNamespace(id=12, assurance=assurance, prenom="Patient", nom="Test")


def _source():
    return SimpleNamespace(id=98, patient_id=12, document_type=models.DocumentType.ORDONNANCE)


def _ordonnance():
    return OrdonnanceData(medications=[MedicationItem(
        nom="MEDICAMENT TEST",
        dosage="500 mg",
        forme="comprime",
        posologie="1 cp matin et soir",
    )])


def test_non_far_patient_is_a_noop():
    assert archive_far_ordonnance_from_source(
        None,
        patient=_patient(assurance="CNSS"),
        source_ordonnance_document=_source(),
        ordonnance=_ordonnance(),
        uploaded_by_id=7,
    ) is None


def test_far_source_must_be_an_ordonnance_archive():
    source = _source()
    source.document_type = models.DocumentType.AUTRE
    with pytest.raises(ValueError, match="source must be an archived ordonnance"):
        archive_far_ordonnance_from_source(
            None,
            patient=_patient(),
            source_ordonnance_document=source,
            ordonnance=_ordonnance(),
            uploaded_by_id=7,
        )


def test_far_source_must_belong_to_same_patient():
    source = _source()
    source.patient_id = 99
    with pytest.raises(ValueError, match="another patient"):
        archive_far_ordonnance_from_source(
            None,
            patient=_patient(),
            source_ordonnance_document=source,
            ordonnance=_ordonnance(),
            uploaded_by_id=7,
        )
