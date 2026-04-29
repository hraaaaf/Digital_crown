import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json

from backend import models, schemas
from backend.services.ai_advisor import ai_advisor

logger = logging.getLogger(__name__)

# --- BASE DE DONNÉES PHARMACOLOGIQUE MAROC (ÉLITE) ---
MOROCCAN_DRUG_DB = {
    "AMOXICILLINE": ["Augmentin", "Clamoxyl", "Amoxyl", "Curam"],
    "AMOXICILLINE_ACIDE_CLAVULANIQUE": ["Augmentin", "Curam", "Clavulin"],
    "SPIRAMYCINE_METRONIDAZOLE": ["Bi-Rodogyl", "Rodogyl", "Birodogyl"],
    "METRONIDAZOLE": ["Flagyl"],
    "IBUPROFENE": ["Spidifen", "Advil", "Algofène", "Nurofen"],
    "ACIDE_TIAPROFRENIQUE": ["Surgam"],
    "PARACETAMOL": ["Doliprane", "Dafalgan", "Efferalgan"],
    "BETAMETHASONE": ["Celestene", "Betneval"],
    "CHLORHEXIDINE": ["Eludril", "Hextril", "Givalex"]
}

class PrescriptionAgenticService:
    """
    Système de prescription agentique v2.0 "Zero Friction".
    Orchestre deux agents Gemini pour transformer le diagnostic en plan thérapeutique.
    """

    def generate_clinical_assessment(self, db: Session, patient_id: int, act_names: List[str]) -> Dict[str, Any]:
        """
        AGENT 1 : RECHERCHE SCIENTIFIQUE (Le Chercheur)
        Analyse le dossier et propose un bilan de cohérence clinique.
        """
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return {"error": "Patient introuvable"}

        age = self._calculate_age(patient.date_naissance)
        context = {
            "patient": {
                "nom": patient.nom,
                "age": age,
                "genre": patient.genre,
                "poids": "65kg (estimé)" if age > 15 else "Variable", # Idéalement à ajouter au modèle
                "antecedents": patient.antecedents_medicaux or "Néant",
                "allergies": self._extract_allergies(patient.antecedents_medicaux)
            },
            "actes_du_jour": act_names,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        prompt = f"""
        Tu es un expert en pharmacologie clinique dentaire de classe mondiale. 
        Ta mission est de réaliser un BILAN SCIENTIFIQUE pour le patient suivant :
        
        CONTEXTE PATIENT:
        {json.dumps(context, indent=2)}
        
        INSTRUCTIONS:
        1. Analyse les risques (allergies, interactions avec les antécédents).
        2. Identifie les molécules recommandées par la littérature (HAS, OMS) pour ces actes.
        3. Propose une stratégie : Antibioprophylaxie ? Antibiothérapie curative ? Gestion de l'inflammation ?
        4. Si c'est un enfant, calcule les doses théoriques en mg/kg.
        
        Réponds UNIQUEMENT en JSON avec la structure :
        {{
          "risques_identifies": ["..."],
          "recommandations_moleculaires": [
             {{"molecule": "...", "justification": "...", "priorite": "haute/moyenne"}}
          ],
          "strategie_globale": "...",
          "bilan_markdown": "### Bilan Scientifique... (Rédige un résumé pro en Markdown)"
        }}
        """

        try:
            # Appel à l'agent IA (Gemini via AIAdvisor)
            response = ai_advisor.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            assessment = self._parse_json_response(response.text)
            return assessment
        except Exception as e:
            logger.error(f"Erreur Agent Chercheur: {e}")
            return {"error": str(e), "fallback": True}

    def design_treatment_plan(self, assessment: Dict[str, Any], patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AGENT 2 : L'ARCHITECTE (Plan de Traitement)
        Transforme le bilan en ordonnance concrète avec le contexte marocain.
        """
        
        prompt = f"""
        Tu es un médecin chef de cabinet dentaire au Maroc.
        En te basant sur ce BILAN SCIENTIFIQUE :
        {json.dumps(assessment, indent=2)}
        
        Et ce CONTEXTE PATIENT :
        {json.dumps(patient_context, indent=2)}
        
        Établis un PLAN DE TRAITEMENT précis en utilisant uniquement des médicaments disponibles au Maroc.
        MÉDICAMENTS DISPONIBLES (Noms commerciaux): {json.dumps(MOROCCAN_DRUG_DB)}
        
        INSTRUCTIONS:
        1. Choisis le MEILLEUR nom commercial pour chaque molécule.
        2. Détermine la forme (Gélules, Comprimés, Sachets, Suspension) selon l'âge.
        3. Rédige une posologie CLAIRE et SANS AMBIGUÏTÉ (ex: 1 gélule matin et soir pendant 6 jours).
        4. Ajoute des conseils d'utilisation (ex: au milieu des repas).
        
        Réponds UNIQUEMENT en JSON avec la structure :
        {{
          "plan_nom": "Protocole ...",
          "prescriptions": [
             {{
               "medicament": "NOM COMMERCIAL (ex: Augmentin)",
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
            response = ai_advisor.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            plan = self._parse_json_response(response.text)
            return plan
        except Exception as e:
            logger.error(f"Erreur Agent Architecte: {e}")
            return {"error": str(e)}

    def _calculate_age(self, birth_date):
        if not birth_date: return 30
        today = datetime.now()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _extract_allergies(self, text: Optional[str]) -> List[str]:
        if not text: return []
        # Logique simplifiée pour la démo, l'agent fera mieux
        text = text.lower()
        allergies = []
        if "pénicilline" in text or "amox" in text: allergies.append("Pénicillines")
        if "atb" in text: allergies.append("Antibiotiques")
        return allergies

    def _parse_json_response(self, text: str) -> Dict:
        # Nettoyage du markdown si nécessaire
        clean_text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except:
            # Fallback manuel si le JSON est mal formé
            return { "error": "JSON malformé", "raw": text }

prescription_agentic = PrescriptionAgenticService()
