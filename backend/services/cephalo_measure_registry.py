"""
Source unique de vérité pour les unités des métriques céphalo.

Importer ici plutôt que de dupliquer la logique dans le générateur PDF
et le validateur de cohérence.
"""
from __future__ import annotations

# Mots-clés dont la présence dans un nom de métrique indique une mesure en mm.
# Toutes les autres métriques céphalo sont en degrés (°).
MM_KEYWORDS: tuple[str, ...] = (
    "Ligne", "Surplomb", "Recouvrement", "Decalage", "Décalage",
    "Situation", "Profondeur", "I_NA_mm", "I_NB_mm", "Wits",
    "Longueur", "Differentiel", "Etage",
)

_MM_KEYWORDS_LOWER: tuple[str, ...] = tuple(k.lower() for k in MM_KEYWORDS)


def is_mm_metric(name: str) -> bool:
    """Retourne True si le nom de métrique implique une mesure linéaire (mm)."""
    n = name.lower()
    return any(kw in n for kw in _MM_KEYWORDS_LOWER)


def cephalo_unit(metric_name: str) -> str:
    """Retourne 'mm' ou '°' selon le nom de la métrique."""
    return "mm" if is_mm_metric(metric_name) else "°"
