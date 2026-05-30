import httpx
import logging
from backend.services.anonymizer import anonymize_payload
from backend.config import settings
from backend import database, models

logger = logging.getLogger(__name__)

async def sync_telemetry_logs():
    """
    Récupère les feedbacks IA non synchronisés et les envoie anonymisés vers Supabase.
    Cette fonction est conçue pour tourner en tâche de fond (Background Task).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.info("Supabase credentials non configurés, annulation de la télémétrie.")
        return

    db = database.SessionLocal()
    try:
        # Récupère les feedbacks IA récents (En production, on pourrait filtrer sur is_synced=False)
        recent_feedbacks = db.query(models.AIFeedback).order_by(models.AIFeedback.created_at.desc()).limit(50).all()
        
        if not recent_feedbacks:
            return

        payloads = []
        for fb in recent_feedbacks:
            payload = {
                "insight_type": fb.insight_type,
                "insight_content": fb.insight_content,
                "action": fb.action,
                "corrected_text": fb.corrected_text,
                "created_at": fb.created_at.isoformat() if fb.created_at else None
            }
            payloads.append(anonymize_payload(payload))

        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/ai_telemetry_logs",
                json=payloads,
                headers=headers,
                timeout=10.0
            )
            if response.status_code not in (200, 201, 204):
                logger.warning(f"Erreur Télémétrie: {response.status_code} - {response.text}")
            else:
                logger.info(f"Télémétrie envoyée avec succès ({len(payloads)} logs).")
    except Exception as e:
        logger.error(f"Echec de la télémétrie: {str(e)}")
    finally:
        db.close()
