import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from PIL import Image

logger = logging.getLogger(__name__)

class CardExtractor:
    """
    Service d'extraction de données à partir de cartes de visite via Google Gemini.
    Zero-Friction Onboarding.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Utilisation de Flash pour la vitesse (Zero Friction)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("CardExtractor: GEMINI_API_KEY non configurée.")

    async def extract(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse l'image d'une carte de visite et retourne un JSON structuré.
        """
        if not self.model:
            return {"error": "Service IA non configuré"}

        try:
            img = Image.open(image_path)
            
            prompt = """
            Tu es un assistant spécialisé dans la numérisation de cabinets médicaux.
            Analyse cette image de carte de visite et extrée les informations suivantes.
            
            FORMAT DE RÉPONSE ATTENDU (JSON UNIQUEMENT) :
            {
              "nom_cabinet": "Nom de l'établissement",
              "nom_praticien": "Nom complet du docteur",
              "adresse": "Adresse postale complète",
              "specialites": ["liste", "des", "specialites", "extraites"],
              "telephone_fixe": "Numéro de tel fixe",
              "telephone_mobile": "Numéro de portable",
              "email": "Email de contact"
            }
            
            RÈGLES :
            - Si une info est manquante, mets null.
            - Pour les spécialités, traduis-les en français standard si nécessaire.
            - Réponds par le JSON brut, sans backticks ni blabla.
            """
            
            response = await self.model.generate_content_async([prompt, img])
            text = response.text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Erreur extraction carte: {e}")
            return {"error": str(e)}

card_extractor = CardExtractor()
