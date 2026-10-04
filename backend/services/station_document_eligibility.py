from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from backend import models

# V1.5-04.1 is intentionally fail-closed. A document type being technically
# downloadable in the cabinet application never makes it station-eligible.
SELF_SERVICE_ALLOWED_TYPES: Final[frozenset[models.DocumentType]] = frozenset({
    models.DocumentType.CERTIFICAT,
    models.DocumentType.AUTRE,
})

SELF_SERVICE_MARKER = "station_self_service"
SELF_SERVICE_KIND_ATTENDANCE = "attendance_certificate"
SELF_SERVICE_KIND_CARE_SHEET = "care_sheet"
SELF_SERVICE_ALLOWED_KINDS: Final[frozenset[str]] = frozenset({
    SELF_SERVICE_KIND_ATTENDANCE,
    SELF_SERVICE_KIND_CARE_SHEET,
})


@dataclass(frozen=True)
class StationDocumentEligibility:
    eligible: bool
    kind: str | None = None
    reason: str | None = None


def station_document_eligibility(
    document: models.DocumentArchive,
    *,
    patient_id: int,
) -> StationDocumentEligibility:
    """Return station self-service eligibility without mutating state.

    Contract:
    - patient ownership must match the already-identified station patient;
    - only active/latest documents can be exposed;
    - the document type must be explicitly whitelisted;
    - legacy documents are denied unless their clinical_data carries the
      explicit station_self_service marker written by a trusted workflow;
    - unknown kinds/markers fail closed.
    """
    if int(document.patient_id) != int(patient_id):
        return StationDocumentEligibility(False, reason="PATIENT_MISMATCH")
    if document.status != models.DocumentStatus.ACTIF or document.deleted_at is not None:
        return StationDocumentEligibility(False, reason="DOCUMENT_NOT_ACTIVE")
    if not bool(document.is_latest_version):
        return StationDocumentEligibility(False, reason="DOCUMENT_NOT_LATEST")
    if document.document_type not in SELF_SERVICE_ALLOWED_TYPES:
        return StationDocumentEligibility(False, reason="DOCUMENT_TYPE_NOT_ALLOWED")

    metadata = document.clinical_data if isinstance(document.clinical_data, dict) else {}
    marker = metadata.get(SELF_SERVICE_MARKER)
    if not isinstance(marker, dict) or marker.get("eligible") is not True:
        return StationDocumentEligibility(False, reason="EXPLICIT_ELIGIBILITY_REQUIRED")

    kind = marker.get("kind")
    if kind not in SELF_SERVICE_ALLOWED_KINDS:
        return StationDocumentEligibility(False, reason="DOCUMENT_KIND_NOT_ALLOWED")

    # 04.1 only evaluates the explicit eligibility contract. 04.2/04.3 own
    # the stronger evidence/finalization checks for each document kind.
    return StationDocumentEligibility(True, kind=kind)
