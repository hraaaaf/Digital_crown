"""Garde-fous de cohérence visuelle pour les documents générés (ReportLab).

Ce module N'EST PAS un moteur de mise en page alternatif — il ne remplace ni
get_adaptive_font_size(), ni get_document_margins(), ni le système de
compression single-page-force existant. Il fournit uniquement de petits
utilitaires additifs que les générateurs peuvent appliquer sur les textes
qu'ils composent, pour éviter les ruptures visuelles absurdes (ex: "33 ans"
coupé en deux lignes) sans jamais tronquer de donnée clinique ni imposer une
grille rigide.
"""
import re

from backend.services.generators.document_typography import MIN_READABLE_SIZE

# Unités/mots courts qui ne doivent jamais être séparés du nombre qui les
# précède par un retour à la ligne (ex: "33 ans", "200 mg", "3 jours").
_UNBREAKABLE_UNITS = (
    "ans", "an", "mg", "g", "ml", "kg", "cm", "mm",
    "j", "jour", "jours", "semaine", "semaines", "mois", "%",
)

_UNIT_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s+(" + "|".join(re.escape(u) for u in _UNBREAKABLE_UNITS) + r")\b",
    re.IGNORECASE,
)


def protect_unit_patterns(text: str) -> str:
    """Insère une espace insécable entre un nombre et l'unité qui le suit
    (33 ans, 200 mg, 3 jours...) pour empêcher un retour à la ligne isolé au
    milieu d'un groupe qui doit rester ensemble.

    N'altère jamais le contenu — seulement le caractère d'espacement entre
    le nombre et l'unité. Sûr à appliquer sur du texte déjà composé
    (paragraphes libres, posologie utilisateur, etc.).
    """
    if not text:
        return text
    return _UNIT_PATTERN.sub(lambda m: f"{m.group(1)} {m.group(2)}", text)


def join_unbreakable(*parts, sep: str = " ") -> str:
    """Joint des fragments avec une espace insécable — pour construire à la
    source un groupe qui ne doit jamais être coupé (ex: nom + ", " + âge +
    " ans"). Préférer cette fonction à protect_unit_patterns() quand on
    compose le texte soi-même (contrôle exact des points de jointure).
    """
    return sep.join(str(p) for p in parts if p is not None and str(p) != "")


def assert_min_readable(font_sizes) -> bool:
    """Vrai si toutes les tailles de police fournies respectent MIN_READABLE_SIZE.
    Utilitaire pour les tests — ne modifie rien, ne fait que vérifier.
    """
    return all(fs >= MIN_READABLE_SIZE for fs in font_sizes)
