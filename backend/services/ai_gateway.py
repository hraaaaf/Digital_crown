"""
AI Gateway — point de contrôle UNIQUE des sorties LLM (S4).

Principe : LOCAL-FIRST. Par défaut toute l'IA tourne en local (Ollama). Aucun
appel vers un fournisseur cloud n'est autorisé tant que CLOUD_AI_ENABLED est
False (opt-in EXPLICITE du cabinet — cf. S3, capsule IA confinée). Ce module est
le seul endroit où la politique d'egress IA est décidée, afin qu'elle soit
auditable d'un coup d'œil.
"""
import logging
from urllib.parse import urlparse

from backend.config import settings

logger = logging.getLogger(__name__)

# Endpoint local canonique (Ollama exposant une API compatible OpenAI sur /v1).
LOCAL_LLM_BASE = f"{settings.OLLAMA_URL.rstrip('/')}/v1"

# Hôtes considérés comme « dans le cabinet » (loopback).
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def cloud_ai_allowed() -> bool:
    """True seulement si le cabinet a EXPLICITEMENT activé la sortie cloud."""
    return bool(getattr(settings, "CLOUD_AI_ENABLED", False))


def is_local_endpoint(url: str) -> bool:
    """True si l'URL pointe vers le loopback ou une IP LAN privée (RFC1918)."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if host in _LOCAL_HOSTS:
        return True
    return (
        host.startswith("10.")
        or host.startswith("192.168.")
        or host.startswith("169.254.")
        or any(host.startswith(f"172.{i}.") for i in range(16, 32))
        or host.endswith(".local")
    )


def resolve_llm_base(requested: str) -> str:
    """
    Résout l'URL de base LLM en respectant la politique local-first.

    - Endpoint local (loopback/LAN) → autorisé tel quel.
    - Endpoint distant + CLOUD_AI_ENABLED=True → autorisé (opt-in cabinet).
    - Endpoint distant + CLOUD_AI_ENABLED=False → REFUSÉ, repli FORCÉ sur le
      local. Aucune donnée ne quitte le cabinet sans opt-in explicite.
    """
    requested = (requested or "").rstrip("/")
    if not requested:
        return LOCAL_LLM_BASE
    if is_local_endpoint(requested):
        return requested
    if cloud_ai_allowed():
        logger.info(
            "AI Gateway: endpoint LLM cloud autorisé (opt-in) : %s",
            urlparse(requested).hostname,
        )
        return requested
    logger.warning(
        "AI Gateway: endpoint LLM distant '%s' BLOQUÉ (CLOUD_AI_ENABLED=False). "
        "Repli local-first sur %s. Aucune donnée envoyée hors cabinet.",
        urlparse(requested).hostname,
        LOCAL_LLM_BASE,
    )
    return LOCAL_LLM_BASE
