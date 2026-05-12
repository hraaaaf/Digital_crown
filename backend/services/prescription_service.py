import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import func, desc, case
from sqlalchemy.orm import Session
from backend import models
from backend.services.clinical_rules_engine import clinical_rules

logger = logging.getLogger(__name__)

class PrescriptionService:
    """
    Service d'intelligence de prescription (Phase 2 & 3).
    Gère la hiérarchie : Préférences Doc > Protocoles Système > IA.
    """

    def resolve_smart_prescription(self, db: Session, patient_id: int, acts: List[str], doctor_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Génère un plan de prescription intelligent basé sur le contexte.
        """
        # 1. Récupérer les données patient
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient introuvable")

        patient_data = {
            "age": self._calculate_age(patient.date_naissance),
            "poids": 70, # TODO: Récupérer le poids réel si dispo
            "antecedents": patient.antecedents_medicaux or ""
        }

        # 2. ANALYSE SÉCURITÉ (CRE)
        safety_analysis = clinical_rules.analyze_case(patient_data, acts)
        
        # 3. RÉCUPÉRATION DES HABITUDES (HABITS ENGINE)
        # On prend le premier acte majeur pour les habitudes
        main_act = clinical_rules._normalize_act_name(acts[0]) if acts else "DEFAULT"
        habit = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.doctor_id == doctor_id,
            models.DoctorPrescriptionPreference.act_code == main_act
        ).first()

        plan_source = "Système (Standard)"
        suggested_drugs = []

        if habit:
            plan_source = "Habituelle (Praticien)"
            suggested_drugs = habit.drugs_json
        else:
            # Fallback sur les molécules recommandées par le CRE
            for rec in safety_analysis["recommandations_moleculaires"]:
                suggested_drugs.append({
                    "name": rec["noms_commerciaux"][0],
                    "dosage": rec["dosage_defaut"],
                    "forme": rec["forme"],
                    "posologie": "Selon prescription" # Sera affiné par l'IA ou les habitudes
                })

        return {
            "source": plan_source,
            "act_context": main_act,
            "drugs": suggested_drugs,
            "safety": {
                "risques": safety_analysis["risques_identifies"],
                "dosage_note": safety_analysis["dosage_note"],
                "is_child": safety_analysis["is_child"]
            },
            "moteur": f"HabitsEngine v1.0 + {safety_analysis['moteur']}"
        }

    def learn_habit(self, db: Session, doctor_id: int, act_code: str, drugs: List[Dict[str, Any]]):
        """
        Enregistre ou met à jour une habitude de prescription.
        """
        try:
            # Nettoyer les données pour le stockage
            cleaned_drugs = []
            for d in drugs:
                cleaned_drugs.append({
                    "name": d.get("name", d.get("nom", "")),
                    "dosage": d.get("dosage", ""),
                    "forme": d.get("forme", ""),
                    "posologie": d.get("posologie", "")
                })

            existing = db.query(models.DoctorPrescriptionPreference).filter(
                models.DoctorPrescriptionPreference.doctor_id == doctor_id,
                models.DoctorPrescriptionPreference.act_code == act_code
            ).first()

            if existing:
                existing.drugs_json = cleaned_drugs
            else:
                new_habit = models.DoctorPrescriptionPreference(
                    doctor_id=doctor_id,
                    act_code=act_code,
                    drugs_json=cleaned_drugs
                )
                db.add(new_habit)
            
            db.commit()
            logger.info(f"✅ Habitude enregistrée pour {doctor_id} sur l'acte {act_code}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur apprentissage habitude : {e}")
            
    def record_medication_usage(self, db: Session, doctor_id: int, med_name: str, dosage: str = None, posologie: str = None):
        """
        Enregistre l'usage d'un médicament pour l'apprentissage futur.
        """
        try:
            med_name = med_name.strip().upper()
            existing = db.query(models.DoctorMedicationHabit).filter(
                models.DoctorMedicationHabit.doctor_id == doctor_id,
                models.DoctorMedicationHabit.medication_name == med_name,
                models.DoctorMedicationHabit.dosage == dosage,
                models.DoctorMedicationHabit.posologie == posologie
            ).first()

            if existing:
                existing.usage_count += 1
            else:
                new_habit = models.DoctorMedicationHabit(
                    doctor_id=doctor_id,
                    medication_name=med_name,
                    dosage=dosage,
                    posologie=posologie
                )
                db.add(new_habit)
            
            # Incrémenter aussi le compteur global
            global_med = db.query(models.Medication).filter(models.Medication.nom == med_name).first()
            if global_med:
                global_med.usage_count += 1
                
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur record_medication_usage : {e}")

    def get_personalized_suggestions(self, db: Session, doctor_id: int, query: str = "") -> Dict[str, List[str]]:
        """
        Retourne des suggestions prioritaires basées sur les habitudes du docteur.
        Priorise les correspondances au début du nom (Start-with priority).
        """
        query = query.strip().upper()
        if not query:
            return {"medications": [], "dosages": [], "posologies": []}
        
        # 1. Médicaments favoris (Habits)
        # On utilise une expression CASE pour prioriser les correspondances au début
        med_habits = db.query(
            models.DoctorMedicationHabit.medication_name,
            func.sum(models.DoctorMedicationHabit.usage_count).label("total")
        ).filter(
            models.DoctorMedicationHabit.doctor_id == doctor_id,
            models.DoctorMedicationHabit.medication_name.ilike(f"%{query}%")
        ).group_by(models.DoctorMedicationHabit.medication_name).order_by(
            # Priorité 1 : Commence par la requête (0 = oui, 1 = non)
            case(
                (models.DoctorMedicationHabit.medication_name.ilike(f"{query}%"), 0),
                else_=1
            ),
            # Priorité 2 : Fréquence d'usage
            desc("total")
        ).limit(10).all()
        
        meds = [m[0] for m in med_habits]
        
        # 2. Compléter avec la base globale si besoin (< 5 résultats)
        if len(meds) < 10:
            global_meds = db.query(models.Medication.nom).filter(
                models.Medication.nom.ilike(f"%{query}%"),
                ~models.Medication.nom.in_(meds)
            ).order_by(
                # Priorité 1 : Commence par la requête
                case(
                    (models.Medication.nom.ilike(f"{query}%"), 0),
                    else_=1
                ),
                # Priorité 2 : Fréquence globale
                models.Medication.usage_count.desc()
            ).limit(10 - len(meds)).all()
            meds.extend([m[0] for m in global_meds])
        
        return {
            "medications": meds,
            "dosages": [],
            "posologies": []
        }

    def get_medication_details(self, db: Session, doctor_id: int, med_name: str) -> Dict[str, List[str]]:
        """
        Récupère les dosages et posologies habituels pour un médicament donné.
        Fallback sur le dictionnaire global si pas d'habitudes.
        """
        med_name = med_name.strip().upper()
        
        # 1. Rechercher dans les habitudes
        habits = db.query(models.DoctorMedicationHabit).filter(
            models.DoctorMedicationHabit.doctor_id == doctor_id,
            models.DoctorMedicationHabit.medication_name == med_name
        ).order_by(models.DoctorMedicationHabit.usage_count.desc()).all()
        
        dosages = list(set([h.dosage for h in habits if h.dosage]))
        posologies = list(set([h.posologie for h in habits if h.posologie]))
        
        # 2. Si vide, chercher dans le dictionnaire global
        if not dosages:
            global_meds = db.query(models.Medication).filter(
                models.Medication.nom == med_name
            ).all()
            dosages = list(set([m.dosage for m in global_meds if m.dosage]))
            # Si on n'a pas encore de posologie habituelle pour ce méd, on laisse vide 
            # ou on pourrait suggérer une posologie par défaut si elle existait en BDD.
        
        return {
            "dosages": dosages[:5],
            "posologies": posologies[:5]
        }

    def get_doctor_presets(self, db: Session, doctor_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les ordonnances types (presets) enregistrées par le docteur.
        """
        presets = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.doctor_id == doctor_id
        ).order_by(models.DoctorPrescriptionPreference.updated_at.desc()).limit(10).all()
        
        return [
            {
                "id": p.id,
                "act_context": p.act_code,
                "drugs": p.drugs_json
            } for p in presets
        ]

    def get_doctor_habits_summary(self, db: Session, doctor_id: int) -> Dict[str, Any]:
        """
        Récupère une synthèse des habitudes globales du docteur pour le contexte IA.
        """
        # 1. Top médicaments
        med_habits = db.query(
            models.DoctorMedicationHabit.medication_name,
            func.sum(models.DoctorMedicationHabit.usage_count).label("total")
        ).filter(models.DoctorMedicationHabit.doctor_id == doctor_id
        ).group_by(models.DoctorMedicationHabit.medication_name
        ).order_by(desc("total")).limit(5).all()

        # 2. Top Presets (Actes)
        presets = db.query(models.DoctorPrescriptionPreference.act_code).filter(
            models.DoctorPrescriptionPreference.doctor_id == doctor_id
        ).limit(5).all()

        return {
            "top_medications": [m[0] for m in med_habits],
            "favorite_acts": [p[0] for p in presets]
        }

    def _calculate_age(self, birth_date) -> int:
        from datetime import date
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

prescription_service = PrescriptionService()
