import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend import models
from datetime import datetime

logger = logging.getLogger(__name__)

class AccountingService:
    """
    Service de gestion comptable et apprentissage des actes fréquents.
    """

    def record_act_usage(self, db: Session, doctor_id: int, act_name: str, price: float = 0.0, category: str = None):
        """
        Enregistre l'usage d'un acte clinique pour l'apprentissage des raccourcis.
        """
        try:
            act_name = act_name.strip()
            existing = db.query(models.DoctorActHabit).filter(
                models.DoctorActHabit.doctor_id == doctor_id,
                models.DoctorActHabit.act_name == act_name
            ).first()

            if existing:
                existing.usage_count += 1
                # Mettre à jour le prix si c'est une valeur non nulle
                if price > 0:
                    existing.base_price = price
                if category:
                    existing.category = category
            else:
                new_habit = models.DoctorActHabit(
                    doctor_id=doctor_id,
                    act_name=act_name,
                    base_price=price,
                    category=category,
                    usage_count=1
                )
                db.add(new_habit)
            
            db.commit()
            logger.info(f"✅ Habitude d'acte enregistrée : {act_name} pour Dr {doctor_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur record_act_usage : {e}")

    def get_frequent_acts(self, db: Session, doctor_id: int, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Retourne les actes les plus fréquents pour la barre de raccourcis.
        """
        habits = db.query(models.DoctorActHabit).filter(
            models.DoctorActHabit.doctor_id == doctor_id
        ).order_by(models.DoctorActHabit.usage_count.desc()).limit(limit).all()
        
        return [
            {
                "name": h.act_name,
                "price": h.base_price,
                "category": h.category
            } for h in habits
        ]

accounting_service = AccountingService()
