from datetime import date, datetime

import pytest

from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
)
from backend.services.insurance_submission import (
    build_insurance_archive_clinical_data,
    build_insurance_archive_tags,
)


def _line(mapping_status=InsuranceMappingStatus.NOT_EVALUATED, **overrides):
    values = {
        "source": InsuranceLineSource(
            honoraires_document_id=42,
            honoraires_line_index=0,
            acte_id=7,
        ),
        "service_date": date(2026, 9, 14),
        "label": "Detartrage",
        "teeth": ["11", "21"],
        "amount_mad": 500,
        "mapping_status": mapping_status,
    }
    values.update(overrides)
    return InsuranceSubmissionLine(**values)


def _draft(**overrides):
    values = {
        "patient_id": 12,
        "organization": InsuranceOrganization.CNSS,
        "honoraires_document_id": 42,
        "lines": [_line()],
        "template": InsuranceTemplateSnapshot(
            template_version="CNSS-610-1-04",
            template_hash="abc123",
            source_url="https://example.invalid/cnss.pdf",
        ),
    }
    values.update(overrides)
    return InsuranceSubmissionDraft(**values)


def test_exact_mapping_requires_code_and_rule():
    with pytest.raises(ValueError, match="ngap_code"):
        _line(mapping_status=InsuranceMappingStatus.EXACT)

    with pytest.raises(ValueError, match="mapping_rule_id"):
        _line(
            mapping_status=InsuranceMappingStatus.EXACT,
            ngap_code="D1",
        )

    line = _line(
        mapping_status=InsuranceMappingStatus.EXACT,
        ngap_code="D1",
        mapping_rule_id="ngap-2026:d1",
    )
    assert line.ngap_code == "D1"


def test_non_exact_mapping_cannot_carry_ngap_code():
    with pytest.raises(ValueError, match="only for EXACT"):
        _line(
            mapping_status=InsuranceMappingStatus.AMBIGUOUS,
            ngap_code="D1",
        )


def test_ready_for_review_fails_closed_on_unresolved_fields():
    with pytest.raises(ValueError, match="READY_FOR_REVIEW"):
        _draft(
            status=InsuranceDraftStatus.READY_FOR_REVIEW,
            unresolved_fields=["insured.registration_number"],
        )


def test_ready_for_review_fails_closed_on_ambiguous_mapping():
    with pytest.raises(ValueError, match="blocking mappings"):
        _draft(
            status=InsuranceDraftStatus.READY_FOR_REVIEW,
            lines=[_line(mapping_status=InsuranceMappingStatus.AMBIGUOUS)],
        )


def test_validated_requires_practitioner_and_timestamp():
    exact = _line(
        mapping_status=InsuranceMappingStatus.EXACT,
        ngap_code="D1",
        mapping_rule_id="ngap-2026:d1",
    )
    with pytest.raises(ValueError, match="practitioner"):
        _draft(status=InsuranceDraftStatus.VALIDATED, lines=[exact])

    draft = _draft(
        status=InsuranceDraftStatus.VALIDATED,
        lines=[exact],
        validated_by_practitioner_id=3,
        validated_at=datetime(2026, 9, 14, 18, 45),
    )
    assert draft.status == InsuranceDraftStatus.VALIDATED


def test_archive_snapshot_preserves_provenance_and_tags():
    draft = _draft()
    snapshot = build_insurance_archive_clinical_data(draft)

    assert snapshot["kind"] == "INSURANCE_SUBMISSION"
    assert snapshot["organization"] == "CNSS"
    assert snapshot["source_honoraires_document_id"] == 42
    assert snapshot["template_version"] == "CNSS-610-1-04"
    assert snapshot["draft"]["lines"][0]["teeth"] == ["11", "21"]
    assert build_insurance_archive_tags(draft) == [
        "insurance_submission",
        "cnss",
        "template:CNSS-610-1-04",
    ]
