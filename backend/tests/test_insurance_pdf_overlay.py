import hashlib
from datetime import date, datetime

import fitz
import pytest

from backend.schemas.insurance_submission import (
    InsuranceAdministrativeSnapshot,
    InsuranceCareType,
    InsuranceDraftStatus,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceReferenceSnapshot,
    InsuranceRequestNature,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
    InsuranceTemplateTrust,
)
from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayPlacement,
    InsuranceOverlayProfile,
    OverlayKind,
    render_insurance_pdf_overlay,
)


def _template() -> bytes:
    document = fitz.open()
    document.new_page()
    document.new_page()
    payload = document.tobytes()
    document.close()
    return payload


def _draft(template_hash):
    return InsuranceSubmissionDraft(
        patient_id=1,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[InsuranceSubmissionLine(
            source=InsuranceLineSource(
                honoraires_document_id=42,
                honoraires_line_index=0,
                acte_id=7,
                catalog_act_id=8,
            ),
            service_date=date(2026, 9, 14),
            label="Detartrage",
            teeth=["11", "21"],
            amount_mad=500.0,
            mapping_status=InsuranceMappingStatus.EXACT,
            ngap_code="D1",
            ngap_coefficient=10.0,
            mapping_rule_id="arrete-177-06:D1",
        )],
        administrative=InsuranceAdministrativeSnapshot(
            request_nature=InsuranceRequestNature.EXECUTION,
            insured_full_name="Assure Test",
            insured_registration_number="123456",
            insured_national_id="AB123456",
            insured_address="Rabat",
            relationship_to_insured="LUI_MEME",
            beneficiary_full_name="Youssef Test",
            beneficiary_birth_date=date(1990, 1, 1),
            beneficiary_national_id="AB123456",
            beneficiary_sex="M",
            practitioner_full_name="Dr Test",
            practitioner_inpe="INPE123",
            care_type=InsuranceCareType.SOINS,
            attachments_count=0,
        ),
        status=InsuranceDraftStatus.VALIDATED,
        template=InsuranceTemplateSnapshot(
            template_version="CNSS-610-1-04",
            template_hash=template_hash,
            source_url="cabinet://validated/CNSS-610-1-04.pdf",
            trust=InsuranceTemplateTrust.CABINET_VALIDATED_BINARY,
        ),
        reference=InsuranceReferenceSnapshot(
            ngap_reference_version="arrete-177-06",
            ngap_reference_hash="a" * 64,
        ),
        validated_by_practitioner_id=3,
        validated_at=datetime(2026, 9, 14, 20, 30),
    )


def test_overlay_renders_only_profile_fields_on_locked_template():
    template = _template()
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _draft(template_hash)
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash=template_hash,
        profile_version="synthetic-v1",
        placements=(
            InsuranceOverlayPlacement("administrative.beneficiary_full_name", 0, 72, 72),
            InsuranceOverlayPlacement("administrative.practitioner_inpe", 0, 72, 92),
            InsuranceOverlayPlacement("choice.care_type.SOINS", 0, 72, 112, kind=OverlayKind.MARK),
            InsuranceOverlayPlacement("lines[0].ngap_code", 0, 72, 132),
            InsuranceOverlayPlacement("computed.total_amount_mad", 0, 72, 152),
        ),
    )

    rendered = render_insurance_pdf_overlay(
        draft=draft,
        template_bytes=template,
        profile=profile,
    )
    document = fitz.open(stream=rendered, filetype="pdf")
    text = document[0].get_text("text")
    document.close()
    assert "Youssef Test" in text
    assert "INPE123" in text
    assert "D1" in text
    assert "500" in text
    assert "X" in text


def test_overlay_rejects_profile_bound_to_other_template_hash():
    template = _template()
    draft = _draft(hashlib.sha256(template).hexdigest())
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash="b" * 64,
        profile_version="wrong-hash",
        placements=(),
    )
    with pytest.raises(ValueError, match="profile template SHA-256 mismatch"):
        render_insurance_pdf_overlay(
            draft=draft,
            template_bytes=template,
            profile=profile,
        )


def test_overlay_forbids_signature_or_stamp_fields():
    template = _template()
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _draft(template_hash)
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash=template_hash,
        profile_version="forbidden-field",
        placements=(
            InsuranceOverlayPlacement("administrative.signature_praticien", 0, 72, 72),
        ),
    )
    with pytest.raises(ValueError, match="forbidden"):
        render_insurance_pdf_overlay(
            draft=draft,
            template_bytes=template,
            profile=profile,
        )
