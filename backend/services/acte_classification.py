"""
Classification d'un libellé de ligne facturée en ActeType — UNIFY-ACT-PERSISTENCE-1.

Fonction pure, réutilisable partout où un Acte est créé automatiquement à partir d'un
libellé texte libre (documents.py::generate_document). Généralise les listes de
mots-clés déjà présentes dans documents.py (suggestion RDV/radio, sémantique
différente, non touchées) plutôt que de les dupliquer une 3e fois.
"""
from backend import models

_PROTHESE_KEYWORDS = ['couronne', 'prothèse', 'prothese', 'bridge', 'implant', 'facette', 'inlay', 'onlay']
_ORTHO_CONTENTION_KEYWORDS = ['contention']
_ORTHO_SEMESTRE_KEYWORDS = ['ortho', 'semestr', 'bagues', 'appareil ortho']


def classify_acte_type(libelle: str) -> "models.ActeType":
    """Classifie un libellé en ActeType par heuristique de mots-clés.
    Limite connue : dépend de la formulation libre saisie par l'utilisateur — pas de
    garantie de correspondance exacte (cf. habits_engine.py qui a la même limite sur
    ses propres recherches ilike)."""
    if not libelle:
        return models.ActeType.SOIN
    lower = libelle.lower()
    if any(k in lower for k in _ORTHO_CONTENTION_KEYWORDS):
        return models.ActeType.ORTHO_CONTENTION
    if any(k in lower for k in _PROTHESE_KEYWORDS):
        return models.ActeType.PROTHESE
    if any(k in lower for k in _ORTHO_SEMESTRE_KEYWORDS):
        return models.ActeType.ORTHO_SEMESTRE
    return models.ActeType.SOIN
