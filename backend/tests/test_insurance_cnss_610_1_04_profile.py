from dataclasses import replace
from datetime import date, datetime
import hashlib

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
from backend.services.insurance_cnss_610_1_04_profile import (
    CNSS_610_1_04_PROFILE_V1,
    CNSS_610_1_04_PROFILE_VERSION,
    CNSS_610_1_04_TEMPLATE_SHA256,
)
from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayProfile,
    insurance_overlay_profile_payload,
    render_insurance_pdf_overlay,
)


def _synthetic_template() -> bytes:
    document = fitz.open()
    document.new_page(width=1032, height=728)
    document.new_page(width=1032, height=728)
    payload = document.tobytes()
    document.close()
    return payload


def _line(index: int) -> InsuranceSubmissionLine:
    return InsuranceSubmissionLine(
        source=InsuranceLineSource(
            honoraires_document_id=42,
            honoraires_line_index=index,
            acte_id=100 + index,
            catalog_act_id=200 + index,
        ),
        service_date=date(2026, 9, 15),
        label=f"Acte {index}",
        teeth=["11", "21"] if index == 0 else ["36"],
        amount_mad=500.0,
        mapping_status=InsuranceMappingStatus.EXACT,
        ngap_code="D708",
        ngap_coefficient=12.0,
        mapping_rule_id=f"arrete-177-06:D708:{index}",
    )


def _draft(template_hash: str, line_count: int = 1) -> InsuranceSubmissionDraft:
    return InsuranceSubmissionDraft(
        patient_id=1,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[_line(index) for index in range(line_count)],
        administrative=InsuranceAdministrativeSnapshot(
            request_nature=InsuranceRequestNature.EXECUTION,
            insured_full_name="Assure Test",
            insured_registration_number="123456789",
            insured_national_id="AB123456",
            insured_address="Rabat",
            relationship_to_insured="LUI_MEME",
            beneficiary_full_name="Youssef Test",
            beneficiary_birth_date=date(1990, 1, 1),
            beneficiary_national_id="AB123456",
            beneficiary_sex="M",
            practitioner_full_name="Dr Test",
            practitioner_inpe="INPE123456",
            care_type=InsuranceCareType.SOINS,
            attachments_count=2,
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
        validated_at=datetime(2026, 9, 15, 12, 30),
    )


def test_cnss_profile_is_bound_to_exact_cabinet_validated_binary_hash():
    assert CNSS_610_1_04_PROFILE_V1.template_hash == CNSS_610_1_04_TEMPLATE_SHA256
    assert CNSS_610_1_04_TEMPLATE_SHA256 == (
        "e1fb63afb1893886d518135dfb209f24f2464e8cd664e89881fc7c373854864d"
    )
    assert CNSS_610_1_04_PROFILE_V1.profile_version == CNSS_610_1_04_PROFILE_VERSION
    assert CNSS_610_1_04_PROFILE_VERSION == "cnss-610-1-04-e1fb63af-v2"
    assert CNSS_610_1_04_PROFILE_V1.max_lines == 3


def test_cnss_page_1_profile_is_restricted_to_validated_practitioner_zone():
    page_1 = {
        placement.field_key: placement
        for placement in CNSS_610_1_04_PROFILE_V1.placements
        if placement.page_index == 0
    }
    assert set(page_1) == {
        "administrative.beneficiary_full_name",
        "administrative.beneficiary_birth_date",
        "administrative.beneficiary_national_id",
        "choice.beneficiary_sex.M",
        "choice.beneficiary_sex.F",
        "administrative.practitioner_inpe",
        "choice.care_type.SOINS",
        "choice.care_type.PROTHESE",
        "choice.care_type.ORTHODONTIE_FACIALE",
        "choice.care_type.AUTRES",
        "administrative.prior_approval_number",
        "administrative.accident_circumstances",
        "administrative.accident_date",
    }
    assert page_1["administrative.beneficiary_birth_date"].y == 291
    assert page_1["administrative.beneficiary_national_id"].y == 312


def test_overlay_profile_payload_remains_backward_compatible_when_capacity_is_unset():
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="legacy",
        template_hash="a" * 64,
        profile_version="legacy-v1",
        placements=(),
    )
    assert "max_lines" not in insurance_overlay_profile_payload(profile)


def test_cnss_profile_rejects_more_lines_than_the_form_can_display():
    template = _synthetic_template()
    template_hash = hashlib.sha256(template).hexdigest()
    profile = replace(CNSS_610_1_04_PROFILE_V1, template_hash=template_hash)
    draft = _draft(template_hash, line_count=4)

    with pytest.raises(ValueError, match="cannot represent all care lines"):
        render_insurance_pdf_overlay(
            draft=draft,
            template_bytes=template,
            profile=profile,
        )


def test_cnss_profile_renders_one_line_and_leaves_unused_form_rows_blank():
    template = _synthetic_template()
    template_hash = hashlib.sha256(template).hexdigest()
    profile = replace(CNSS_610_1_04_PROFILE_V1, template_hash=template_hash)
    draft = _draft(template_hash, line_count=1)

    rendered = render_insurance_pdf_overlay(
        draft=draft,
        template_bytes=template,
        profile=profile,
    )
    document = fitz.open(stream=rendered, filetype="pdf")
    text = "\n".join(page.get_text("text") for page in document)
    document.close()

    assert "D708" in text
    assert "2026-09-15" in text
    assert text.count("D708") == 1


def test_cnss_profile_renders_only_validated_page_1_zone_without_signature_fields():
    template = _synthetic_template()
    template_hash = hashlib.sha256(template).hexdigest()
    profile = replace(CNSS_610_1_04_PROFILE_V1, template_hash=template_hash)
    draft = _draft(template_hash)

    rendered = render_insurance_pdf_overlay(
        draft=draft,
        template_bytes=template,
        profile=profile,
    )
    document = fitz.open(stream=rendered, filetype="pdf")
    text = "\n".join(page.get_text("text") for page in document)
    document.close()

    assert "Youssef Test" in text
    assert "1990-01-01" in text
    assert "AB123456" in text
    assert "INPE123456" in text
    assert "D708" in text
    assert "Assure Test" not in text
    assert "123456789" not in text
    assert "Rabat" not in text
    assert text.count("X") == 2  # beneficiary sex + care type only
    assert "signature" not in text.lower()
    assert "cachet" not in text.lower()
