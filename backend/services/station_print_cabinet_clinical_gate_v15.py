"""LOT04.8-C: authenticated Cabinet-only clinical preflight, no print permit.

Invocation boundary: only after existing FastAPI get_current_user has
authenticated an active Cabinet user and applied the WorkstationModeGate.
The caller MUST resolve the workstation from its secure cookie using
workstation_mode._find_workstation; no browser-provided workstation ID is
accepted. The routine uses the SAME SQLAlchemy Session for the structural
check, locked clinical archive and audited care-sheet state.

Crucial distinction: valid finalization and correct PDF bytes still do not
authorize a physical print. The printer certification registry is absent.
Therefore the result ALWAYS denies and the durable claim/print driver are
never called. There is no Station endpoint here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

from sqlalchemy.orm import Session

from backend import models
from backend.services.station_care_sheet import (
    care_sheet_state, verified_care_sheet_bytes,
)
from backend.services.station_print_cabinet_preflight_v15 import (
    inspect_cabinet_care_sheet_preflight,
)


@dataclass(frozen=True)
class CabinetPrintClinicalGate:
    allowed: bool
    reason: str
    archive_verified: bool = False
    # Intentionally no bytes/path, patient name or print permit in response.


def clinically_recheck_cabinet_print(
    db: Session,
    *,
    authenticated_user: models.User,
    authenticated_workstation: models.WorkstationMode | None,
    session_id: str,
    document_id: int,
    expected_sha256: str,
    now: datetime | None = None,
) -> CabinetPrintClinicalGate:
    """Verify authoritative clinical facts; ALWAYS deny printer activation.

    This is an internal verification helper, not a session/print endpoint.
    Identity inputs come from the authenticated Cabinet dependencies, not
    client-provided actor IDs. The existing ORM Session owns the transaction.
    Exception/IO errors propagate (fail closed). Never calls db.commit().
    """
    def deny(reason: str) -> CabinetPrintClinicalGate:
        return CabinetPrintClinicalGate(False, reason)

    if authenticated_user is None or authenticated_workstation is None:
        return deny("CABINET_AUTH_REQUIRED")
    owner_id = getattr(authenticated_user, "id", None)
    employer_id = getattr(authenticated_user, "employer_id", None)
    workstation_id = getattr(authenticated_workstation, "id", None)
    workstation_tenant = getattr(authenticated_workstation, "employer_id", None)
    if (
        type(owner_id) is not int or owner_id <= 0
        or employer_id is not None
        or workstation_tenant != owner_id
        or type(workstation_id) is not str or not workstation_id
        or getattr(authenticated_workstation, "revoked_at", "missing") is not None
        or getattr(authenticated_workstation, "default_experience", None) != "cabinet"
    ):
        return deny("CABINET_OWNER_WORKSTATION_REQUIRED")

    # PostgreSQL row locks protect from concurrent session purge/document
    # replacement while checking authoritative clinical audit and bytes.
    # SQLite unit tests do not prove PG row-lock behavior; separate PG proof.
    locked_session = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == owner_id,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).with_for_update().first()
    if locked_session is None:
        return deny("SESSION_NOT_AVAILABLE")
    locked_document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_id,
        models.DocumentArchive.patient_id == locked_session.patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.is_latest_version.is_(True),
        models.DocumentArchive.deleted_at.is_(None),
    ).with_for_update().first()
    if locked_document is None:
        return deny("ARCHIVE_NOT_AVAILABLE")

    structural = inspect_cabinet_care_sheet_preflight(
        db.connection(), tenant_id=owner_id,
        actor_user_id=owner_id, actor_employer_id=None,
        cabinet_workstation_id=workstation_id, session_id=session_id,
        document_id=document_id, expected_archive_sha256=expected_sha256,
        now=now if now is not None else datetime.now(timezone.utc),
    )
    if structural.reason != "FINALIZATION_WITHDRAWAL_POLICY_AND_PHYSICAL_PROOF_REQUIRED":
        return deny("STRUCTURAL_" + structural.reason)

    # Call the ACTUAL V1.5-04.3 audit source, not a duplicate boolean flag
    # supplied in a Station request or a user-editable JSON body.
    clinical_state = care_sheet_state(db, locked_document, employer_id=owner_id)
    if not clinical_state.finalized:
        return deny("CARE_SHEET_NOT_FINALIZED")
    if not clinical_state.withdrawal_authorized:
        return deny("WITHDRAWAL_NOT_AUTHORIZED")

    # Re-read immutable bytes from the canonical archive path. The helper
    # rejects symlinks/path traversal, size mismatch and wrong SHA256.
    pdf_bytes = verified_care_sheet_bytes(locked_document)
    if hashlib.sha256(pdf_bytes).hexdigest() != expected_sha256:
        return deny("ARCHIVE_DIGEST_CHANGED")

    # Independent secure release / printer certification has NOT been
    # demonstrated. No ledger claim, no spool, no "completed" status.
    return CabinetPrintClinicalGate(
        allowed=False, reason="TRUSTED_PRINTER_CERTIFICATION_REQUIRED",
        archive_verified=True,
    )
