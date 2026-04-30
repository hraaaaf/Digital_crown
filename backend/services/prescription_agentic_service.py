import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json

from backend import models, schemas
from backend.services.clinical_rules_engine import clinical_rules
from backend.services.prescription_service import prescription_service

logger = logging.getLogger(__name__)

class PrescriptionAgenticService:
    """
    Système de prescription "Zero Friction" v4.7.
    Architecture 100% Déterministe & Local-First.
    L'Agent "Chercheur" analyse les habitudes et la sécurité, 
    L'Agent "Architecte" structure le plan sans IA (Rule-based).
    """
    
    def __init__(self):
        # Aucune clé API requise, moteur local-only
        pass

    def generate_clinical_assessment(self, db: Session, patient_id: int, act_names: List[str], doctor_id: Optional[int] = None) -> Dict[str, Any]:
        """
        ANALYSE : Local-First (CRE + Habitudes)
        """
        # APPEL AU SERVICE D'INTELLIGENCE (Habitudes + CRE)
        smart_plan = prescription_service.resolve_smart_prescription(db, patient_id, act_names, doctor_id)
        
        # Enrichissement du bilan Markdown
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        bilan = f"""
### Bilan Scientifique (Local Engine)
**Source :** {smart_plan['source']}
**Patient :** {patient.nom} {patient.prenom} ({self._calculate_age(patient.date_naissance)} ans)
**Contexte Clinique :** {", ".join(act_names)}

**⚠️ Sécurité & Contre-indications :**
{chr(10).join([f"• {r}" for r in smart_plan['safety']['risques']]) if smart_plan['safety']['risques'] else "✅ Validation sécurité effectuée (Aucun risque détecté)."}

**💊 Suggestions (Habitudes/Protocoles) :**
{chr(10).join([f"• {d['name']} ({d['dosage']})" for d in smart_plan['drugs']])}
        """
        
        smart_plan["bilan_markdown"] = bilan
        return smart_plan

    def design_treatment_plan(self, assessment: Dict[str, Any], patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        STRUCTURE : Transformation déterministe des suggestions en plan de traitement.
        Zéro LLM - Utilise les données du ClinicalRulesEngine et les habitudes.
        """
        # On récupère les drogues suggérées (qui incluent déjà les habitudes du docteur)
        suggested_drugs = assessment.get("drugs", [])
        
        # Transformation en structure d'ordonnance finale
        prescriptions = []
        for drug in suggested_drugs:
            prescriptions.append({
                "medicament": drug.get("name", "").upper(),
                "dosage": drug.get("dosage", ""),
                "forme": drug.get("forme", "Comprimés"),
                "posologie": drug.get("posologie", ""), # Soit l'habitude, soit vide pour saisie manuelle
                "conseil": ""
            })
            
        return {
            "plan_nom": f"Protocole {assessment.get('act_context', 'Standard')}",
            "prescriptions": prescriptions,
            "conseils_patient": [assessment.get("strategie_globale", "Suivre les recommandations.")],
            "is_deterministic": True
        }

    def _calculate_age(self, birth_date):
        if not birth_date: return 30
        today = datetime.now()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

prescription_agentic = PrescriptionAgenticService()
