"""V1.5-04.5 — authorized care-sheet collection on the patient's own Companion.

A kiosk may announce that documents are available, but must never receive
clinical PDF bytes. Retrieval requires an authenticated, paired patient
identity, exactly the access that claimed a currently active Station session,
and a trusted finalized/authorized archive. No PDF or bearer URL is cached.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import get_db, patient_identity, principal_for_access
from backend.services.station_care_sheet import WITHDRAW_ACTION, care_sheet_state, verified_care_sheet_bytes
from backend.services.station_document_eligibility import (
    SelfServiceDocumentCandidate, StationEligibilityContext,
    evaluate_document_eligibility,
)

router = APIRouter()


def _authorized_session(
    db: Session, identity: PatientCompanionIdentity, access_id: str, session_id: str,
):
    principal, _ = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == access_id,
        PatientCompanionAccess.identity_id == identity.id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.patient_id == principal.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="STATION_DOCUMENT_SESSION_NOT_FOUND")
    now = datetime.utcnow()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == principal.employer_id,
        models.WorkstationPatientSession.patient_id == principal.patient_id,
        models.WorkstationPatientSession.patient_access_id == access.id,
        models.WorkstationPatientSession.claimed_at.is_not(None),
        models.WorkstationPatientSession.purged_at.is_(None),
        models.WorkstationPatientSession.expires_at > now,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="STATION_DOCUMENT_SESSION_NOT_FOUND")
    station = db.query(models.WorkstationMode).filter(
        models.WorkstationMode.id == row.workstation_id,
        models.WorkstationMode.employer_id == principal.employer_id,
        models.WorkstationMode.default_experience == "station",
        models.WorkstationMode.revoked_at.is_(None),
    ).first()
    if station is None:
        raise HTTPException(status_code=404, detail="STATION_DOCUMENT_SESSION_NOT_FOUND")
    context = StationEligibilityContext(
        tenant_id=principal.employer_id,
        patient_id=principal.patient_id,
        station_id=station.id,
        session_id=row.id,
        session_tenant_id=row.employer_id,
        session_patient_id=row.patient_id,
        session_station_id=row.workstation_id,
        session_created_at=row.created_at,
        session_claimed_at=row.claimed_at,
        session_expires_at=row.expires_at,
        session_purged_at=row.purged_at,
        station_tenant_id=station.employer_id,
        station_experience=station.default_experience,
        station_revoked_at=station.revoked_at,
        now=now,
    )
    return principal, context


def _eligible(db: Session, employer_id: int, context: StationEligibilityContext, document: models.DocumentArchive) -> bool:
    state = care_sheet_state(db, document, employer_id=employer_id)
    return evaluate_document_eligibility(
        context,
        SelfServiceDocumentCandidate(
            document_id=str(document.id),
            tenant_id=employer_id,
            patient_id=document.patient_id,
            kind="care_sheet",
            is_active=document.status == models.DocumentStatus.ACTIF,
            is_latest_version=document.is_latest_version is True,
            finalized=state.finalized,
            withdrawal_authorized=state.withdrawal_authorized,
        ),
    ).eligible


@router.get("/station-session/{session_id}/documents")
def companion_station_documents(
    session_id: str,
    response: Response,
    access_id: str = Query(alias="accessId", min_length=36, max_length=36),
    db: Session = Depends(get_db),
    identity: PatientCompanionIdentity = Depends(patient_identity),
):
    principal, context = _authorized_session(db, identity, access_id, session_id)
    rows = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == principal.patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.is_latest_version.is_(True),
    ).order_by(models.DocumentArchive.id.desc()).limit(100).all()
    eligible = [
        {"documentId": item.id, "kind": "care_sheet"}
        for item in rows if _eligible(db, principal.employer_id, context, item)
    ]
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return {"documents": eligible}


@router.get("/station-session/{session_id}/documents/care-sheet/{document_id}")
def companion_station_care_sheet(
    session_id: str, document_id: int, request: Request,
    access_id: str = Query(alias="accessId", min_length=36, max_length=36),
    db: Session = Depends(get_db),
    identity: PatientCompanionIdentity = Depends(patient_identity),
):
    principal, context = _authorized_session(db, identity, access_id, session_id)
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_id,
        models.DocumentArchive.patient_id == principal.patient_id,
    ).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="STATION_CARE_SHEET_NOT_FOUND")
    if not _eligible(db, principal.employer_id, context, doc):
        raise HTTPException(status_code=409, detail="STATION_CARE_SHEET_NOT_ELIGIBLE")
    try:
        contents = verified_care_sheet_bytes(doc)
    except (ValueError, OSError):
        raise HTTPException(status_code=409, detail="STATION_CARE_SHEET_FILE_UNTRUSTED") from None
    db.add(models.AuditLog(
        user_id=None,
        employer_id=principal.employer_id,
        action=WITHDRAW_ACTION,
        resource_type="DocumentArchive",
        resource_id=str(doc.id),
        details=f"Verified PDF delivered to authenticated Patient Companion; sha256={doc.file_hash}",
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()
    return Response(
        content=contents, media_type="application/pdf",
        headers={
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "Content-Disposition": f'attachment; filename="care-sheet-{int(doc.id)}.pdf"',
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )
