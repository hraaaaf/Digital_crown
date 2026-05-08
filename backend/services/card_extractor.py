import io
import base64
import json
import logging
import requests
from typing import Dict, Any
from PIL import Image
from backend.config import settings

logger = logging.getLogger(__name__)

OLLAMA_ENDPOINT = f"{settings.OLLAMA_URL}/api/generate"
VISION_MODEL = "llama3.2-vision"


class CardExtractor:
    """
    Service d'extraction de données à partir de cartes de visite via SLM vision local.
    Zero-Friction Onboarding — aucune API externe.
    """

    async def extract(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse l'image d'une carte de visite et retourne un JSON structuré.
        """
        try:
            img = Image.open(image_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            prompt = """Tu es un assistant spécialisé dans la numérisation de cabinets médicaux.
Analyse cette image de carte de visite et extrait les informations suivantes.

FORMAT DE RÉPONSE ATTENDU (JSON UNIQUEMENT) :
{
  "nom_cabinet": "Nom de l'établissement",
  "nom_praticien": "Nom complet du docteur",
  "nom_praticien_ar": "Nom complet du docteur en Arabe (si présent)",
  "adresse": "Adresse postale complète",
  "specialites": ["liste", "des", "specialites"],
  "telephone_fixe": "Numéro de tel fixe",
  "telephone_mobile": "Numéro de portable",
  "email": "Email de contact"
}

RÈGLES :
- Si une info est manquante, mets null.
- Traduis les spécialités en français standard si nécessaire.
- Réponds par le JSON brut uniquement, sans backticks ni commentaires."""

            response = requests.post(
                OLLAMA_ENDPOINT,
                json={
                    "model": VISION_MODEL,
                    "prompt": prompt,
                    "images": [img_b64],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=30.0,
            )
            response.raise_for_status()

            text = response.json().get("response", "{}").strip()
            return json.loads(text)

        except requests.exceptions.Timeout:
            logger.warning("CardExtractor: timeout Ollama vision")
            return {"error": "Délai dépassé — modèle vision trop lent"}
        except Exception as e:
            logger.error(f"Erreur extraction carte: {e}")
            return {"error": str(e)}


card_extractor = CardExtractor()
