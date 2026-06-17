import json
import logging
import httpx
from typing import Dict, List, Any
from backend.config import settings
from backend.services.llm_cache import llm_cache
from backend.services.pii_masker import mask_patient_context

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
                "patient": mask_patient_context(patient_info),
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

            # Cache check — même contexte clinique = même réponse
            cached = llm_cache.get(MODEL, prompt)
            if cached:
                text = cached.strip()
                if "[" in text and "]" in text:
                    text = text[text.find("[") : text.rfind("]") + 1]
                return json.loads(text)

            # Master Elite Timeout Strategy: 2s connect, 10s generate.
            try:
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
                    llm_cache.set(MODEL, prompt, text)

                    if "[" in text and "]" in text:
                        text = text[text.find("[") : text.rfind("]") + 1]
                    return json.loads(text)

            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.HTTPStatusError):
                # Ollama indisponible. Le fallback Gemini est une SORTIE CLOUD :
                # interdit sauf opt-in explicite du cabinet (S3 — capsule confinée).
                # Sans opt-in, aucun contexte clinique ne quitte le cabinet.
                if settings.CLOUD_AI_ENABLED and settings.GEMINI_API_KEY:
                    return await self._gemini_fallback(prompt)
                if settings.GEMINI_API_KEY and not settings.CLOUD_AI_ENABLED:
                    logger.warning(
                        "AICoherenceService: Ollama hors-ligne. Fallback Gemini BLOQUÉ "
                        "(CLOUD_AI_ENABLED=False). Aucune donnée clinique envoyée au cloud."
                    )
                else:
                    logger.warning("AICoherenceService: Ollama hors-ligne, pas de fallback IA configuré.")
                return []

        except Exception as e:
            logger.error(f"AICoherenceService: Erreur inattendue: {e}")
            return []

    async def _gemini_fallback(self, prompt: str) -> List[Dict[str, Any]]:
        """Fallback to Gemini API when Ollama is unavailable.

        Sortie cloud : verrouillée par CLOUD_AI_ENABLED (S3). Défense en profondeur
        — refuse l'envoi même si appelé directement sans passer par le garde-fou amont.
        """
        if not settings.CLOUD_AI_ENABLED:
            logger.warning("AICoherenceService: _gemini_fallback refusé (CLOUD_AI_ENABLED=False).")
            return []
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            result = model.generate_content(
                f"{prompt}\n\nRéponds UNIQUEMENT avec un tableau JSON valide."
            )
            text = result.text.strip()
            if "[" in text and "]" in text:
                text = text[text.find("[") : text.rfind("]") + 1]
            parsed = json.loads(text)
            llm_cache.set(f"gemini:{MODEL}", prompt, text)
            logger.info("AICoherenceService: Gemini fallback utilisé avec succès.")
            return parsed
        except Exception as e:
            logger.warning(f"AICoherenceService: Gemini fallback échoué: {e}")
            return []

# Instance singleton
ai_coherence = AICoherenceService()
