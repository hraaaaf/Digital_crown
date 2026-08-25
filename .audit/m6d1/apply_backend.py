from pathlib import Path

path = Path('backend/routers/mobile.py')
text = path.read_text(encoding='utf-8')

old_import = 'from sqlalchemy.orm import Session\n'
new_import = 'from sqlalchemy.orm import Session, contains_eager\n'
if old_import not in text:
    raise SystemExit('Expected sqlalchemy.orm import not found')
text = text.replace(old_import, new_import, 1)

marker = '\n\nclass MobileRefreshRequest(BaseModel):\n'
if marker not in text:
    raise SystemExit('MobileRefreshRequest marker not found')

block = r'''


def _serialize_mobile_notification(alert) -> dict:
    patient = getattr(alert, "patient", None)
    priority = getattr(alert, "priority", None)
    priority = getattr(priority, "value", priority)
    patient_name = None
    if patient is not None:
        patient_name = f"{getattr(patient, 'prenom', '') or ''} {getattr(patient, 'nom', '') or ''}".strip() or None
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "patient_name": patient_name,
        "type": alert.alert_type,
        "title": alert.title,
        "message": alert.message,
        "priority": priority,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.get('/notifications', summary='Notifications mobiles non lues du cabinet')
def get_mobile_notifications(
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    now = datetime.now()
    alerts = (
        db.query(models.ProactiveAlert)
        .outerjoin(models.Patient, models.ProactiveAlert.patient_id == models.Patient.id)
        .options(contains_eager(models.ProactiveAlert.patient))
        .filter(
            models.ProactiveAlert.employer_id == employer_id,
            models.ProactiveAlert.is_read == False,  # noqa: E712
            or_(models.ProactiveAlert.expires_at.is_(None), models.ProactiveAlert.expires_at > now),
            or_(models.ProactiveAlert.patient_id.is_(None), models.Patient.deleted_at.is_(None)),
            or_(models.ProactiveAlert.snoozed_until.is_(None), models.ProactiveAlert.snoozed_until <= now),
        )
        .order_by(models.ProactiveAlert.priority, models.ProactiveAlert.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "total": len(alerts),
        "alerts": [_serialize_mobile_notification(alert) for alert in alerts],
    }


@router.patch('/notifications/{alert_id}/read', summary='Marquer une notification mobile comme lue')
def mark_mobile_notification_read(
    alert_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    alert = db.query(models.ProactiveAlert).filter(
        models.ProactiveAlert.id == alert_id,
        models.ProactiveAlert.employer_id == employer_id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail='Notification introuvable')
    alert.is_read = True
    db.commit()
    return {"status": "ok"}


@router.patch('/notifications/{alert_id}/snooze', summary='Reporter une notification mobile de 24 heures')
def snooze_mobile_notification(
    alert_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(_legacy.require_mobile_permission("patients")),
):
    employer_id = mobile_user.get_employer_id()
    alert = db.query(models.ProactiveAlert).filter(
        models.ProactiveAlert.id == alert_id,
        models.ProactiveAlert.employer_id == employer_id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail='Notification introuvable')
    now = datetime.now()
    alert.snoozed_until = now + timedelta(hours=24)
    if not alert.expires_at or alert.expires_at < alert.snoozed_until + timedelta(days=1):
        alert.expires_at = alert.snoozed_until + timedelta(days=1)
    db.commit()
    return {"status": "ok", "snoozed_until": alert.snoozed_until.isoformat()}
'''

text = text.replace(marker, block + marker, 1)
path.write_text(text, encoding='utf-8')
