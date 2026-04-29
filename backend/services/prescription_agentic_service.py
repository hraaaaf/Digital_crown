import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json

from backend import models, schemas
from backend.services.ai_advisor import ai_advisor

logger = logging.getLogger(__name__)

from backend.services.clinical_rules_engine import clinical_rules
from backend.services.prescription_service import prescription_service

class PrescriptionAgenticService:
    """
    Système de prescription agentique v2.0 "Zero Friction".
    Hybride : Agent Chercheur Local-First (Déterministe + Habitudes) + Agent Architecte Gemini (Synthèse).
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("PrescriptionAgenticService: GEMINI_API_KEY non configurée.")

    def generate_clinical_assessment(self, db: Session, patient_id: int, act_names: List[str], doctor_id: Optional[int] = None) -> Dict[str, Any]:
        """
        AGENT 1 : LE CHERCHEUR (Local First - Déterministe + Habitudes)
        Analyse le dossier et les habitudes du praticien via PrescriptionService.
        """
        # APPEL AU SERVICE D'INTELLIGENCE (Habitudes + CRE)
        smart_plan = prescription_service.get_smart_plan(db, doctor_id, patient_id, act_names)
        
        # Enrichissement du bilan Markdown
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        bilan = f"""
### Bilan de Sécurité & Intelligence Clinique
**Source :** {smart_plan['source']}
**Patient :** {patient.nom} {patient.prenom} ({self._calculate_age(patient.date_naissance)} ans)
**Actes détectés :** {", ".join(act_names)}

**⚠️ Sécurité :**
{chr(10).join([f"• {r}" for r in smart_plan['safety']['risques']]) if smart_plan['safety']['risques'] else "✅ Aucun risque détecté."}

**💊 Suggestions (Habitudes/Protocoles) :**
{chr(10).join([f"• {d['name']} ({d['dosage']})" for d in smart_plan['drugs']])}
        """
        
        smart_plan["bilan_markdown"] = bilan
        return smart_plan

    def design_treatment_plan(self, assessment: Dict[str, Any], patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AGENT 2 : L'ARCHITECTE (Plan de Traitement Synthétisé)
        Transforme le bilan et les suggestions en ordonnance finale élégante.
        """
        if not self.model:
            # Fallback direct si Gemini absent
            return {
                "plan_nom": f"Protocole {assessment.get('act_context', 'Standard')}",
                "prescriptions": assessment.get("drugs", []),
                "conseils_patient": [assessment.get("strategie_globale", "Suivre les recommandations.")]
            }
        
        # Injection de la pharmacopée marocaine réelle du CRE dans le prompt
        moroccan_drugs = clinical_rules.MAROC_PHARMACOPEIA
        
        prompt = f"""
        Tu es un médecin chef de cabinet dentaire au Maroc.
        En te basant sur ce BILAN SCIENTIFIQUE ET HABITUDES :
        {json.dumps(assessment, indent=2)}
        
        Établis un PLAN DE TRAITEMENT final précis.
        PHARMACOPÉE MAROCAINE RÉFÉRENTE: {json.dumps(moroccan_drugs)}
        
        INSTRUCTIONS:
        1. Utilise les médicaments suggérés en priorité (car ce sont les HABITUDES du docteur).
        2. Si un médicament suggéré n'a pas de posologie, rédige une posologie CLAIRE (ex: 1 gélule matin et soir pendant 6 jours).
        3. Assure-toi que la forme est adaptée (ex: Si is_child est true, préférer suspensions).
        4. Ajoute des conseils d'utilisation (ex: au milieu des repas).
        
        Réponds UNIQUEMENT en JSON avec la structure :
        {{
          "plan_nom": "Nom du protocole",
          "prescriptions": [
             {{
               "medicament": "NOM COMMERCIAL",
               "dosage": "...",
               "forme": "...",
               "posologie": "...",
               "duree": "...",
               "conseil": "..."
             }}
          ],
          "conseils_patient": ["..."]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            plan = self._parse_json_response(response.text)
            return plan
        except Exception as e:
            logger.error(f"Erreur Agent Architecte: {e}")
            return {"error": str(e)}

    def _calculate_age(self, birth_date):
        if not birth_date: return 30
        today = datetime.now()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _parse_json_response(self, text: str) -> Dict:
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx+1]
                return json.loads(json_str)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Erreur Parsing JSON IA: {e}")
            return { "error": "Erreur de formatage IA" }

prescription_agentic = PrescriptionAgenticService()
