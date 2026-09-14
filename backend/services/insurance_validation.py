"""Server-side practitioner validation gate for insurance submission drafts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
    InsuranceTemplateTrust,
)
from backend.services.insurance_administrative import missing_cnss_administrative_fields
from backend.services.insurance_consistency import assert_draft_matches_honoraires_source
from backend.services.insurance_source_store import load_stored_insurance_source
from backend.services.insurance_submission import apply_ngap_reference_to_draft


def _assert_template_source(
    *,
    source_store_root: Path,
    draft: InsuranceSubmissionDraft,
) -> None:
    if not draft.template.template_hash:
        raise ValueError("Insurance template is not SHA-256 locked")
    loaded = load_stored_insurance_source(
        root=source_store_root,
        namespace=f"template-{draft.organization.value.lower()}",
        version=draft.template.template_version,
        sha256=draft.template.template_hash,
    )
    manifest = loaded.manifest
    expected = {
        "kind": "INSURANCE_TEMPLATE",
        "organization": draft.organization.value,
        "source_url": draft.template.source_url,
        "trust": draft.template.trust.value if draft.template.trust else None,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Insurance template manifest {key} mismatch")
    if draft.template.trust not in {
        InsuranceTemplateTrust.OFFICIAL_PRIMARY,
        InsuranceTemplateTrust.CABINET_VALIDATED_BINARY,
    }:
        raise ValueError("Insurance template trust is insufficient for practitioner validation")
    if (
        draft.template.trust == InsuranceTemplateTrust.CABINET_VALIDATED_BINARY
        and not str(manifest.get("cabinet_validated_by") or "").strip()
    ):
        raise ValueError("Cabinet-validated template has no validator identity")


def _assert_ngap_source(
    *,
    source_store_root: Path,
    draft: InsuranceSubmissionDraft,
) -> None:
    version = str(draft.reference.ngap_reference_version or "").strip()
    source_hash = str(draft.reference.ngap_reference_hash or "").strip()
    if not version or len(source_hash) != 64:
        raise ValueError("NGAP reference is not locked")
    loaded = load_stored_insurance_source(
        root=source_store_root,
        namespace="ngap",
        version=version,
        sha256=source_hash,
    )
    manifest = loaded.manifest
    if manifest.get("kind") != "NGAP_PRIMARY":
        raise ValueError("NGAP stored source kind mismatch")
    if manifest.get("status") != "VERIFIED_PRIMARY":
        raise ValueError("NGAP stored source is not VERIFIED_PRIMARY")


def validate_insurance_draft_by_practitioner(
    db: Session,
    *,
    draft: InsuranceSubmissionDraft,
    practitioner_id: int,
    source_store_root: Path,
    validated_at: datetime | None = None,
) -> InsuranceSubmissionDraft:
    """Rebuild all authoritative gates and return a newly validated immutable snapshot.

    Client-provided clinical/financial fields, NGAP statuses, unresolved flags and source
    trust are not accepted as authority. The function rechecks them against DB/store.
    """
    source = assert_draft_matches_honoraires_source(db, draft=draft)
    if int(practitioner_id) != int(source.practitioner_id):
        raise ValueError("Only the source Honoraires practitioner can validate this submission")
    practitioner = db.query(models.User).filter(
        models.User.id == int(practitioner_id),
        models.User.is_active.is_(True),
    ).first()
    if practitioner is None:
        raise ValueError("Validation practitioner is unavailable")

    reference_version = str(draft.reference.ngap_reference_version or "").strip()
    if not reference_version:
        raise ValueError("NGAP reference version is required before practitioner validation")

    # Re-resolve NGAP from server mappings. Any client mapping manipulation disappears.
    resolved = apply_ngap_reference_to_draft(
        db,
        draft=draft,
        reference_version=reference_version,
    )

    # Administrative completeness is recomputed independently of client unresolved flags.
    if draft.organization == InsuranceOrganization.CNSS:
        administrative_missing = missing_cnss_administrative_fields(draft.administrative)
    else:
        raise ValueError("Administrative validation policy is not yet implemented for this insurer")

    # Preserve server-resolved NGAP blockers and rebuild administrative blockers.
    unresolved = [
        value for value in resolved.unresolved_fields
        if not value.startswith("administrative.")
    ]
    unresolved.extend(administrative_missing)
    resolved = resolved.model_copy(update={
        "administrative": draft.administrative,
        "unresolved_fields": unresolved,
        "status": InsuranceDraftStatus.INCOMPLETE,
        "template": draft.template,
    })

    if unresolved:
        raise ValueError("Insurance submission still has unresolved required fields")
    if any(line.mapping_status.value != "EXACT" for line in resolved.lines):
        raise ValueError("Insurance submission contains unresolved NGAP mappings")

    _assert_template_source(source_store_root=Path(source_store_root), draft=resolved)
    _assert_ngap_source(source_store_root=Path(source_store_root), draft=resolved)

    payload = resolved.model_dump()
    payload.update({
        "status": InsuranceDraftStatus.VALIDATED,
        "validated_by_practitioner_id": int(practitioner_id),
        "validated_at": validated_at or datetime.now(),
        "unresolved_fields": [],
    })
    return InsuranceSubmissionDraft.model_validate(payload)
