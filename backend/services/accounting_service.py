import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from backend import models
from backend.utils.accounting_utils import extract_amount_from_clinical_data
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
                "id": h.id,
                "name": h.act_name,
                "base_price": h.base_price,
                "category": h.category,
                "usage_count": h.usage_count
            } for h in habits
        ]

    def get_treasury_summary(self, db: Session, user_employer_id: int) -> Dict[str, Any]:
        """
        Calcule un résumé de la trésorerie pour le Treasury Hub.
        Inclut les Documents (Notes) et les Actes marqués pour la compta.
        """
        # 1. Documents non encore encaissés (is_collected = False)
        docs = db.query(models.DocumentArchive).join(models.Patient).filter(
            or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            models.DocumentArchive.is_collected == False,
            or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None),
            or_(models.DocumentArchive.is_accounted == True, models.DocumentArchive.is_accounted == None),
            models.Patient.employer_id == user_employer_id
        ).all()

        # 2. Actes non encore encaissés (is_collected = False)
        actes = db.query(models.Acte).join(models.Patient).filter(
            models.Acte.is_accounted == True,
            models.Acte.is_collected == False,
            models.Patient.employer_id == user_employer_id
        ).all()

        # Calcul des totaux
        pending_total_docs = sum(extract_amount_from_clinical_data(d.clinical_data) for d in docs if (d.payment_status == models.PaiementStatut.EN_ATTENTE or d.payment_status == models.PaiementStatut.A_ENCAISSER or d.payment_status == None))
        partial_total_docs = sum(extract_amount_from_clinical_data(d.clinical_data) for d in docs if d.payment_status == models.PaiementStatut.PARTIEL)
        
        pending_total_actes = sum(a.montant for a in actes if a.statut_paiement in [models.PaiementStatut.EN_ATTENTE, models.PaiementStatut.A_ENCAISSER])
        partial_total_actes = sum(a.montant for a in actes if a.statut_paiement == models.PaiementStatut.PARTIEL)

        items = []
        for d in docs:
            items.append({
                "id": f"doc_{d.id}",
                "patient_name": f"{d.patient.nom} {d.patient.prenom}",
                "patient_id": d.patient_id,
                "amount": extract_amount_from_clinical_data(d.clinical_data),
                "status": d.payment_status or models.PaiementStatut.EN_ATTENTE,
                "date": d.created_at.isoformat(),
                "type": "NOTE"
            })
            
        for a in actes:
            items.append({
                "id": f"acte_{a.id}",
                "patient_name": f"{a.patient.nom} {a.patient.prenom}",
                "patient_id": a.patient_id,
                "amount": a.montant,
                "status": a.statut_paiement or models.PaiementStatut.EN_ATTENTE,
                "date": a.date_debut.isoformat(),
                "type": "ACTE"
            })

        items.sort(key=lambda x: x["date"], reverse=True)

        return {
            "pending_count": len(items),
            "pending_total": pending_total_docs + pending_total_actes,
            "partial_total": partial_total_docs + partial_total_actes,
            "cheques_count": len([i for i in items if i["status"] == models.PaiementStatut.A_ENCAISSER]),
            "items": items
        }

accounting_service = AccountingService()
