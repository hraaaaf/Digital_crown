import hashlib
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import GhostMemoryLog

class GhostMemoryService:
    """
    Gestionnaire de la mémoire du Ghost Brain V2.
    Stocke et récupère les insights cliniques de manière persistante.
    """

    def _hash_context(self, context_data: str) -> str:
        """Génère un hash SHA-256 déterministe pour éviter les doublons."""
        return hashlib.sha256(context_data.encode('utf-8')).hexdigest()

    def add_memory(self, db: Session, patient_id: int, employer_id: int, insight_type: str, content: str, context_data: str) -> Optional[GhostMemoryLog]:
        """
        Ajoute un nouveau souvenir si le contexte est nouveau.
        Retourne le log créé, ou None si c'est un doublon récent.
        """
        context_hash = self._hash_context(context_data)
        
        # Vérification anti-spam (doublon sur le même contexte)
        existing = db.query(GhostMemoryLog).filter(
            GhostMemoryLog.patient_id == patient_id,
            GhostMemoryLog.context_hash == context_hash
        ).first()

        if existing:
            return None # Déjà mémorisé

        new_log = GhostMemoryLog(
            patient_id=patient_id,
            employer_id=employer_id,
            insight_type=insight_type,
            content=content,
            context_hash=context_hash,
            is_read=False
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log

    def get_recent_memories(self, db: Session, patient_id: int, limit: int = 5) -> List[GhostMemoryLog]:
        """
        Récupère les dernières réflexions du Ghost Brain pour contextualiser un nouvel avis.
        """
        return db.query(GhostMemoryLog).filter(
            GhostMemoryLog.patient_id == patient_id
        ).order_by(desc(GhostMemoryLog.created_at)).limit(limit).all()
        
    def mark_as_read(self, db: Session, log_id: int) -> bool:
        """
        Marque un insight comme lu par le praticien.
        """
        log = db.query(GhostMemoryLog).filter(GhostMemoryLog.id == log_id).first()
        if log:
            log.is_read = True
            db.commit()
            return True
        return False

    def get_unread_count(self, db: Session, employer_id: int) -> int:
        """
        Compte le nombre de notifications Ghost Brain non lues pour un praticien.
        """
        return db.query(GhostMemoryLog).filter(
            GhostMemoryLog.employer_id == employer_id,
            GhostMemoryLog.is_read == False
        ).count()

ghost_memory = GhostMemoryService()
