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

    def get_recommended_duration(self, act_name: str) -> int:
        """
        Calcule dynamiquement la durée optimale recommandée (en minutes) 
        selon la complexité de l'acte clinique.
        """
        name = act_name.upper().strip()
        
        if "CANAL" in name or "ENDO" in name:
            if "PLURI" in name or "MOLAIRE" in name:
                return 60
            return 45
            
        if "IMPLANT" in name:
            return 90
        if "CHIRURGIE" in name or "BIOPSIE" in name:
            return 60
            
        if "EXTRACTION" in name or "AVULSION" in name:
            if "SAGESSE" in name or "INCLUS" in name or "COMPLEXE" in name:
                return 45
            return 30
            
        if "COURONNE" in name or "PROTHÈSE" in name or "FACETTE" in name:
            return 45
        if "COMPOSITE" in name or "RECONSTRUCTION" in name:
            return 30
            
        if "DÉTARTRAGE" in name or "PROPHYLAXIE" in name:
            return 30
        if "CONSULTATION" in name or "EXAMEN" in name or "BILAN" in name:
            return 15
            
        return 30

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
        
        if last_detartrage:
            _days_detartrage = (datetime.now() - last_detartrage.date_debut).days
            if _days_detartrage > 365:
                triggers.append({
                    "type": "CRITICAL_PREVENTION",
                    "title": "Détartrage Annuel Dépassé",
                    "message": f"Dernier détartrage il y a {_days_detartrage} jours. Risque parodontal élevé.",
                    "action": "Planifier Détartrage"
                })
            elif _days_detartrage > 180:
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

        # A2: Gap Ortho Critique
        if patient.dossier and patient.dossier.is_ortho_active:
            _now = datetime.now()
            _next_ortho_rdv = db.query(models.Appointment).filter(
                models.Appointment.patient_id == patient_id,
                models.Appointment.datetime_start > _now,
                models.Appointment.status != "ANNULÉ"
            ).order_by(models.Appointment.datetime_start).first()
            if not _next_ortho_rdv:
                triggers.append({
                    "type": "ORTHO_GAP",
                    "title": "Gap Ortho Critique",
                    "message": "Traitement orthodontique actif — aucun RDV futur planifié.",
                    "action": "Planifier RDV Ortho"
                })
            else:
                _days_until = (_next_ortho_rdv.datetime_start - _now).days
                if _days_until > 45:
                    triggers.append({
                        "type": "ORTHO_GAP",
                        "title": "Gap Ortho Critique",
                        "message": f"Prochain RDV ortho dans {_days_until}j (seuil critique : 45j).",
                        "action": "Avancer le RDV"
                    })

        # B2: Abandon Pattern
        _now_b2 = datetime.now()
        _last_appts = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.datetime_start < _now_b2
        ).order_by(desc(models.Appointment.datetime_start)).limit(4).all()
        if len(_last_appts) >= 2:
            _consecutive_cancels = 0
            for _appt in _last_appts:
                if _appt.status == "ANNULÉ":
                    _consecutive_cancels += 1
                else:
                    break
            if _consecutive_cancels >= 2:
                _has_future_rdv = db.query(models.Appointment).filter(
                    models.Appointment.patient_id == patient_id,
                    models.Appointment.datetime_start > _now_b2,
                    models.Appointment.status != "ANNULÉ"
                ).first()
                if not _has_future_rdv:
                    triggers.append({
                        "type": "ABANDON_RISK",
                        "title": "Risque Perte Patient",
                        "message": f"{_consecutive_cancels} RDV annulés consécutifs sans rebooking.",
                        "action": "Contacter le Patient"
                    })

        # C3: Patient Haute Valeur à Risque
        if patient.manual_grade == "PLATINUM":
            _solde = db.query(func.sum(models.Acte.montant)).filter(
                models.Acte.patient_id == patient_id,
                models.Acte.statut_paiement == "EN_ATTENTE"
            ).scalar() or 0.0
            if _solde > 2000:
                triggers.append({
                    "type": "HIGH_VALUE_RISK",
                    "title": "Patient Premium — Impayé Critique",
                    "message": f"Patient PLATINUM avec {_solde:.0f} MAD en attente de règlement.",
                    "action": "Relancer le Paiement"
                })

        # A4: Traitement Abandonné
        _devis = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == "DEVIS"
        ).order_by(desc(models.DocumentArchive.created_at)).first()
        if _devis:
            _days_devis = (datetime.now() - _devis.created_at).days
            _acte_after = db.query(models.Acte).filter(
                models.Acte.patient_id == patient_id,
                models.Acte.date_debut > _devis.created_at
            ).first()
            if _days_devis > 60 and not _acte_after:
                triggers.append({
                    "type": "TREATMENT_ABANDONED",
                    "title": "Traitement Non Commencé",
                    "message": f"Devis établi il y a {_days_devis}j sans acte commencé.",
                    "action": "Rappeler le patient"
                })

        # A5: Rétention Post-Soin
        _cutoff_low = datetime.now() - timedelta(days=10)
        _cutoff_high = datetime.now() - timedelta(days=5)
        _post_care = db.query(models.Acte).filter(
            models.Acte.patient_id == patient_id,
            models.Acte.libelle.ilike("%extrac%"),
            models.Acte.date_debut >= _cutoff_low,
            models.Acte.date_debut <= _cutoff_high
        ).first()
        if _post_care:
            triggers.append({
                "type": "POST_CARE_FOLLOWUP",
                "title": "Suivi Post-Extraction",
                "message": "Extraction réalisée il y a ~7 jours. Appel de suivi recommandé.",
                "action": "Appeler le patient"
            })

        # B1: Score No-Show
        _six_months_ago = datetime.now() - timedelta(days=180)
        _rdvs_b1 = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.datetime_start >= _six_months_ago
        ).all()
        if len(_rdvs_b1) >= 3:
            _annules_b1 = sum(1 for r in _rdvs_b1 if r.status == "ANNULÉ")
            _taux = _annules_b1 / len(_rdvs_b1)
            if _taux > 0.4:
                triggers.append({
                    "type": "NOSHOW_RISK",
                    "title": "Risque No-Show Élevé",
                    "message": f"Taux d'annulation : {int(_taux * 100)}% sur {len(_rdvs_b1)} RDV.",
                    "action": "Envoyer rappel WhatsApp"
                })

        # B4: Progression Traitement Ortho
        dossier = patient.dossier
        if dossier and dossier.is_ortho_active:
            _semestres = db.query(func.count(models.Acte.id)).filter(
                models.Acte.patient_id == patient_id,
                models.Acte.type_acte == "ORTHO_SEMESTRE"
            ).scalar() or 0
            if _semestres > 0:
                _progression = min(int((_semestres / 4) * 100), 100)
                triggers.append({
                    "type": "ORTHO_PROGRESSION",
                    "title": "Progression Orthodontie",
                    "message": f"{_semestres} séance(s) sur ~4 — {_progression}% d'avancement estimé.",
                    "action": "Voir plan de traitement"
                })

        # B3: Créneau Maudit
        _all_cancelled = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.status == "ANNULÉ"
        ).all()
        if len(_all_cancelled) >= 3:
            from collections import Counter
            _hour_counts = Counter(a.datetime_start.hour for a in _all_cancelled)
            _cursed_hour, _curse_count = _hour_counts.most_common(1)[0]
            if _curse_count >= 3:
                triggers.append({
                    "type": "CURSED_SLOT",
                    "title": "Créneau Récurrent Annulé",
                    "message": f"Patient annule systématiquement à {_cursed_hour}h ({_curse_count} fois). Éviter ce créneau.",
                    "action": "Reprogrammer à un autre créneau"
                })

        # B5: Prédiction Fin Traitement Ortho
        if dossier and dossier.is_ortho_active:
            _ortho_acts = db.query(models.Acte).filter(
                models.Acte.patient_id == patient_id,
                models.Acte.type_acte == "ORTHO_SEMESTRE"
            ).order_by(models.Acte.date_debut).all()
            if len(_ortho_acts) >= 2:
                _intervals = [
                    (_ortho_acts[i + 1].date_debut - _ortho_acts[i].date_debut).days
                    for i in range(len(_ortho_acts) - 1)
                ]
                _avg_interval = sum(_intervals) / len(_intervals)
                _remaining_semesters = max(0, 4 - len(_ortho_acts))
                _predicted_end = _ortho_acts[-1].date_debut + timedelta(days=int(_avg_interval * _remaining_semesters))
                _months_left = max(0, (_predicted_end - datetime.now()).days // 30)
                if _months_left > 0:
                    triggers.append({
                        "type": "ORTHO_COMPLETION_ESTIMATE",
                        "title": "Fin de Traitement Estimée",
                        "message": f"Fin ortho estimée dans ~{_months_left} mois ({_predicted_end.strftime('%B %Y')}).",
                        "action": "Voir progression"
                    })

        return triggers

habits_engine = HabitsEngine()
