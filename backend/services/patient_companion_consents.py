from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionConsentEvidence,
    PatientCompanionConsentRequest,
    PatientCompanionShareGrant,
)
from backend.services.document_signature_p3 import verify_document_integrity
from backend.services.patient_companion_remote_worker import RemoteDomainResult
from backend.services.patient_signature_png import validate_patient_signature_png


def effective_consent_state(row: PatientCompanionConsentRequest, *, now: datetime | None = None) -> str:
    now = now or datetime.utcnow()
    if row.revoked_at is not None or row.status == "REVOKED":
        return "REVOKED"
    if row.status == "SIGNED":
        return "SIGNED"
    if row.expires_at is not None and row.expires_at <= now:
        return "EXPIRED"
    return "PENDING"


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def handle_consent_sign(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    consent_id = payload.get("consent_id")
    signature_base64 = payload.get("signature_base64")
    if not isinstance(consent_id, str) or len(consent_id) != 36:
        return _reject("INVALID_CONSENT")
    if not isinstance(signature_base64, str):
        return _reject("INVALID_SIGNATURE")

    request = (
        db.query(PatientCompanionConsentRequest)
        .filter(
            PatientCompanionConsentRequest.public_id == consent_id,
            PatientCompanionConsentRequest.employer_id == access.employer_id,
            PatientCompanionConsentRequest.patient_id == access.patient_id,
        )
        .with_for_update()
        .first()
    )
    if request is None:
        return _reject("CONSENT_NOT_FOUND")

    state = effective_consent_state(request)
    if state == "SIGNED":
        return _reject("ALREADY_SIGNED")
    if state == "REVOKED":
        return _reject("CONSENT_REVOKED")
    if state == "EXPIRED":
        return _reject("CONSENT_EXPIRED")

    share = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.id == request.share_grant_id,
        PatientCompanionShareGrant.employer_id == access.employer_id,
        PatientCompanionShareGrant.patient_id == access.patient_id,
        PatientCompanionShareGrant.resource_type == "document",
        PatientCompanionShareGrant.resource_id == request.document_id,
        PatientCompanionShareGrant.revoked_at.is_(None),
    ).first()
    if share is None:
        return _reject("DOCUMENT_NOT_SHARED")

    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == request.document_id,
        models.DocumentArchive.patient_id == access.patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).first()
    if document is None:
        return _reject("DOCUMENT_UNAVAILABLE")

    if (
        str(document.document_group_id) != str(request.document_group_id)
        or int(document.version_number) != int(request.document_version)
        or str(document.file_hash) != str(request.document_file_hash)
        or int(document.file_size) != int(request.document_file_size)
    ):
        return _reject("DOCUMENT_VERSION_CHANGED")

    integrity_ok, _reason = verify_document_integrity(document)
    if not integrity_ok:
        return _reject("DOCUMENT_INTEGRITY_FAILED")

    if db.query(PatientCompanionConsentEvidence).filter(
        PatientCompanionConsentEvidence.consent_request_id == request.id,
    ).first() is not None:
        return _reject("ALREADY_SIGNED")

    signature_png = validate_patient_signature_png(signature_base64)
    signed_at = datetime.utcnow()
    evidence = PatientCompanionConsentEvidence(
        consent_request_id=request.id,
        access_id=access.id,
        employer_id=access.employer_id,
        patient_id=access.patient_id,
        signature_png=signature_png,
        signature_sha256=hashlib.sha256(signature_png).hexdigest(),
        signature_size=len(signature_png),
        signed_at=signed_at,
    )
    db.add(evidence)
    request.status = "SIGNED"
    db.flush()

    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "CONSENT_SIGNED",
            "consent_id": request.public_id,
            "evidence_ref": evidence.public_id,
            "status": "SIGNED",
            "signed_at": signed_at.isoformat(),
            "qualified_electronic_signature": False,
        },
    )


PC04_REMOTE_HANDLERS = {
    "consent.sign": handle_consent_sign,
}
