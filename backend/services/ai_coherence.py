# -*- coding: utf-8 -*-
import json
import logging
import requests
from typing import Dict, List, Any
from backend.config import settings

logger = logging.getLogger(__name__)

OLLAMA_ENDPOINT = f"{settings.OLLAMA_URL}/api/generate"
MODEL = "llama3.2"


class AICoherenceService:
    """
    Module 4 : Intelligence Sémantique & Vigilance Clinique.
    Utilise un SLM local (Ollama) pour valider la cohérence entre le profil
    médical et le document en cours de génération.
    """

    async def analyze_with_ia(
        self,
        patient_info: Dict[str, Any],
        doc_type: str,
        doc_data: Dict[str, Any],
        recent_acts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Analyse sémantique locale pour détecter des contre-indications ou omissions.
        """
        try:
            context = {
                "patient": {
                    "age": patient_info.get("age"),
                    "genre": patient_info.get("genre"),
                    "antecedents": patient_info.get("antecedents", "Néant"),
                },
                "document": {"type": doc_type, "contenu": doc_data},
                "actes_recents": recent_acts,
                "doctor_habits": patient_info.get("doctor_habits", {}),
            }

            prompt = f"""Tu es un assistant de vigilance clinique expert en odontologie (IAmina).
Analyse le contexte patient et le document en cours pour détecter des RISQUES ou INCOHÉRENCES.

CONTEXTE :
{json.dumps(context, ensure_ascii=False, indent=2)}

RÈGLES D'ANALYSE :
1. CONTRE-INDICATIONS : médicament prescrit malgré un antécédent à risque.
2. PRIORITÉ HABITUDES : molécule inhabituelle pour le docteur → signaler comme "info".
3. OMISSIONS : acte invasif sans couverture adaptée.
4. COHÉRENCE D'ÂGE : dosages adaptés à l'âge.

FORMAT DE RÉPONSE (JSON UNIQUEMENT) :
[{{"level": "critical"|"warning"|"info", "message": "description concise"}}]

Si aucun risque, renvoie []. JSON brut uniquement, aucun texte autour."""

            response = requests.post(
                OLLAMA_ENDPOINT,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=10.0,
            )
            response.raise_for_status()

            text = response.json().get("response", "[]").strip()
            if "[" in text and "]" in text:
                text = text[text.find("[") : text.rfind("]") + 1]
            return json.loads(text)

        except requests.exceptions.Timeout:
            logger.warning("AICoherenceService: timeout Ollama, skip analyse")
            return []
        except Exception as e:
            logger.error(f"Erreur Analyse IA Coherence: {e}")
            return []


# Instance singleton
ai_coherence = AICoherenceService()
