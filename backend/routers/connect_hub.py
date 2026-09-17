from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session, contains_eager

from backend import database, models
from backend.routers.auth import get_current_user, has_permission
from backend.services.accounting_service import accounting_service

router = APIRouter(tags=["Connect Hub"])


def _alert_items(db: Session, current_user: models.User) -> list[dict]:
    if not has_permission(current_user, "patients"):
        return []

    employer_id = current_user.get_employer_id()
    now = datetime.now()
    alerts = (
        db.query(models.ProactiveAlert)
        .outerjoin(models.Patient, models.ProactiveAlert.patient_id == models.Patient.id)
        .options(contains_eager(models.ProactiveAlert.patient))
        .filter(
            models.ProactiveAlert.employer_id == employer_id,
            models.ProactiveAlert.is_read == False,
            or_(models.ProactiveAlert.expires_at.is_(None), models.ProactiveAlert.expires_at > now),
            or_(models.ProactiveAlert.patient_id.is_(None), models.Patient.deleted_at.is_(None)),
            or_(models.ProactiveAlert.snoozed_until.is_(None), models.ProactiveAlert.snoozed_until <= now),
        )
        .order_by(models.ProactiveAlert.priority, models.ProactiveAlert.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": f"alert:{alert.id}",
            "source": "proactive_alert",
            "category": "attention",
            "title": alert.title,
            "message": alert.message,
            "patient_id": alert.patient_id,
            "patient_name": (
                f"{alert.patient.nom} {alert.patient.prenom}".strip()
                if alert.patient
                else None
            ),
            "priority": alert.priority,
            "action": alert.action,
            "destination": "/dashboard",
            "channel": "in_app",
            "delivery_state": "source_state",
            "delivery_verified": False,
        }
        for alert in alerts
    ]


def _treasury_item(db: Session, current_user: models.User) -> list[dict]:
    if not has_permission(current_user, ["accounting", "payments"]):
        return []

    summary = accounting_service.get_treasury_summary(db, current_user.get_employer_id())
    pending_count = int(summary.get("pending_count") or 0)
    proactive_count = len(summary.get("proactive_alerts") or [])
    if pending_count <= 0 and proactive_count <= 0:
        return []

    return [
        {
            "id": "treasury:pending",
            "source": "treasury_hub",
            "category": "attention",
            "title": "Relances de trésorerie",
            "message": f"{pending_count} dossier(s) à encaisser",
            "patient_id": None,
            "patient_name": None,
            "priority": "high" if proactive_count else "normal",
            "action": "Ouvrir la trésorerie",
            "destination": "/accounting?tab=treasury",
            "channel": "in_app",
            "delivery_state": "source_state",
            "delivery_verified": False,
            "meta": {
                "pending_count": pending_count,
                "proactive_count": proactive_count,
            },
        }
    ]


@router.get("/connect-hub")
def get_connect_hub(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Read-only aggregation over canonical cabinet attention sources.

    No Connect Hub row is persisted and no transport is invoked. Each source keeps
    its own permission and tenant boundary; transport delivery is never inferred.
    """
    items = _alert_items(db, current_user) + _treasury_item(db, current_user)
    return {
        "total": len(items),
        "requires_attention": len(items),
        "items": items,
        "delivery_semantics": "source_state_only",
    }
