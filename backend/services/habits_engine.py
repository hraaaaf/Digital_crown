import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session
from backend import models

logger = logging.getLogger(__name__)

class HabitsEngine:
    """
    Moteur de Profilage Local (MPL).
    Analyse les fréquences d'usage pour rendre l'interface prédictive.
    """

    def record_act_sequence(self, db: Session, doctor_id: int, patient_id: int):
        """
        Analyse les deux derniers actes d'un patient pour renforcer la corrélation.
        """
        try:
            last_two = db.query(models.Acte).filter(
                models.Acte.patient_id == patient_id
            ).order_by(desc(models.Acte.date_debut)).limit(2).all()

            if len(last_two) < 2:
                return

            act_b = last_two[0].libelle
            act_a = last_two[1].libelle

            # Renforcement du lien A -> B
            existing = db.query(models.DoctorActCorrelation).filter(
                models.DoctorActCorrelation.doctor_id == doctor_id,
                models.DoctorActCorrelation.act_a == act_a,
                models.DoctorActCorrelation.act_b == act_b
            ).first()

            if existing:
                existing.occurrence_count += 1
            else:
                new_corr = models.DoctorActCorrelation(
                    doctor_id=doctor_id,
                    act_a=act_a,
                    act_b=act_b
                )
                db.add(new_corr)
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording act sequence: {e}")

    def get_smart_bundles(self, db: Session, doctor_id: int, current_act: str) -> List[str]:
        """
        Suggère les actes suivants probables basés sur l'acte en cours (TF logic).
        """
        correlations = db.query(models.DoctorActCorrelation).filter(
            models.DoctorActCorrelation.doctor_id == doctor_id,
            models.DoctorActCorrelation.act_a == current_act
        ).order_by(desc(models.DoctorActCorrelation.occurrence_count)).limit(3).all()

        return [c.act_b for c in correlations]

    def get_relevance_score(self, db: Session, doctor_id: int, act_code: str, drug_name: str) -> float:
        """
        Calcule un score de pertinence (0.0 - 1.0) pour un médicament dans un contexte d'acte.
        Basé sur la fréquence d'usage relative.
        """
        # Fréquence absolue pour cet acte
        habit = db.query(models.DoctorMedicationHabit).filter(
            models.DoctorMedicationHabit.doctor_id == doctor_id,
            models.DoctorMedicationHabit.medication_name == drug_name
        ).first()
        
        if not habit:
            return 0.1

        # On pourrait normaliser par le total d'usages du docteur (IDF-like)
        total_doctor_usages = db.query(func.sum(models.DoctorMedicationHabit.usage_count)).filter(
            models.DoctorMedicationHabit.doctor_id == doctor_id
        ).scalar() or 1

        return min(0.95, (habit.usage_count / total_doctor_usages) * 10)

    def check_proactive_triggers(self, db: Session, patient_id: int) -> List[Dict[str, Any]]:
        """
        Machine à états : analyse le dossier patient pour déclencher des actions.
        """
        triggers = []
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return []

        # Exemple 1 : Fin de traitement Ortho (Trigger Phase)
        if patient.dossier and patient.dossier.is_ortho_active:
            # On cherche si un acte de "Contention" a été posé récemment
            contention_act = db.query(models.Acte).filter(
                models.Acte.patient_id == patient_id,
                models.Acte.libelle.ilike("%contention%")
            ).first()
            
            if contention_act:
                triggers.append({
                    "type": "PHASE_END",
                    "title": "Fin de Traitement Actif",
                    "message": "Phase de contention détectée. Prévoir le suivi à 6 mois.",
                    "action": "Planifier contrôle"
                })

        # Exemple 2 : Prévention (Trigger Temps)
        last_detartrage = db.query(models.Acte).filter(
            models.Acte.patient_id == patient_id,
            models.Acte.libelle.ilike("%détartrage%")
        ).order_by(desc(models.Acte.date_debut)).first()
        
        if last_detartrage and (datetime.now() - last_detartrage.date_debut).days > 180:
            triggers.append({
                "type": "PREVENTION",
                "title": "Hygiène & Prévention",
                "message": "Dernier détartrage il y a plus de 6 mois.",
                "action": "Suggérer Détartrage"
            })

        # Exemple 3 : Dossier Incomplet (Trigger Qualité)
        if not patient.antecedents_medicaux or len(patient.antecedents_medicaux) < 5:
            triggers.append({
                "type": "QUALITY",
                "title": "Sécurité Clinique",
                "message": "Antécédents médicaux non renseignés. Risque de contre-indication.",
                "action": "Compléter Dossier"
            })

        return triggers

habits_engine = HabitsEngine()
