"""Final insurance rendering + archival gate.

This is the last backend step before an insurer PDF becomes a patient archive document.
It revalidates the already validated draft against authoritative DB/store state, rejects
stale or client-altered snapshots, renders against the exact immutable template and
archives the final PDF with reproducible overlay evidence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from backend.schemas.insurance_submission import InsuranceDraftStatus, InsuranceSubmissionDraft
from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayProfile,
    insurance_overlay_profile_payload,
    insurance_overlay_profile_sha256,
    render_insurance_pdf_overlay,
)
from backend.services.insurance_source_store import load_stored_insurance_source
from backend.services.insurance_submission import archive_validated_insurance_pdf
from backend.services.insurance_validation import validate_insurance_draft_by_practitioner


def _canonical_draft_payload(draft: InsuranceSubmissionDraft) -> dict:
    return draft.model_dump(mode="json")


def finalize_insurance_submission_pdf(
    db: Session,
    *,
    draft: InsuranceSubmissionDraft,
    source_store_root: Path,
    overlay_profile: InsuranceOverlayProfile,
    filename: str,
    uploaded_by_id: int | None = None,
):
    """Revalidate, render and archive one insurance PDF atomically at the service level.

    A draft validated earlier is not trusted blindly. The clinical/financial source,
    NGAP mappings and immutable source manifests are checked again immediately before
    rendering. If the reconstructed authoritative snapshot differs, finalization stops.
    """
    if draft.status != InsuranceDraftStatus.VALIDATED:
        raise ValueError("Insurance finalization requires a VALIDATED draft")
    practitioner_id = draft.validated_by_practitioner_id
    if practitioner_id is None or draft.validated_at is None:
        raise ValueError("Insurance finalization requires practitioner validation provenance")
    if not str(filename or "").strip().lower().endswith(".pdf"):
        raise ValueError("Insurance finalization filename must be a PDF")

    root = Path(source_store_root)
    authoritative = validate_insurance_draft_by_practitioner(
        db,
        draft=draft,
        practitioner_id=int(practitioner_id),
        source_store_root=root,
        validated_at=draft.validated_at,
    )
    if _canonical_draft_payload(authoritative) != _canonical_draft_payload(draft):
        raise ValueError("Validated insurance draft is stale or altered; review is required again")

    template_hash = str(draft.template.template_hash or "")
    loaded_template = load_stored_insurance_source(
        root=root,
        namespace=f"template-{draft.organization.value.lower()}",
        version=draft.template.template_version,
        sha256=template_hash,
    )

    rendered_pdf = render_insurance_pdf_overlay(
        draft=authoritative,
        template_bytes=loaded_template.pdf_bytes,
        profile=overlay_profile,
    )
    rendered_hash = hashlib.sha256(rendered_pdf).hexdigest()
    profile_hash = insurance_overlay_profile_sha256(overlay_profile)
    render_evidence = {
        "renderer": "PDF_OVERLAY_V1",
        "overlay_profile_version": overlay_profile.profile_version,
        "overlay_profile_sha256": profile_hash,
        "overlay_profile": insurance_overlay_profile_payload(overlay_profile),
        "template_sha256": template_hash,
        "rendered_pdf_sha256": rendered_hash,
    }

    document, is_new_version = archive_validated_insurance_pdf(
        db,
        draft=authoritative,
        pdf_content=rendered_pdf,
        filename=filename,
        uploaded_by_id=uploaded_by_id,
        render_evidence=render_evidence,
    )
    if document.file_hash != rendered_hash:
        raise RuntimeError("Archived insurance PDF hash does not match rendered bytes")
    return document, is_new_version, rendered_pdf
