# -*- coding: utf-8 -*-
import os
import json
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AICoherenceService:
    """
    Module 4 : Intelligence Sémantique & Vigilance Clinique.
    Utilise Gemini 1.5 Flash pour valider la cohérence entre le profil médical
    et le document en cours de génération.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("AICoherenceService: GEMINI_API_KEY non configurée.")

    async def analyze_with_ia(self, patient_info: Dict[str, Any], doc_type: str, doc_data: Dict[str, Any], recent_acts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyse sémantique via Gemini pour détecter des contre-indications ou omissions.
        """
        if not self.model:
            return []

        try:
            # Préparation du contexte pour l'IA
            context = {
                "patient": {
                    "age": patient_info.get("age"),
                    "genre": patient_info.get("genre"),
                    "antecedents": patient_info.get("antecedents", "Néant")
                },
                "document": {
                    "type": doc_type,
                    "contenu": doc_data
                },
                "actes_recents": recent_acts
            }

            prompt = f"""
            Tu es un assistant de vigilance clinique expert en odontologie.
            Analyse le contexte patient et le document en cours pour détecter des RISQUES ou des INCOHÉRENCES.
            
            CONTEXTE :
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            RÈGLES D'ANALYSE :
            1. CONTRE-INDICATIONS : Détecte si un médicament (AINS, Aspirine, etc.) est prescrit malgré un antécédent à risque (Ulcère, Cardiopathie, Grossesse, Allaitement).
            2. OMISSIONS : Si un acte invasif (extraction, chirurgie) a été réalisé chez un patient à risque (Valvulopathie, Diabète), vérifie si une couverture adaptée est suggérée.
            3. COHÉRENCE D'ÂGE : Vérifie si les dosages ou types de documents sont adaptés à l'âge du patient.
            
            FORMAT DE RÉPONSE (JSON UNIQUEMENT) :
            [
              {{
                "level": "critical" | "warning" | "info",
                "message": "Description concise du risque ou de l'incohérence"
              }}
            ]
            
            RÈGLES DE SORTIE :
            - Si aucun risque n'est détecté, renvoie une liste vide [].
            - Réponds uniquement par le JSON brut.
            - Sois précis et professionnel dans tes messages.
            """

            response = await self.model.generate_content_async(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            
            # Nettoyage si Gemini ajoute du texte autour
            if "[" in text and "]" in text:
                text = text[text.find("["):text.rfind("]")+1]
            
            warnings = json.loads(text)
            return warnings
        except Exception as e:
            logger.error(f"Erreur Analyse IA Coherence: {e}")
            return []

# Instance singleton
ai_coherence = AICoherenceService()
