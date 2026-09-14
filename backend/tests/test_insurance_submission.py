from datetime import date, datetime

import pytest

from backend.schemas.insurance_submission import (
    InsuranceDraftStatus, InsuranceLineSource, InsuranceMappingStatus,
    InsuranceOrganization, InsuranceSubmissionDraft, InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
)
from backend.services.insurance_submission import (
    archive_validated_insurance_pdf, build_draft_from_honoraires_snapshot,
    build_insurance_archive_clinical_data, build_insurance_archive_tags,
)


def _line(mapping_status=InsuranceMappingStatus.NOT_EVALUATED, **overrides):
    values = {
        "source": InsuranceLineSource(honoraires_document_id=42, honoraires_line_index=0, acte_id=7),
        "service_date": date(2026, 9, 14), "label": "Detartrage", "teeth": ["11", "21"],
        "amount_mad": 500, "mapping_status": mapping_status,
    }
    values.update(overrides)
    return InsuranceSubmissionLine(**values)


def _exact_line(**overrides):
    return _line(mapping_status=InsuranceMappingStatus.EXACT, ngap_code="D1",
        mapping_rule_id="ngap-2026:d1", **overrides)


def _draft(**overrides):
    values = {
        "patient_id": 12, "organization": InsuranceOrganization.CNSS,
        "honoraires_document_id": 42, "lines": [_line()],
        "template": InsuranceTemplateSnapshot(template_version="CNSS-610-1-04",
            template_hash="abc123", source_url="https://example.invalid/cnss.pdf"),
    }
    values.update(overrides)
    return InsuranceSubmissionDraft(**values)


def test_exact_mapping_requires_code_and_rule():
    with pytest.raises(ValueError, match="ngap_code"):
        _line(mapping_status=InsuranceMappingStatus.EXACT)
    with pytest.raises(ValueError, match="mapping_rule_id"):
        _line(mapping_status=InsuranceMappingStatus.EXACT, ngap_code="D1")
    assert _exact_line().ngap_code == "D1"


def test_non_exact_mapping_cannot_carry_ngap_code():
    with pytest.raises(ValueError, match="only for EXACT"):
        _line(mapping_status=InsuranceMappingStatus.AMBIGUOUS, ngap_code="D1")


def test_ready_for_review_requires_exact_mapping_and_no_missing_fields():
    with pytest.raises(ValueError, match="READY_FOR_REVIEW"):
        _draft(status=InsuranceDraftStatus.READY_FOR_REVIEW)
    with pytest.raises(ValueError, match="READY_FOR_REVIEW"):
        _draft(status=InsuranceDraftStatus.READY_FOR_REVIEW, lines=[_exact_line()],
            unresolved_fields=["insured.registration_number"])
    assert _draft(status=InsuranceDraftStatus.READY_FOR_REVIEW, lines=[_exact_line()]).status == InsuranceDraftStatus.READY_FOR_REVIEW


def test_validated_requires_practitioner_and_timestamp():
    with pytest.raises(ValueError, match="practitioner"):
        _draft(status=InsuranceDraftStatus.VALIDATED, lines=[_exact_line()])
    draft = _draft(status=InsuranceDraftStatus.VALIDATED, lines=[_exact_line()],
        validated_by_practitioner_id=3, validated_at=datetime(2026, 9, 14, 18, 45))
    assert draft.status == InsuranceDraftStatus.VALIDATED


def test_honoraires_adapter_reads_teeth_and_aligns_actes():
    draft = build_draft_from_honoraires_snapshot(
        patient_id=12, organization=InsuranceOrganization.CNSS, honoraires_document_id=42,
        payments=[
            {"date": "2026-09-13", "acte": "Detartrage", "dents": [11, 21], "montant": 500},
            {"date": "2026-09-14T10:00:00", "acte": "Extraction", "dent": "18", "montant": "700"},
        ], active_acte_ids=[70, 71], template_version="CNSS-610-1-04")
    assert draft.status == InsuranceDraftStatus.INCOMPLETE
    assert draft.lines[0].teeth == ["11", "21"]
    assert draft.lines[0].source.acte_id == 70
    assert draft.lines[1].teeth == ["18"]
    assert draft.lines[1].service_date == date(2026, 9, 14)


def test_historical_line_count_mismatch_fails_closed():
    with pytest.raises(ValueError, match="line count mismatch"):
        build_draft_from_honoraires_snapshot(
            patient_id=12, organization=InsuranceOrganization.CNSS, honoraires_document_id=42,
            payments=[{"acte": "Detartrage", "montant": 500}], active_acte_ids=[70, 71],
            template_version="CNSS-610-1-04")


def test_archive_snapshot_preserves_provenance_and_tags():
    draft = _draft()
    snapshot = build_insurance_archive_clinical_data(draft)
    assert snapshot["kind"] == "INSURANCE_SUBMISSION"
    assert snapshot["organization"] == "CNSS"
    assert snapshot["source_honoraires_document_id"] == 42
    assert snapshot["template_version"] == "CNSS-610-1-04"
    assert snapshot["draft"]["lines"][0]["teeth"] == ["11", "21"]
    assert build_insurance_archive_tags(draft) == ["insurance_submission", "cnss", "template:CNSS-610-1-04"]


def test_archive_rejects_unvalidated_draft_before_db():
    with pytest.raises(ValueError, match="VALIDATED"):
        archive_validated_insurance_pdf(None, draft=_draft(), pdf_content=b"%PDF-1.4\n", filename="cnss.pdf")


def test_archive_rejects_non_pdf_before_db():
    validated = _draft(status=InsuranceDraftStatus.VALIDATED, lines=[_exact_line()],
        validated_by_practitioner_id=3, validated_at=datetime(2026, 9, 14, 18, 45))
    with pytest.raises(ValueError, match="PDF content"):
        archive_validated_insurance_pdf(None, draft=validated, pdf_content=b"not a pdf", filename="cnss.pdf")
