import hashlib
from datetime import date, datetime
from types import SimpleNamespace

import fitz
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
    InsuranceTemplateTrust,
)
from backend.services.insurance_finalization import finalize_insurance_submission_pdf
from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayPlacement,
    InsuranceOverlayProfile,
    insurance_overlay_profile_sha256,
)


def _template_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page()
    payload = doc.tobytes()
    doc.close()
    return payload


def _validated_draft(template_hash: str) -> InsuranceSubmissionDraft:
    return InsuranceSubmissionDraft(
        patient_id=1,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[InsuranceSubmissionLine(
            source=InsuranceLineSource(
                honoraires_document_id=42,
                honoraires_line_index=0,
                acte_id=7,
                catalog_act_id=9,
            ),
            service_date=date(2026, 9, 14),
            label="Detartrage",
            teeth=["11"],
            amount_mad=500.0,
            mapping_status=InsuranceMappingStatus.EXACT,
            ngap_code="D1",
            ngap_coefficient=10.0,
            mapping_rule_id="ngap-test:d1",
        )],
        unresolved_fields=[],
        status=InsuranceDraftStatus.VALIDATED,
        template=InsuranceTemplateSnapshot(
            template_version="CNSS-610-1-04",
            template_hash=template_hash,
            source_url="cabinet://validated/CNSS-610-1-04.pdf",
            trust=InsuranceTemplateTrust.CABINET_VALIDATED_BINARY,
        ),
        reference=InsuranceReferenceSnapshot(
            ngap_reference_version="arrete-177-06-test",
            ngap_reference_hash="b" * 64,
        ),
        validated_by_practitioner_id=3,
        validated_at=datetime(2026, 9, 14, 20, 0),
    )


def test_finalization_archives_reproducible_render_evidence(monkeypatch, tmp_path):
    template = _template_bytes()
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _validated_draft(template_hash)
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash=template_hash,
        profile_version="cnss-test-v1",
        placements=(InsuranceOverlayPlacement(
            field_key="computed.total_amount_mad",
            page_index=0,
            x=72,
            y=72,
        ),),
    )

    monkeypatch.setattr(
        "backend.services.insurance_finalization.validate_insurance_draft_by_practitioner",
        lambda *args, **kwargs: draft,
    )
    monkeypatch.setattr(
        "backend.services.insurance_finalization.load_stored_insurance_source",
        lambda *args, **kwargs: SimpleNamespace(pdf_bytes=template),
    )

    captured = {}

    def fake_archive(db, *, draft, pdf_content, filename, uploaded_by_id=None, render_evidence=None):
        captured["evidence"] = render_evidence
        captured["pdf"] = pdf_content
        return SimpleNamespace(file_hash=hashlib.sha256(pdf_content).hexdigest()), False

    monkeypatch.setattr(
        "backend.services.insurance_finalization.archive_validated_insurance_pdf",
        fake_archive,
    )

    document, is_new_version, rendered = finalize_insurance_submission_pdf(
        None,
        draft=draft,
        source_store_root=tmp_path,
        overlay_profile=profile,
        filename="cnss.pdf",
        uploaded_by_id=3,
    )

    assert is_new_version is False
    assert rendered.startswith(b"%PDF")
    assert document.file_hash == hashlib.sha256(rendered).hexdigest()
    evidence = captured["evidence"]
    assert evidence["renderer"] == "PDF_OVERLAY_V1"
    assert evidence["overlay_profile_version"] == "cnss-test-v1"
    assert evidence["overlay_profile_sha256"] == insurance_overlay_profile_sha256(profile)
    assert evidence["overlay_profile"]["placements"][0]["field_key"] == "computed.total_amount_mad"
    assert evidence["rendered_pdf_sha256"] == document.file_hash


def test_finalization_rejects_stale_validated_snapshot(monkeypatch, tmp_path):
    template = _template_bytes()
    template_hash = hashlib.sha256(template).hexdigest()
    draft = _validated_draft(template_hash)
    authoritative = draft.model_copy(update={
        "source_ordonnance_document_id": 999,
    })
    monkeypatch.setattr(
        "backend.services.insurance_finalization.validate_insurance_draft_by_practitioner",
        lambda *args, **kwargs: authoritative,
    )

    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash=template_hash,
        profile_version="cnss-test-v1",
        placements=(),
    )

    with pytest.raises(ValueError, match="stale or altered"):
        finalize_insurance_submission_pdf(
            None,
            draft=draft,
            source_store_root=tmp_path,
            overlay_profile=profile,
            filename="cnss.pdf",
        )


def test_finalization_requires_pdf_filename(tmp_path):
    template = _template_bytes()
    draft = _validated_draft(hashlib.sha256(template).hexdigest())
    profile = InsuranceOverlayProfile(
        organization="CNSS",
        template_version="CNSS-610-1-04",
        template_hash=draft.template.template_hash,
        profile_version="cnss-test-v1",
        placements=(),
    )
    with pytest.raises(ValueError, match="filename must be a PDF"):
        finalize_insurance_submission_pdf(
            None,
            draft=draft,
            source_store_root=tmp_path,
            overlay_profile=profile,
            filename="cnss.txt",
        )
