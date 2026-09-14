from datetime import datetime
import hashlib

from backend import models
from backend.schemas.insurance_submission import InsuranceDraftStatus, InsuranceLineSource, InsuranceMappingStatus, InsuranceOrganization, InsuranceSubmissionDraft, InsuranceSubmissionLine, InsuranceTemplateSnapshot
from backend.services.insurance_submission import archive_validated_insurance_pdf


def test_insurance_archive_persists_pdf_snapshot(db, dentiste, tmp_path, monkeypatch):
    from backend.services import archive_service

    monkeypatch.setattr(archive_service, "MEDIA_DIR", tmp_path)
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    monkeypatch.setattr(archive_service, "LEGACY_DOCS_DIR", tmp_path / "documents")

    patient = models.Patient(
        nom="Patient", prenom="Test", date_naissance=datetime(1990, 1, 1),
        sexe="M", employer_id=dentiste.id, assurance="CNSS"
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    draft = InsuranceSubmissionDraft(
        patient_id=patient.id,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[InsuranceSubmissionLine(
            source=InsuranceLineSource(honoraires_document_id=42, honoraires_line_index=0, acte_id=7),
            service_date=datetime(2026, 9, 14).date(), label="Detartrage", teeth=["11", "21"],
            amount_mad=500, mapping_status=InsuranceMappingStatus.EXACT,
            ngap_code="D1", mapping_rule_id="ngap-2026:d1"
        )],
        status=InsuranceDraftStatus.VALIDATED,
        template=InsuranceTemplateSnapshot(template_version="CNSS-610-1-04", template_hash="template-hash"),
        validated_by_practitioner_id=dentiste.id,
        validated_at=datetime(2026, 9, 14, 18, 45),
    )

    pdf = b"%PDF-1.4 insurance-test"
    document, _ = archive_validated_insurance_pdf(
        db, draft=draft, pdf_content=pdf, filename="cnss.pdf", uploaded_by_id=dentiste.id
    )

    assert document.document_type == models.DocumentType.AUTRE
    assert document.patient_id == patient.id
    assert document.file_hash == hashlib.sha256(pdf).hexdigest()
    assert document.clinical_data["kind"] == "INSURANCE_SUBMISSION"
    assert document.clinical_data["organization"] == "CNSS"
    assert document.clinical_data["source_honoraires_document_id"] == 42
    assert "insurance_submission" in document.tags
    assert "cnss" in document.tags
