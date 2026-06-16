import logging
import threading
from datetime import datetime, timedelta

from backend import models, database
from backend.services.habits_engine import habits_engine as _engine
from backend.services.push_service import send_push_to_employer

logger = logging.getLogger(__name__)


def send_license_expiry_emails() -> int:
    """Envoie une relance email une seule fois a J-7, J-3 et J-1."""
    from backend.services.email_service import email_service

    now = datetime.utcnow()
    sent_count = 0
    checkpoints = {7, 3, 1}

    with database.SessionLocal() as db:
        users = db.query(models.User).filter(
            models.User.employer_id == None,
            models.User.is_active == True,
            models.User.is_licensed == True,
            models.User.license_expires_at != None,
            models.User.license_expires_at >= now,
            models.User.license_expires_at <= now + timedelta(days=8),
        ).all()

        for user in users:
            days_left = (user.license_expires_at.date() - now.date()).days
            if days_left not in checkpoints:
                continue

            action = f"license_expiry_email_{days_left}d"
            already_sent = db.query(models.LicenseHistory).filter(
                models.LicenseHistory.user_id == user.id,
                models.LicenseHistory.action == action,
            ).first()
            if already_sent:
                continue

            try:
                if email_service.send_license_expiry_notice(
                    user.email,
                    user.nom_complet,
                    user.license_expires_at,
                    days_left,
                ):
                    db.add(models.LicenseHistory(
                        user_id=user.id,
                        admin_id=None,
                        action=action,
                        duration=days_left,
                    ))
                    sent_count += 1
            except Exception as exc:
                logger.warning("License expiry email failed for %s: %s", user.email, exc)

        db.commit()

    logger.info("License expiry emails sent: %d", sent_count)
    return sent_count


def run_daily_alerts():
    """Calcule les alertes proactives pour tous les patients actifs et les stocke en DB."""
    with database.SessionLocal() as db:
        cutoff = datetime.now() - timedelta(days=90)
        active_ids = {row[0] for row in db.query(models.Acte.patient_id).filter(
            models.Acte.date_debut >= cutoff).distinct().all()}
        ortho_ids = {row[0] for row in db.query(models.DossierClinique.patient_id).filter(
            models.DossierClinique.is_ortho_active == True).all()}
        all_ids = active_ids | ortho_ids

        db.query(models.ProactiveAlert).filter(
            models.ProactiveAlert.expires_at < datetime.now()
        ).delete(synchronize_session=False)

        new_count = 0
        new_by_employer: dict[int, int] = {}
        for patient_id in all_ids:
            patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
            if not patient:
                continue
            try:
                triggers = _engine.check_proactive_triggers(db, patient_id)
            except Exception as e:
                logger.warning("Trigger error patient %s: %s", patient_id, e)
                db.rollback()
                continue
            for t in triggers:
                exists = db.query(models.ProactiveAlert).filter(
                    models.ProactiveAlert.patient_id == patient_id,
                    models.ProactiveAlert.alert_type == t["type"],
                    models.ProactiveAlert.created_at >= datetime.now() - timedelta(hours=24)
                ).first()
                if not exists:
                    priority = 1 if any(k in t["type"] for k in ("CRITICAL", "RISK", "ABANDONED")) else 2
                    db.add(models.ProactiveAlert(
                        employer_id=patient.employer_id,
                        patient_id=patient_id,
                        alert_type=t["type"],
                        title=t["title"],
                        message=t["message"],
                        action=t.get("action", ""),
                        priority=priority,
                        expires_at=datetime.now() + timedelta(days=7)
                    ))
                    new_count += 1
                    new_by_employer[patient.employer_id] = new_by_employer.get(patient.employer_id, 0) + 1
                    
                    # Ghost Brain V2 : Conscience temporelle
                    from backend.services.ghost_memory_service import ghost_memory
                    ghost_memory.add_memory(
                        db=db,
                        patient_id=patient_id,
                        employer_id=patient.employer_id,
                        insight_type="TEMPOREL",
                        content=f"Analyse Proactive: {t['title']} - {t['message']}",
                        context_data=f"{t['type']}_{patient_id}_{datetime.now().strftime('%Y-%m')}"
                    )
        db.commit()

        logger.info("Daily alerts: %d new alerts for %d active patients", new_count, len(all_ids))

        for emp_id, count in new_by_employer.items():
            sent = send_push_to_employer(
                db, emp_id,
                title=f"Digital Crown — {count} alerte(s) aujourd'hui",
                body="Consultez votre tableau de bord pour les actions prioritaires."
            )
            if sent:
                logger.info("Push sent to employer %s: %d device(s)", emp_id, sent)


_stop_flag = False
_current_timer = None

def start_daily_scheduler():
    """Lance le scheduler récursif — première exécution après 10s, puis toutes les 24h."""
    global _current_timer, _stop_flag
    _stop_flag = False
    
    def _run_and_reschedule():
        global _current_timer
        if _stop_flag:
            return
            
        try:
            # 1. Sauvegarde automatique de la DB (V1 Requirement)
            from backend.services.backup_service import backup_service
            backup_service.run_daily_backup()

            # 2. Relances transactionnelles de licence
            send_license_expiry_emails()
            
            # 3. Alertes proactives
            run_daily_alerts()
        except Exception as e:
            logger.warning("Daily scheduler failed: %s", e)
            
        if not _stop_flag:
            try:
                _current_timer = threading.Timer(86400, _run_and_reschedule)
                _current_timer.daemon = True
                _current_timer.start()
            except RuntimeError:
                # L'interpréteur Python est en cours d'arrêt (souvent pendant les tests)
                pass

    try:
        _current_timer = threading.Timer(10, _run_and_reschedule)
        _current_timer.daemon = True
        _current_timer.start()
        logger.info("Daily scheduler armed (first run in 10s)")
    except RuntimeError:
        pass

def stop_daily_scheduler():
    """Arrête proprement le scheduler (utile pour les tests)."""
    global _current_timer, _stop_flag
    _stop_flag = True
    if _current_timer:
        _current_timer.cancel()
