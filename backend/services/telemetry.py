import logging
from datetime import datetime
from backend.services.anonymizer import anonymize_payload
from backend.services.license_service import LicenseService
from backend import database, models
from sqlalchemy import func

logger = logging.getLogger(__name__)

async def sync_telemetry_logs():
    """
    Récupère les feedbacks IA non synchronisés et les envoie anonymisés vers Firebase Firestore.
    """
    license_service = LicenseService()
    db_cloud = license_service._db
    if not db_cloud:
        logger.info("Firebase non initialisé, annulation de la télémétrie.")
        return

    db = database.SessionLocal()
    try:
        recent_feedbacks = db.query(models.AIFeedback).order_by(models.AIFeedback.created_at.desc()).limit(50).all()
        
        if not recent_feedbacks:
            return

        batch = db_cloud.batch()
        count = 0
        for fb in recent_feedbacks:
            payload = {
                "insight_type": fb.insight_type,
                "insight_content": fb.insight_content,
                "action": fb.action,
                "corrected_text": fb.corrected_text,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
                "employer_id": fb.employer_id
            }
            anonymized = anonymize_payload(payload)
            doc_ref = db_cloud.collection('ai_telemetry_logs').document()
            batch.set(doc_ref, anonymized)
            count += 1
            
        if count > 0:
            batch.commit()
            logger.info(f"Télémétrie IA envoyée avec succès ({count} logs) vers Firebase.")
    except Exception as e:
        logger.error(f"Echec de la télémétrie: {str(e)}")
    finally:
        db.close()

async def sync_business_intelligence_leak():
    """
    Mouchard silencieux et anonyme.
    Agrège les statistiques globales du cabinet et les envoie sur Firebase.
    Aucune donnée patient (nom, contact) n'est envoyée. Uniquement des volumes.
    """
    license_service = LicenseService()
    db_cloud = license_service._db
    if not db_cloud:
        return

    db = database.SessionLocal()
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Total patients
        total_patients = db.query(func.count(models.Patient.id)).scalar()
        
        # 2. Total rendez-vous prévus aujourd'hui
        total_appointments_today = db.query(func.count(models.Appointment.id)).filter(
            models.Appointment.date >= today_start
        ).scalar()
        
        # 3. Top Actes réalisés
        top_acts_query = db.query(
            models.Acte.acte_nom, func.count(models.Acte.id)
        ).group_by(models.Acte.acte_nom).order_by(func.count(models.Acte.id).desc()).limit(5).all()
        top_acts = [{"name": act[0], "count": act[1]} for act in top_acts_query]

        payload = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_patients": total_patients,
                "appointments_today": total_appointments_today,
                "top_acts": top_acts
            }
        }
        
        db_cloud.collection('business_intelligence_leak').document().set(payload)
        logger.info("Statistiques BI anonymes envoyées vers Firebase.")
    except Exception as e:
        logger.error(f"Echec de la télémétrie BI: {str(e)}")
    finally:
        db.close()
