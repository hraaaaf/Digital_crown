from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionConsentRequest,
    PatientCompanionQuestionnaireAssignment,
    PatientCompanionQuestionnaireDefinition,
    PatientCompanionQuestionnaireSubmission,
    PatientCompanionShareGrant,
)
from backend.models_patient_companion_notifications import (
    PatientCompanionNotificationPreference,
    PatientCompanionNotificationReceipt,
)
from backend.services.patient_companion_consents import effective_consent_state
from backend.services.patient_companion_remote_worker import RemoteDomainResult


APPOINTMENT_REMINDER_WINDOW = timedelta(days=7)
DEFAULT_PREFERENCES = {
    "appointments": True,
    "documents": True,
    "questionnaires": True,
    "consents": True,
}


def _notification_id(access: PatientCompanionAccess, source_key: str) -> str:
    return hashlib.sha256(f"{access.public_id}|{source_key}".encode("utf-8")).hexdigest()[:32]


def _preferences_row(
    db: Session,
    access: PatientCompanionAccess,
) -> PatientCompanionNotificationPreference | None:
    return db.query(PatientCompanionNotificationPreference).filter(
        PatientCompanionNotificationPreference.access_id == access.id,
        PatientCompanionNotificationPreference.employer_id == access.employer_id,
        PatientCompanionNotificationPreference.patient_id == access.patient_id,
    ).first()


def notification_preferences(db: Session, access: PatientCompanionAccess) -> dict[str, bool]:
    row = _preferences_row(db, access)
    if row is None:
        return dict(DEFAULT_PREFERENCES)
    return {
        "appointments": bool(row.appointments),
        "documents": bool(row.documents),
        "questionnaires": bool(row.questionnaires),
        "consents": bool(row.consents),
    }


def _appointment_candidates(
    db: Session,
    access: PatientCompanionAccess,
    now: datetime,
) -> list[dict[str, Any]]:
    rows = db.query(models.Appointment).filter(
        models.Appointment.employer_id == access.employer_id,
        models.Appointment.patient_id == access.patient_id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.datetime_start >= now,
        models.Appointment.datetime_start <= now + APPOINTMENT_REMINDER_WINDOW,
        models.Appointment.status != models.AppointmentStatus.ANNULE,
    ).order_by(models.Appointment.datetime_start.asc()).all()
    return [
        {
            "source_key": f"appointment:{row.id}:{row.datetime_start.isoformat()}",
            "category": "appointments",
            "kind": "APPOINTMENT_REMINDER",
            "title": "Rendez-vous à venir",
            "message": "Un rendez-vous est prévu prochainement avec votre cabinet.",
            "created_at": row.created_at or row.datetime_start,
            "due_at": row.datetime_start,
            "priority": "reminder",
        }
        for row in rows
    ]


def _consent_candidates(
    db: Session,
    access: PatientCompanionAccess,
    now: datetime,
) -> tuple[list[dict[str, Any]], set[int]]:
    requests = db.query(PatientCompanionConsentRequest).filter(
        PatientCompanionConsentRequest.employer_id == access.employer_id,
        PatientCompanionConsentRequest.patient_id == access.patient_id,
        PatientCompanionConsentRequest.revoked_at.is_(None),
    ).order_by(PatientCompanionConsentRequest.created_at.desc()).all()
    items: list[dict[str, Any]] = []
    pending_share_ids: set[int] = set()
    for row in requests:
        if effective_consent_state(row, now=now) != "PENDING":
            continue
        share = db.query(PatientCompanionShareGrant).filter(
            PatientCompanionShareGrant.id == row.share_grant_id,
            PatientCompanionShareGrant.employer_id == access.employer_id,
            PatientCompanionShareGrant.patient_id == access.patient_id,
            PatientCompanionShareGrant.revoked_at.is_(None),
        ).first()
        if share is None:
            continue
        document = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == row.document_id,
            models.DocumentArchive.patient_id == access.patient_id,
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        ).first()
        if document is None:
            continue
        pending_share_ids.add(share.id)
        items.append({
            "source_key": f"consent:{row.public_id}",
            "category": "consents",
            "kind": "CONSENT_PENDING",
            "title": "Signature en attente",
            "message": document.title or document.original_filename or "Un document attend votre signature.",
            "created_at": row.created_at,
            "due_at": row.expires_at,
            "priority": "action",
        })
    return items, pending_share_ids


def _questionnaire_candidates(
    db: Session,
    access: PatientCompanionAccess,
    now: datetime,
) -> list[dict[str, Any]]:
    rows = db.query(
        PatientCompanionQuestionnaireAssignment,
        PatientCompanionQuestionnaireDefinition,
    ).join(
        PatientCompanionQuestionnaireDefinition,
        PatientCompanionQuestionnaireDefinition.id
        == PatientCompanionQuestionnaireAssignment.questionnaire_id,
    ).filter(
        PatientCompanionQuestionnaireAssignment.employer_id == access.employer_id,
        PatientCompanionQuestionnaireAssignment.patient_id == access.patient_id,
        PatientCompanionQuestionnaireAssignment.status == "ASSIGNED",
        PatientCompanionQuestionnaireAssignment.revoked_at.is_(None),
        PatientCompanionQuestionnaireDefinition.employer_id == access.employer_id,
    ).all()

    items: list[dict[str, Any]] = []
    for assignment, definition in rows:
        if assignment.expires_at is not None and assignment.expires_at <= now:
            continue
        submitted = db.query(PatientCompanionQuestionnaireSubmission.id).filter(
            PatientCompanionQuestionnaireSubmission.assignment_id == assignment.id,
            PatientCompanionQuestionnaireSubmission.employer_id == access.employer_id,
            PatientCompanionQuestionnaireSubmission.patient_id == access.patient_id,
        ).first()
        if submitted is not None:
            continue
        items.append({
            "source_key": f"questionnaire:{assignment.public_id}",
            "category": "questionnaires",
            "kind": "QUESTIONNAIRE_PENDING",
            "title": "Questionnaire à compléter",
            "message": definition.title,
            "created_at": assignment.assigned_at,
            "due_at": assignment.expires_at,
            "priority": "action",
        })
    return items


def _document_candidates(
    db: Session,
    access: PatientCompanionAccess,
    pending_consent_share_ids: set[int],
) -> list[dict[str, Any]]:
    shares = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.employer_id == access.employer_id,
        PatientCompanionShareGrant.patient_id == access.patient_id,
        PatientCompanionShareGrant.resource_type == "document",
        PatientCompanionShareGrant.revoked_at.is_(None),
    ).order_by(PatientCompanionShareGrant.created_at.desc()).all()

    items: list[dict[str, Any]] = []
    for share in shares:
        if share.id in pending_consent_share_ids:
            continue
        document = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == share.resource_id,
            models.DocumentArchive.patient_id == access.patient_id,
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        ).first()
        if document is None:
            continue
        items.append({
            "source_key": f"share:{share.public_id}",
            "category": "documents",
            "kind": "DOCUMENT_SHARED",
            "title": "Nouveau document partagé",
            "message": document.title or document.original_filename or "Un document est disponible dans votre espace.",
            "created_at": share.created_at,
            "due_at": None,
            "priority": "info",
        })
    return items


def source_candidates(
    db: Session,
    access: PatientCompanionAccess,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.utcnow()
    consents, pending_consent_share_ids = _consent_candidates(db, access, now)
    items = [
        *_appointment_candidates(db, access, now),
        *consents,
        *_questionnaire_candidates(db, access, now),
        *_document_candidates(db, access, pending_consent_share_ids),
    ]
    for item in items:
        item["notification_id"] = _notification_id(access, item["source_key"])
    return items


def project_notifications(
    db: Session,
    access: PatientCompanionAccess,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.utcnow()
    prefs = notification_preferences(db, access)
    receipts = {
        row.source_key: row
        for row in db.query(PatientCompanionNotificationReceipt).filter(
            PatientCompanionNotificationReceipt.access_id == access.id,
            PatientCompanionNotificationReceipt.employer_id == access.employer_id,
            PatientCompanionNotificationReceipt.patient_id == access.patient_id,
        ).all()
    }

    visible: list[dict[str, Any]] = []
    for item in source_candidates(db, access, now=now):
        if not prefs.get(str(item["category"]), False):
            continue
        receipt = receipts.get(str(item["source_key"]))
        if receipt is not None:
            if receipt.read_at is not None:
                continue
            if receipt.snoozed_until is not None and receipt.snoozed_until > now:
                continue
        visible.append({
            key: value
            for key, value in item.items()
            if key != "source_key"
        })

    priority_order = {"action": 0, "reminder": 1, "info": 2}
    visible.sort(key=lambda item: (
        priority_order.get(str(item.get("priority")), 9),
        item.get("due_at") or datetime.max,
        item.get("created_at") or datetime.max,
    ))
    return {"items": visible, "preferences": prefs}


def _resolve_source(
    db: Session,
    access: PatientCompanionAccess,
    notification_id: str,
) -> dict[str, Any] | None:
    for item in source_candidates(db, access):
        if item["notification_id"] == notification_id:
            return item
    return None


def _lock_access(db: Session, access: PatientCompanionAccess) -> None:
    db.query(PatientCompanionAccess.id).filter(
        PatientCompanionAccess.id == access.id,
        PatientCompanionAccess.employer_id == access.employer_id,
        PatientCompanionAccess.patient_id == access.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).with_for_update().one()


def _receipt_for_source(
    db: Session,
    access: PatientCompanionAccess,
    source_key: str,
) -> PatientCompanionNotificationReceipt:
    row = db.query(PatientCompanionNotificationReceipt).filter(
        PatientCompanionNotificationReceipt.access_id == access.id,
        PatientCompanionNotificationReceipt.source_key == source_key,
    ).first()
    if row is None:
        row = PatientCompanionNotificationReceipt(
            access_id=access.id,
            employer_id=access.employer_id,
            patient_id=access.patient_id,
            source_key=source_key,
        )
        db.add(row)
        db.flush()
    return row


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def handle_notification_read(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"notification_id"} or not isinstance(payload.get("notification_id"), str):
        return _reject("INVALID_REQUEST")
    item = _resolve_source(db, access, payload["notification_id"])
    if item is None:
        return _reject("NOTIFICATION_NOT_FOUND")
    _lock_access(db, access)
    row = _receipt_for_source(db, access, str(item["source_key"]))
    if row.read_at is None:
        row.read_at = datetime.utcnow()
    row.snoozed_until = None
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={"code": "NOTIFICATION_READ", "notification_id": payload["notification_id"]},
    )


def handle_notification_snooze(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"notification_id"} or not isinstance(payload.get("notification_id"), str):
        return _reject("INVALID_REQUEST")
    item = _resolve_source(db, access, payload["notification_id"])
    if item is None:
        return _reject("NOTIFICATION_NOT_FOUND")
    _lock_access(db, access)
    row = _receipt_for_source(db, access, str(item["source_key"]))
    if row.read_at is not None:
        return _reject("NOTIFICATION_ALREADY_READ")
    row.snoozed_until = datetime.utcnow() + timedelta(hours=24)
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "NOTIFICATION_SNOOZED",
            "notification_id": payload["notification_id"],
            "snoozed_until": row.snoozed_until.isoformat(),
        },
    )


def handle_notification_preferences(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != set(DEFAULT_PREFERENCES):
        return _reject("INVALID_REQUEST")
    if not all(isinstance(payload[key], bool) for key in DEFAULT_PREFERENCES):
        return _reject("INVALID_REQUEST")
    _lock_access(db, access)
    row = _preferences_row(db, access)
    if row is None:
        row = PatientCompanionNotificationPreference(
            access_id=access.id,
            employer_id=access.employer_id,
            patient_id=access.patient_id,
        )
        db.add(row)
    for key in DEFAULT_PREFERENCES:
        setattr(row, key, bool(payload[key]))
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={"code": "NOTIFICATION_PREFERENCES_UPDATED", "preferences": notification_preferences(db, access)},
    )


PC05_REMOTE_HANDLERS = {
    "notification.read": handle_notification_read,
    "notification.snooze": handle_notification_snooze,
    "notification.preferences": handle_notification_preferences,
}
