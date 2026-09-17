from types import SimpleNamespace

import pytest

from backend import models
from backend.schemas.documents import MedicationItem, OrdonnanceData
import backend.services.far_ordonnance_archive_service as service
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256
from backend.services.insurance_template_registry import FAR_2021_1


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


def test_non_far_patient_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        service,
        "load_stored_insurance_source",
        lambda **_: (_ for _ in ()).throw(AssertionError("source store must not be touched")),
    )
    assert service.archive_far_ordonnance_from_source(
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
        service.archive_far_ordonnance_from_source(
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
        service.archive_far_ordonnance_from_source(
            None,
            patient=_patient(),
            source_ordonnance_document=source,
            ordonnance=_ordonnance(),
            uploaded_by_id=7,
        )


def test_far_output_archives_exact_source_link_without_inference(monkeypatch, tmp_path):
    loaded = SimpleNamespace(
        pdf_bytes=b"locked-template-bytes",
        stored=SimpleNamespace(sha256=FAR_2021_1_DERIVED_TEMPLATE_SHA256),
        manifest={
            "kind": "INSURANCE_TEMPLATE",
            "organization": "FAR",
            "trust": FAR_2021_1.trust.value,
            "cabinet_validated_by": "cabinet",
        },
    )
    source_call = {}

    def fake_load(**kwargs):
        source_call.update(kwargs)
        return loaded

    render_call = {}

    def fake_render(**kwargs):
        render_call.update(kwargs)
        return b"rendered-far-pdf"

    archive_call = {}
    far_doc = SimpleNamespace(id=501, file_path="static/archives/12/autre/far.pdf")

    class FakeArchiveService:
        def archive_document(self, **kwargs):
            archive_call.update(kwargs)
            return far_doc, False

    monkeypatch.setattr(service, "load_stored_insurance_source", fake_load)
    monkeypatch.setattr(service, "render_far_prescription_pdf", fake_render)
    monkeypatch.setattr(service, "get_archive_service", lambda db: FakeArchiveService())

    result = service.archive_far_ordonnance_from_source(
        object(),
        patient=_patient(),
        source_ordonnance_document=_source(),
        ordonnance=_ordonnance(),
        uploaded_by_id=7,
        source_store_root=tmp_path,
    )

    assert result is far_doc
    assert source_call == {
        "root": tmp_path,
        "namespace": "template-far",
        "version": FAR_2021_1.version,
        "sha256": FAR_2021_1_DERIVED_TEMPLATE_SHA256,
    }
    assert render_call["template_bytes"] == b"locked-template-bytes"
    assert render_call["patient_full_name"] == "Patient Test"
    assert render_call["payload"].source_ordonnance_document_id == 98
    assert render_call["payload"].lines[0].name == "MEDICAMENT TEST"
    assert render_call["payload"].lines[0].dosage == "500 mg"
    assert render_call["payload"].lines[0].form == "comprime"
    assert render_call["payload"].lines[0].posology == "1 cp matin et soir"
    assert archive_call["clinical_data"]["source_ordonnance_document_id"] == 98
    assert archive_call["clinical_data"]["template_sha256"] == FAR_2021_1_DERIVED_TEMPLATE_SHA256
    assert archive_call["tags"] == ["FAR", "ORDONNANCE", "AUTO_DERIVED"]
    assert archive_call["commit"] is True


def test_far_source_store_sha_is_rechecked(monkeypatch, tmp_path):
    loaded = SimpleNamespace(
        pdf_bytes=b"tampered",
        stored=SimpleNamespace(sha256="0" * 64),
        manifest={
            "kind": "INSURANCE_TEMPLATE",
            "organization": "FAR",
            "trust": FAR_2021_1.trust.value,
            "cabinet_validated_by": "cabinet",
        },
    )
    monkeypatch.setattr(service, "load_stored_insurance_source", lambda **_: loaded)
    with pytest.raises(ValueError, match="stored source SHA-256 mismatch"):
        service.archive_far_ordonnance_from_source(
            object(),
            patient=_patient(),
            source_ordonnance_document=_source(),
            ordonnance=_ordonnance(),
            uploaded_by_id=7,
            source_store_root=tmp_path,
        )
