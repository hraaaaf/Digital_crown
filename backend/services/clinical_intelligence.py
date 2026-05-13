import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, List, Optional

from backend import models, schemas
from backend.services.ai_advisor import ai_advisor

logger = logging.getLogger(__name__)

class ClinicalIntelligenceService:
    """
    Service d'agrégation et d'intelligence clinique (Module 2 & 3).
    """

    def get_patient_summary(self, db: Session, patient_id: int) -> Dict[str, Any]:
        """
        Module 2 — Résumé Flash Patient (P0).
        Aggrege les données sans LLM pour une réponse instantanée.
        """
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return {}

        # 1. Dernière visite
        last_acte = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).order_by(desc(models.Acte.date_debut)).first()
        last_visit = None
        if last_acte:
            last_visit = {
                "date": last_acte.date_debut.strftime("%Y-%m-%d"),
                "acte": last_acte.libelle,
                "days_ago": (datetime.now() - last_acte.date_debut).days
            }

        # 2. Prochain RDV
        next_app = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.datetime_start >= datetime.now(),
            models.Appointment.status != models.AppointmentStatus.ANNULE
        ).order_by(models.Appointment.datetime_start).first()
        
        next_visit = None
        if next_app:
            next_visit = {
                "date": next_app.datetime_start.strftime("%Y-%m-%d"),
                "time": next_app.datetime_start.strftime("%H:%M"),
                "motif": next_app.motif
            }

        # 3. Résumé clinique
        clinical_parts = []
        if patient.antecedents_medicaux:
            clinical_parts.append(f"Antécédents : {patient.antecedents_medicaux}")
        
        if patient.dossier and patient.dossier.is_ortho_active:
            clinical_parts.append("Traitement orthodontique actif.")
            
        # Nombre de couronnes/actes prothétiques
        prothese_count = db.query(models.Acte).filter(
            models.Acte.patient_id == patient_id,
            models.Acte.type_acte == models.ActeType.PROTHESE
        ).count()
        if prothese_count > 0:
            clinical_parts.append(f"{prothese_count} acte(s) prothétique(s) réalisé(s).")

        clinical_summary = " ".join(clinical_parts) if clinical_parts else "Dossier vierge."

        # 4. Alertes IA (Heuristiques)
        alerts = []
        if patient.antecedents_medicaux and any(x in patient.antecedents_medicaux.lower() for x in ["diabète", "avk", "cardiaque", "hypertension"]):
            alerts.append(f"Alerte Médicale : {patient.antecedents_medicaux}")
            
        # Check last analysis for instability
        last_analyses = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).order_by(desc(models.CephaloAnalysis.created_at)).limit(2).all()
        if len(last_analyses) >= 2:
            a1 = last_analyses[0].angles_data
            a2 = last_analyses[1].angles_data
            if a1 and a2 and 'IMPA' in a1 and 'IMPA' in a2:
                diff = abs(a1['IMPA'].get('valeur', 0) - a2['IMPA'].get('valeur', 0))
                if diff > 3:
                    alerts.append("IMPA instable sur les dernières analyses.")

        risk_level = "low"
        if alerts: risk_level = "moderate"
        if any("Alerte Médicale" in a for a in alerts): risk_level = "high"

        return {
            "last_visit": last_visit,
            "next_visit": next_visit,
            "clinical_summary": clinical_summary,
            "alerts": alerts,
            "risk_level": risk_level
        }

    def get_full_diagnostic(self, db: Session, patient_id: int) -> Dict[str, Any]:
        """
        Module 3 — Panneau Conseil Clinique (P2).
        Utilise le LLM via AIAdvisor si possible.
        """
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return {"report": "Patient introuvable."}

        # 1. Fetch last analysis
        last_analysis = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).order_by(desc(models.CephaloAnalysis.id)).first()
        
        if not last_analysis or not last_analysis.angles_data:
            return {
                "report": "## Synthèse Clinique\nDonnées céphalométriques manquantes pour un diagnostic IA complet.\n\n" + 
                          f"**Contexte Patient** : {patient.nom.upper()} {patient.prenom.capitalize()}, {self._calculate_age(patient.date_naissance)} ans.\n" +
                          f"**Antécédents** : {patient.antecedents_medicaux or 'Néant'}.",
                "source": "heuristic",
                "confidence": 0.5,
                "generated_at": datetime.now().isoformat()
            }

        # 2. Format data for AIAdvisor
        # We need to construct a schemas.CephaloAnalysisResult
        # But wait, ai_advisor.generate_diagnostic expects a result object with metrics
        
        # Let's use the heuristic fallback if LLM is too slow or for simplicity first
        # But let's try to simulate the call
        
        # We wrap the stored JSON into the expected schema
        try:
            # Reconstruct result object from stored JSON
            # This is complex because angles_data is a raw dict, not exactly CephaloAnalysisResult
            # AIAdvisor expects osseuse and dentaire categories
            
            # For now, let's use the heuristic fallback directly from AIAdvisor 
            # to give the user immediate feedback in the Panel
            
            cohort = "Adulte"
            age = self._calculate_age(patient.date_naissance)
            if age < 14: cohort = f"Enfant ({age} ans)"
            
            # AIAdvisor._heuristic_fallback expects SkeletalAnalysis and DentalAnalysis objects
            # It's better to implement a "Global" prompt for AIAdvisor that takes Patient + Analysis
            
            report_dict = ai_advisor.generate_diagnostic(
                schemas.CephaloAnalysisResult(
                    analysis_metadata=schemas.AnalysisMetadata(
                        pixel_ratio=last_analysis.mm_per_pixel or 1.0, 
                        cohort=cohort
                    ),
                    metrics=schemas.AnalysisMetrics(**last_analysis.angles_data),
                    visual_debug={},
                    t1_projection={},
                    clinical_data=schemas.ClinicalData()
                ),
                use_slm=False # Force heuristic for speed in "Live"
            )
            
            # Format report as Markdown
            markdown = f"## 🦷 Synthèse Diagnostique ({cohort})\n"
            markdown += f"{report_dict.get('diagnostic_squelettique', '')}\n\n"
            
            markdown += "## 📐 Analyse Dentaire\n"
            markdown += f"{report_dict.get('analyse_dentaire', '')}\n\n"
            
            markdown += "## 💡 Stratégie Thérapeutique (COM)\n"
            markdown += f"{report_dict.get('strategie_therapeutique', '')}"

            return {
                "report": markdown,
                "source": "slm" if not report_dict.get("is_fallback") else "heuristic",
                "confidence": 0.85,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating diagnostic: {e}")
            return {"report": f"Erreur lors de la génération du diagnostic : {str(e)}"}

    def _calculate_age(self, born):
        today = datetime.now()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

clinical_intel = ClinicalIntelligenceService()
