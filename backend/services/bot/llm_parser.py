import os
import re
import json
import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend.services.bot.intent_parser import ParsedIntent, intent_parser as fallback_parser

logger = logging.getLogger(__name__)

class LLMIntentParser:
    def __init__(self):
        self.fallback_parser = fallback_parser
        # Par defaut: on vise une API compatible OpenAI (Ollama en local, Groq, ou OpenAI).
        # La résolution passe par l'AI Gateway (S4) : local-first, egress cloud
        # refusé et replié sur le local tant que CLOUD_AI_ENABLED est False.
        from backend.services.ai_gateway import resolve_llm_base
        self.api_base = resolve_llm_base(os.getenv("LLM_API_BASE", "http://localhost:11434/v1"))
        self.api_key = os.getenv("LLM_API_KEY", "ollama")
        self.model = os.getenv("LLM_MODEL", "llama3")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "3.0")) # Timeout court pour vite fallback
        
        self.system_prompt = """Tu es l'assistant IA déterministe 'Crown Bot' d'un logiciel dentaire.
Ta seule tâche est d'analyser le message de l'utilisateur et d'en extraire l'intention principale et les entités au format JSON stricte.
Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte, explication, ni bloc de code Markdown autour.

Liste des intentions exactes (choisis-en une seule):
- SEARCH_PATIENT
- QUERY_PATIENT
- QUERY_AGENDA
- QUERY_FINANCE
- QUERY_LAB
- QUERY_STATS
- QUERY_ALERTS
- CREATE_APPOINTMENT
- CREATE_PRESCRIPTION
- CREATE_DEVIS
- CHANGE_STATUS
- QUERY_KNOWLEDGE
- HELP
- GREETING
- UNKNOWN

Entités possibles (toutes optionnelles, mets des chaînes vides si inconnu):
- patient_name (string): le nom de famille ou prénom complet du patient
- date (string): la date demandée (ex: "demain", "lundi", "01/01/2026")
- time (string): l'heure du rendez-vous au format HH:MM (ex: "10:00", "14:30")
- duration (string): la durée en minutes (ex: "30", "45")
- motif (string): le motif de la consultation
- tooth (string): le numéro de la dent (ex: "46", "32")

Exemple de sortie :
{"intent": "CREATE_APPOINTMENT", "entities": {"patient_name": "Bennani", "date": "demain", "time": "10:00", "duration": "30", "motif": "carie", "tooth": ""}}
"""

    def parse(self, message: str, context: list | None = None) -> ParsedIntent:
        from backend.services.security.data_sanitizer import data_sanitizer

        # 1. Anonymisation du message courant
        sanitized_message, mapping = data_sanitizer.sanitize(message)

        # 2. Construire les messages LLM avec contexte conversationnel sanitizé
        messages: list = [{"role": "system", "content": self.system_prompt}]
        for turn in (context or []):
            role = "assistant" if turn.get("role") == "bot" else "user"
            sanitized_content, _ = data_sanitizer.sanitize(turn.get("content", ""))
            messages.append({"role": role, "content": sanitized_content})
        messages.append({"role": "user", "content": sanitized_message})

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.0,
                        "response_format": {"type": "json_object"}
                    }
                )
                
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Nettoyage si le modèle a rajouté du texte autour du JSON
                if "{" in content and "}" in content:
                    content = content[content.find("{") : content.rfind("}") + 1]
                
                parsed_json = json.loads(content)
                
                # 2. Restauration des données (De-anonymisation)
                # On restaure chaque valeur dans le dictionnaire des entités
                entities = parsed_json.get("entities", {})
                for key, val in entities.items():
                    if isinstance(val, str):
                        entities[key] = data_sanitizer.restore(val, mapping)
                        
                intent_str = parsed_json.get("intent", "UNKNOWN")
                entities = self._normalize_entities(entities)
                # Complète les champs structurés que le LLM omet ou renvoie mal
                # formés (heure, durée, date ISO, dent, id) via le parser regex
                # déterministe appliqué au message original.
                self._fill_structured_gaps(entities, message)

                logger.info(f"LLM parsed intent: {intent_str} with entities: {entities}")

                return ParsedIntent(
                    intent=intent_str,
                    confidence=0.9,
                    entities=entities,
                    raw_message=message
                )
            else:
                logger.warning(f"LLM API Error {response.status_code}: {response.text}. Fallback to Regex.")
                return self.fallback_parser.parse(message)
                
        except Exception as e:
            logger.warning(f"LLM parsing failed ({e}). Fallback to Regex.")
            return self.fallback_parser.parse(message, context=context)

    def complete(self, messages: list, temperature: float = 0.5, timeout: float | None = None) -> Optional[str]:
        """
        Appel LLM non-streaming unifié (remplace les httpx.Client dupliqués dans
        le dispatcher). Retourne le texte brut ou None si indisponible.
        """
        try:
            with httpx.Client(timeout=timeout or self.timeout) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": messages, "temperature": temperature},
                )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            logger.warning("LLM complete erreur %s: %s", response.status_code, response.text)
        except Exception as e:
            logger.warning("LLM complete échoué: %s", e)
        return None

    def stream_completion(self, messages: list, temperature: float = 0.5):
        """
        Streaming LLM (SSE OpenAI-compatible). Yield les deltas de contenu au fur
        et à mesure. Silencieux (rien yieldé) si le LLM est indisponible.
        """
        try:
            with httpx.Client(timeout=httpx.Timeout(30.0, connect=self.timeout)) as client:
                with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code != 200:
                        logger.warning("LLM stream erreur %s", response.status_code)
                        return
                    for line in response.iter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            delta = json.loads(data)["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as e:
            logger.warning("LLM stream échoué: %s", e)
            return

    def _normalize_entities(self, entities: dict) -> dict:
        """
        Aligne les clés LLM sur le schéma de l'ActionDispatcher ET normalise les
        valeurs : date -> ISO (YYYY-MM-DD), heure -> HH:MM, durée -> int.
        Une valeur invalide est écartée plutôt que propagée (le dispatcher
        demandera une clarification au lieu de crasher sur un fromisoformat).
        """
        key_map = {
            "date": "target_date",
            "tooth": "tooth_number",
            "duration": "duration_minutes",
        }
        normalized: Dict[str, Any] = {}
        for k, v in entities.items():
            if not v:
                continue
            key = key_map.get(k, k)

            if key == "target_date" and isinstance(v, str):
                iso = self._normalize_date_to_iso(v)
                if iso:
                    normalized[key] = iso
                continue

            if key == "time" and isinstance(v, str):
                hhmm = self._normalize_time(v)
                if hhmm:
                    normalized[key] = hhmm
                continue

            if key == "duration_minutes":
                try:
                    normalized[key] = int(re.sub(r"\D", "", str(v)))
                except (ValueError, TypeError):
                    pass
                continue

            normalized[key] = v
        return normalized

    def _normalize_date_to_iso(self, value: str) -> Optional[str]:
        """Convertit une date naturelle ('demain', 'lundi', '01/01/2026') en ISO."""
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            pass
        try:
            import dateparser
            parsed = dateparser.parse(
                value, languages=["fr"],
                settings={"PREFER_DATES_FROM": "future"},
            )
            if parsed:
                return parsed.date().isoformat()
        except Exception as e:
            logger.warning("Normalisation date LLM échouée ('%s'): %s", value, e)
        return None

    def _normalize_time(self, value: str) -> Optional[str]:
        """Normalise une heure ('10h', '14:30', '9 h 15') au format HH:MM."""
        m = re.search(r"(\d{1,2})\s*[h:]\s*(\d{0,2})", value)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
        return None

    def _fill_structured_gaps(self, entities: dict, message: str) -> None:
        """
        Complète les entités structurées manquantes via le parser regex
        déterministe (qui produit déjà le bon schéma : target_date ISO,
        time HH:MM, duration_minutes int, tooth_number, patient_id).
        Ne remplit que les trous — les valeurs LLM déjà présentes priment.
        """
        try:
            regex_entities = self.fallback_parser.parse(message).entities
        except Exception as e:
            logger.warning("Gap-fill regex indisponible: %s", e)
            return
        for field in ("target_date", "time", "duration_minutes", "tooth_number", "patient_id"):
            if field not in entities and field in regex_entities:
                entities[field] = regex_entities[field]


llm_parser = LLMIntentParser()
