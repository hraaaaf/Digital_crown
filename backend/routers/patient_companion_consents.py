from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionConsentEvidence,
    PatientCompanionConsentRequest,
    PatientCompanionIdentity,
    PatientCompanionRemoteKeyset,
    PatientCompanionShareGrant,
)
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
    staff_patient_or_404,
)
from backend.services.audit_service import audit_service
from backend.services.document_signature_p3 import resolve_document_storage_path, verify_document_integrity
from backend.services.patient_companion_consents import effective_consent_state
from backend.services.patient_companion_remote_worker import process_remote_envelope
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class ConsentCreateRequest(BaseModel):
    document_id: int = Field(gt=0)
    expires_at: Optional[datetime] = None


class RemoteCommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob: str = Field(min_length=16, max_length=256 * 1024)


@router.post("/admin/patients/{patient_id}/consents", status_code=201)
def create_patient_consent(
    patient_id: int,
    body: ConsentCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    expires_at = body.expires_at
    if expires_at is not None and expires_at.tzinfo is not None:
        expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    if expires_at is not None and expires_at <= datetime.utcnow():
        raise HTTPException(status_code=422, detail="Expiration du consentement invalide.")

    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == body.document_id,
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")

    from backend.routers.documents import require_document_permission
    doc_type = getattr(document.document_type, "value", document.document_type)
    require_document_permission(str(doc_type), current_user)

    document_path = resolve_document_storage_path(document)
    try:
        if not document_path.is_file() or document_path.read_bytes()[:5] != b"%PDF-":
            raise HTTPException(status_code=409, detail="Seuls les documents PDF sont éligibles au Consent Vault.")
    except OSError:
        raise HTTPException(status_code=409, detail="Document PDF indisponible.") from None

    share = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.employer_id == employer_id,
        PatientCompanionShareGrant.patient_id == patient.id,
        PatientCompanionShareGrant.resource_type == "document",
        PatientCompanionShareGrant.resource_id == document.id,
        PatientCompanionShareGrant.revoked_at.is_(None),
    ).first()
    if share is None:
        raise HTTPException(
            status_code=409,
            detail="Le document doit d'abord être explicitement partagé avec le Patient Companion.",
        )

    integrity_ok, integrity_reason = verify_document_integrity(document)
    if not integrity_ok:
        raise HTTPException(
            status_code=409,
            detail=f"Document non signable : {integrity_reason}",
        )

    existing = db.query(PatientCompanionConsentRequest).filter(
        PatientCompanionConsentRequest.employer_id == employer_id,
        PatientCompanionConsentRequest.patient_id == patient.id,
        PatientCompanionConsentRequest.document_id == document.id,
        PatientCompanionConsentRequest.document_file_hash == document.file_hash,
    ).first()
    if existing is not None:
        if effective_consent_state(existing) == "SIGNED":
            return {
                "consent_id": existing.public_id,
                "status": "SIGNED",
                "document_version": existing.document_version,
            }
        existing.revoked_at = None
        existing.status = "PENDING"
        existing.expires_at = expires_at
        existing.share_grant_id = share.id
        existing.created_by_user_id = current_user.id
        db.commit()
        return {
            "consent_id": existing.public_id,
            "status": effective_consent_state(existing),
            "document_version": existing.document_version,
        }

    consent = PatientCompanionConsentRequest(
        employer_id=employer_id,
        patient_id=patient.id,
        document_id=document.id,
        share_grant_id=share.id,
        document_group_id=str(document.document_group_id),
        document_version=int(document.version_number),
        document_file_hash=str(document.file_hash),
        document_file_size=int(document.file_size),
        created_by_user_id=current_user.id,
        status="PENDING",
        expires_at=expires_at,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_CONSENT_ISSUED",
        resource_type="Document",
        resource_id=str(document.id),
        details=f"version={document.version_number}; sha256={document.file_hash}",
    )
    return {
        "consent_id": consent.public_id,
        "status": "PENDING",
        "document_version": consent.document_version,
    }


@router.delete("/admin/patients/{patient_id}/consents/{consent_id}")
def revoke_patient_consent(
    patient_id: int,
    consent_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    row = db.query(PatientCompanionConsentRequest).filter(
        PatientCompanionConsentRequest.public_id == consent_id,
        PatientCompanionConsentRequest.employer_id == employer_id,
        PatientCompanionConsentRequest.patient_id == patient.id,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Consentement introuvable.")

    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == row.document_id,
        models.DocumentArchive.patient_id == patient.id,
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    from backend.routers.documents import require_document_permission
    doc_type = getattr(document.document_type, "value", document.document_type)
    require_document_permission(str(doc_type), current_user)

    if effective_consent_state(row) == "SIGNED":
        raise HTTPException(status_code=409, detail="Une preuve signée ne peut pas être révoquée silencieusement.")
    row.status = "REVOKED"
    row.revoked_at = datetime.utcnow()
    db.commit()
    return {"consent_id": row.public_id, "status": "REVOKED"}


@router.get("/contexts/{access_id}/consents")
def list_patient_consents(
    access_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    rows = db.query(PatientCompanionConsentRequest).filter(
        PatientCompanionConsentRequest.employer_id == principal.employer_id,
        PatientCompanionConsentRequest.patient_id == principal.patient_id,
    ).order_by(PatientCompanionConsentRequest.created_at.desc()).all()

    items = []
    for row in rows:
        share = db.query(PatientCompanionShareGrant).filter(
            PatientCompanionShareGrant.id == row.share_grant_id,
            PatientCompanionShareGrant.employer_id == principal.employer_id,
            PatientCompanionShareGrant.patient_id == principal.patient_id,
            PatientCompanionShareGrant.revoked_at.is_(None),
        ).first()
        if share is None:
            continue
        document = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == row.document_id,
            models.DocumentArchive.patient_id == principal.patient_id,
        ).first()
        if document is None:
            continue
        evidence = db.query(PatientCompanionConsentEvidence).filter(
            PatientCompanionConsentEvidence.consent_request_id == row.id,
        ).first()
        items.append({
            "consent_id": row.public_id,
            "share_id": share.public_id,
            "title": document.title or document.original_filename,
            "document_type": getattr(document.document_type, "value", document.document_type),
            "document_version": row.document_version,
            "state": effective_consent_state(row),
            "created_at": row.created_at,
            "expires_at": row.expires_at,
            "signed_at": evidence.signed_at if evidence else None,
            "evidence_ref": evidence.public_id if evidence else None,
            "qualified_electronic_signature": False,
        })
    return {"items": items}


@router.get("/contexts/{access_id}/consents/{consent_id}/document")
def read_patient_consent_document(
    access_id: str,
    consent_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    row = db.query(PatientCompanionConsentRequest).filter(
        PatientCompanionConsentRequest.public_id == consent_id,
        PatientCompanionConsentRequest.employer_id == principal.employer_id,
        PatientCompanionConsentRequest.patient_id == principal.patient_id,
    ).first()
    if row is None or effective_consent_state(row) in {"REVOKED", "EXPIRED"}:
        raise HTTPException(status_code=404, detail="Consentement indisponible.")

    share = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.id == row.share_grant_id,
        PatientCompanionShareGrant.employer_id == principal.employer_id,
        PatientCompanionShareGrant.patient_id == principal.patient_id,
        PatientCompanionShareGrant.resource_type == "document",
        PatientCompanionShareGrant.resource_id == row.document_id,
        PatientCompanionShareGrant.revoked_at.is_(None),
    ).first()
    if share is None:
        raise HTTPException(status_code=404, detail="Document non partagé.")

    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == row.document_id,
        models.DocumentArchive.patient_id == principal.patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document indisponible.")
    if (
        str(document.document_group_id) != str(row.document_group_id)
        or int(document.version_number) != int(row.document_version)
        or str(document.file_hash) != str(row.document_file_hash)
        or int(document.file_size) != int(row.document_file_size)
    ):
        raise HTTPException(status_code=409, detail="La version du document a changé.")

    integrity_ok, integrity_reason = verify_document_integrity(document)
    if not integrity_ok:
        raise HTTPException(status_code=409, detail=f"Intégrité du document invalide : {integrity_reason}")
    path = resolve_document_storage_path(document)
    try:
        if path.read_bytes()[:5] != b"%PDF-":
            raise HTTPException(status_code=409, detail="Le document lié n'est pas un PDF valide.")
    except OSError:
        raise HTTPException(status_code=409, detail="Document PDF indisponible.") from None
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=document.original_filename or document.filename,
    )


@router.post("/contexts/{access_id}/consents/remote-command")
def patient_consent_remote_command(
    access_id: str,
    body: RemoteCommandEnvelope,
    request: Request,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-consent-remote-command")
    principal, _patient = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == principal.identity_id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Contexte patient introuvable.")
    keyset = db.query(PatientCompanionRemoteKeyset).filter(
        PatientCompanionRemoteKeyset.access_id == access.id,
        PatientCompanionRemoteKeyset.status == "ACTIVE",
        PatientCompanionRemoteKeyset.revoked_at.is_(None),
    ).first()
    if keyset is None:
        raise HTTPException(status_code=409, detail="Transport sécurisé Patient Companion non initialisé.")
    try:
        ack = process_remote_envelope(
            db,
            access=access,
            keyset=keyset,
            compact_jwe=body.blob,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Commande distante Patient Companion invalide.") from None
    return {"blob": ack}
