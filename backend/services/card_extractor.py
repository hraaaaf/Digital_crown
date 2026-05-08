import io
import os
import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

class CardExtractor:
    """
    Service d'extraction de données à partir de cartes de visite via Google Gemini.
    Zero-Friction Onboarding.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("CardExtractor: GEMINI_API_KEY non configurée.")

    async def extract(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse l'image d'une carte de visite et retourne un JSON structuré.
        """
        if not self.client:
            return {"error": "Service IA non configuré"}

        try:
            img = Image.open(image_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            img_bytes = buf.getvalue()

            prompt = """
            Tu es un assistant spécialisé dans la numérisation de cabinets médicaux.
            Analyse cette image de carte de visite et extrait les informations suivantes.

            FORMAT DE RÉPONSE ATTENDU (JSON UNIQUEMENT) :
            {
              "nom_cabinet": "Nom de l'établissement",
              "nom_praticien": "Nom complet du docteur",
              "nom_praticien_ar": "Nom complet du docteur en Arabe (si présent)",
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

            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
            )
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Erreur extraction carte: {e}")
            return {"error": str(e)}

card_extractor = CardExtractor()
