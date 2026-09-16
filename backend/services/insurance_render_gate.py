"""Fail-closed readiness gate shared by future CNSS/CNOPS/FAR PDF renderers."""

from __future__ import annotations

import hashlib

from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceMappingStatus,
    InsuranceSubmissionDraft,
)


def assert_insurance_render_ready(
    *,
    draft: InsuranceSubmissionDraft,
    template_bytes: bytes,
) -> str:
    """Return the verified template SHA-256 or raise before any PDF rendering.

    Final rendering is forbidden unless practitioner validation, a locked template,
    a locked NGAP reference and exact line mappings are all present. This function
    deliberately knows nothing about layout coordinates.
    """
    if draft.status != InsuranceDraftStatus.VALIDATED:
        raise ValueError("Insurance rendering requires a VALIDATED draft")

    if not template_bytes or not template_bytes.startswith(b"%PDF"):
        raise ValueError("Insurance rendering requires PDF template bytes")

    expected_template_hash = str(draft.template.template_hash or "").lower()
    if len(expected_template_hash) != 64:
        raise ValueError("Insurance template SHA-256 is not locked")

    actual_template_hash = hashlib.sha256(template_bytes).hexdigest()
    if actual_template_hash != expected_template_hash:
        raise ValueError("Insurance template SHA-256 mismatch")

    reference_hash = str(draft.reference.ngap_reference_hash or "").lower()
    if not draft.reference.ngap_reference_version or len(reference_hash) != 64:
        raise ValueError("NGAP reference version/SHA-256 is not locked")

    if any(line.mapping_status != InsuranceMappingStatus.EXACT for line in draft.lines):
        raise ValueError("Insurance rendering requires EXACT NGAP mapping for every line")

    if any(not line.ngap_code or not line.mapping_rule_id for line in draft.lines):
        raise ValueError("Insurance rendering requires traceable NGAP code/rule per line")

    return actual_template_hash
