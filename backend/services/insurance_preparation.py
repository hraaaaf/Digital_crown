"""Prepare an insurance submission draft from one archived Honoraires document.

This service is intentionally renderer-agnostic. Canonical source linkage is delegated
to ``insurance_consistency`` so preparation and final validation use the same rules.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import InsuranceOrganization, InsuranceSubmissionDraft
from backend.services.insurance_administrative import (
    prefill_cnops_administrative,
    prefill_cnss_administrative,
)
from backend.services.insurance_consistency import load_honoraires_insurance_source
from backend.services.insurance_submission import apply_ngap_reference_to_draft, build_draft_from_honoraires_snapshot
from backend.services.insurance_template_registry import (
    CNOPS_DENTAL_CABINET_2026_09_16,
    CNSS_610_1_04,
    FAR_2021_1,
    InsuranceTemplateDefinition,
    LockedInsuranceTemplate,
)

_TEMPLATE_BY_ORGANIZATION = {
    InsuranceOrganization.CNSS: CNSS_610_1_04,
    InsuranceOrganization.CNOPS: CNOPS_DENTAL_CABINET_2026_09_16,
    InsuranceOrganization.FAR: FAR_2021_1,
}


def _template_definition(organization: InsuranceOrganization) -> InsuranceTemplateDefinition:
    try:
        return _TEMPLATE_BY_ORGANIZATION[organization]
    except KeyError as exc:
        raise ValueError("Unsupported insurance organization") from exc


def prepare_insurance_draft_from_honoraires(
    db: Session,
    *,
    honoraires_document_id: int,
    organization: InsuranceOrganization,
    locked_template: LockedInsuranceTemplate | None = None,
    ngap_reference_version: str | None = None,
    on_date: date | None = None,
) -> InsuranceSubmissionDraft:
    """Build a traceable, non-final insurance draft from one archived Honoraires note."""
    source = load_honoraires_insurance_source(db, honoraires_document_id=honoraires_document_id, organization=organization)
    practitioner = db.query(models.User).filter(
        models.User.id == source.practitioner_id,
        models.User.is_active.is_(True),
    ).first()
    if practitioner is None:
        raise ValueError("Honoraires practitioner is unavailable")

    definition = _template_definition(organization)
    if locked_template is not None:
        if locked_template.definition.organization != organization:
            raise ValueError("Locked template organization mismatch")
        if locked_template.definition.version != definition.version:
            raise ValueError("Locked template version mismatch")
        template_hash = locked_template.sha256
        template_source_url = locked_template.source_url
        template_trust = locked_template.definition.trust
    else:
        template_hash = None
        template_source_url = None
        template_trust = None

    draft = build_draft_from_honoraires_snapshot(
        patient_id=source.patient.id,
        organization=organization,
        honoraires_document_id=source.document.id,
        payments=source.payments,
        template_version=definition.version,
        template_hash=template_hash,
        template_source_url=template_source_url,
        template_trust=template_trust,
        active_acte_ids=source.acte_ids,
        fallback_date=(source.document.created_at.date() if source.document.created_at else on_date),
    )

    if organization == InsuranceOrganization.CNSS:
        draft = prefill_cnss_administrative(db, draft=draft, patient=source.patient, practitioner=practitioner)
    elif organization == InsuranceOrganization.CNOPS:
        draft = prefill_cnops_administrative(db, draft=draft, patient=source.patient, practitioner=practitioner)

    if ngap_reference_version:
        draft = apply_ngap_reference_to_draft(db, draft=draft, reference_version=ngap_reference_version, on_date=on_date)
    return draft
