# Configuration des intents pour le Bot
# Extrait du fichier intent_parser.py pour faciliter la maintenance (Clean Architecture)

from typing import List, Tuple

INTENT_PATTERNS: List[Tuple[str, List[str], float]] = [
    # (intent_name, keywords, base_confidence)

    # --- QUERIES (lecture) ---
    ("QUERY_PATIENT", [
        "info", "informations", "dossier", "fiche", "détails", "details",
        "antécédent", "antecedent", "historique patient"
    ], 0.85),

    ("QUERY_AGENDA", [
        "agenda", "planning", "rdv", "rendez-vous", "rendezvous",
        "programme", "emploi du temps", "schedule"
    ], 0.85),

    ("QUERY_FINANCE", [
        "chiffre", "recette", "revenu", "finance", "comptabilité",
        "comptabilite", "ca", "argent", "paiement", "impayé", "impaye",
        "dette", "créance", "creance", "combien"
    ], 0.80),

    ("QUERY_LAB", [
        "labo", "laboratoire", "travaux", "prothèse labo",
        "envoi labo", "lab job", "lab"
    ], 0.85),

    ("QUERY_STATS", [
        "statistique", "stats", "taux", "conversion", "projection",
        "forecast", "prévision", "prevision", "assurance", "distribution"
    ], 0.80),

    ("QUERY_ALERTS", [
        "alerte", "notification", "risque", "attention",
        "patient à risque", "briefing"
    ], 0.85),

    # --- ACTIONS (écriture) ---
    ("CREATE_APPOINTMENT", [
        "prends rdv", "prendre rdv", "ajouter rdv", "créer rdv",
        "creer rdv", "nouveau rdv", "planifier", "réserver",
        "book", "nouveau rendez-vous", "ajouter rendez"
    ], 0.90),

    ("CREATE_PRESCRIPTION", [
        "ordonnance", "prescrire", "prescription",
        "post-extraction", "post extraction", "antibiotique",
        "antalgique", "médicament"
    ], 0.85),

    ("CREATE_DEVIS", [
        "devis", "estimation", "chiffrer", "quote",
        "cout", "coût", "prix", "tarif"
    ], 0.85),

    ("SEARCH_PATIENT", [
        "cherche", "recherche", "trouve", "trouver",
        "search", "find", "qui s'appelle"
    ], 0.80),

    ("CHANGE_STATUS", [
        "marquer", "statut", "terminer", "annuler",
        "en cours", "terminé", "commence"
    ], 0.75),

    ("HELP", [
        "aide", "help", "que sais-tu", "que peux-tu",
        "comment", "quoi faire", "fonctionnalité", "capability"
    ], 0.95),
]
