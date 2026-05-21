import logging
import threading
from datetime import datetime, timedelta

from backend import models, database
from backend.services.habits_engine import habits_engine as _engine
from backend.services.push_service import send_push_to_employer

logger = logging.getLogger(__name__)


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


def start_daily_scheduler():
    """Lance le scheduler récursif — première exécution après 10s, puis toutes les 24h."""
    def _run_and_reschedule():
        try:
            run_daily_alerts()
        except Exception as e:
            logger.warning("Daily scheduler failed: %s", e)
        t = threading.Timer(86400, _run_and_reschedule)
        t.daemon = True
        t.start()

    initial = threading.Timer(10, _run_and_reschedule)
    initial.daemon = True
    initial.start()
    logger.info("Daily scheduler armed (first run in 10s)")
