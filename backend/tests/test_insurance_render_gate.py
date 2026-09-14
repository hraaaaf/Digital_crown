import hashlib
from datetime import date, datetime

import pytest

from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceReferenceSnapshot,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
)
from backend.services.insurance_render_gate import assert_insurance_render_ready


def _validated_draft(template_hash: str, reference_hash: str):
    return InsuranceSubmissionDraft(
        patient_id=1,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[InsuranceSubmissionLine(
            source=InsuranceLineSource(
                honoraires_document_id=42,
                honoraires_line_index=0,
                catalog_act_id=7,
            ),
            service_date=date(2026, 9, 14),
            label="Extraction",
            teeth=["18"],
            amount_mad=700.0,
            mapping_status=InsuranceMappingStatus.EXACT,
            ngap_code="D713",
            ngap_coefficient=10.0,
            mapping_rule_id="arrete-177-06:D713",
        )],
        status=InsuranceDraftStatus.VALIDATED,
        template=InsuranceTemplateSnapshot(
            template_version="CNSS-610-1-04",
            template_hash=template_hash,
            source_url="https://example.invalid/cnss-610-1-04.pdf",
        ),
        reference=InsuranceReferenceSnapshot(
            ngap_reference_version="arrete-177-06",
            ngap_reference_hash=reference_hash,
        ),
        validated_by_practitioner_id=3,
        validated_at=datetime(2026, 9, 14, 19, 0),
    )


def test_renderer_gate_accepts_only_matching_locked_hashes():
    template = b"%PDF-1.4\nlocked-template\n"
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _validated_draft(template_hash, "a" * 64)

    assert assert_insurance_render_ready(
        draft=draft,
        template_bytes=template,
    ) == template_hash


def test_renderer_gate_rejects_template_hash_mismatch():
    draft = _validated_draft("b" * 64, "a" * 64)
    with pytest.raises(ValueError, match="template SHA-256 mismatch"):
        assert_insurance_render_ready(
            draft=draft,
            template_bytes=b"%PDF-1.4\nother-template\n",
        )


def test_renderer_gate_defends_against_unlocked_ngap_reference_even_if_model_was_bypassed():
    template = b"%PDF-1.4\nlocked-template\n"
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _validated_draft(template_hash, "a" * 64).model_copy(update={
        "reference": InsuranceReferenceSnapshot(
            ngap_reference_version="arrete-177-06",
            ngap_reference_hash=None,
        )
    })

    with pytest.raises(ValueError, match="NGAP reference"):
        assert_insurance_render_ready(
            draft=draft,
            template_bytes=template,
        )
