import json
import logging
import httpx
from typing import Dict, List, Any
from backend.config import settings

logger = logging.getLogger(__name__)

OLLAMA_ENDPOINT = f"{settings.OLLAMA_URL}/api/generate"
MODEL = "llama3.2"

class AICoherenceService:
    """
    Module 4 : Intelligence Sémantique & Vigilance Clinique.
    Utilise un SLM local (Ollama) pour valider la cohérence.
    Optimisé pour ne pas bloquer les sessions DB en cas d'indisponibilité (Master Elite Fix).
    """

    async def analyze_with_ia(
        self,
        patient_info: Dict[str, Any],
        doc_type: str,
        doc_data: Dict[str, Any],
        recent_acts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Analyse sémantique asynchrone.
        Si Ollama est hors-ligne, échoue rapidement pour libérer les ressources.
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

            # Master Elite Timeout Strategy: 2s pour se connecter, 10s pour générer.
            # Si Ollama est éteint, on le sait en < 2s.
            async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=2.0)) as client:
                response = await client.post(
                    OLLAMA_ENDPOINT,
                    json={
                        "model": MODEL,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                        "options": {"temperature": 0.1},
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                text = result.get("response", "[]").strip()
                
                if "[" in text and "]" in text:
                    text = text[text.find("[") : text.rfind("]") + 1]
                return json.loads(text)

        except (httpx.ConnectError, httpx.ConnectTimeout):
            # Ollama n'est pas lancé
            logger.warning("AICoherenceService: Ollama hors-ligne. Analyse IA ignorée.")
            return []
        except httpx.HTTPStatusError as e:
            # 404 = modèle non installé localement (ex: llama3.2 absent)
            if e.response.status_code == 404:
                logger.warning(
                    f"AICoherenceService: Modèle '{MODEL}' introuvable dans Ollama. "
                    f"Exécuter : ollama pull {MODEL}"
                )
            else:
                logger.warning(f"AICoherenceService: Réponse HTTP inattendue ({e.response.status_code}). Analyse ignorée.")
            return []
        except Exception as e:
            logger.error(f"AICoherenceService: Erreur inattendue: {e}")
            return []

# Instance singleton
ai_coherence = AICoherenceService()
