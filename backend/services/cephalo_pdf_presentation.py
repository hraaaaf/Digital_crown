"""A display-only French layer; original scientific states stay in the projection.

Unknown machine codes remain fail-closed and are NOT treated as validated.
"""
from __future__ import annotations
import re

STATES = {
    "AVAILABLE": "Mesure disponible (non validée cliniquement)",
    "NOT_COMPUTABLE": "Non calculable avec les données disponibles",
    "INCOMPLETE": "Incomplet",
    "COMPLETE": "Complet sur le plan documentaire (sans validation clinique implicite)",
    "BLOCKED": "Validation en attente",
    "HOLD": "En attente de vérification",
    "SATISFIED": "Référence documentée",
    "VERIFIED": "Vérifié",
    "NON VERIFIED": "Non vérifié",
    "NOT_VERIFIED": "Non vérifié",
    "EVALUABLE": "Évaluation possible (sans sélection)",
    "DROPPED": "Écarté du processus",
    "RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY": "Mesure brute — références uniquement contextuelles",
    "CONTEXT_ONLY_NO_RUNTIME_DELTA": "Référence historique sans écart comparatif validé",
    "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO": "Données techniques tracées dans le dossier",
    "EVIDENCE_GRAPH_V1": "Source documentée dans le dossier",
    "CEPHALO_PDF_PROJECTION_V1": "Données scientifiques tracées",
}
EXPLANATIONS = {
    "diagnostic_rule_registry_empty": "Le référentiel de diagnostic n'est pas disponible.",
    "r14_authoritative_snapshot_not_persisted": "La validation finale du praticien n'est pas enregistrée.",
    "r11_provenance_missing": "La traçabilité des éléments scientifiques est incomplète.",
    "authoritative_pdf_projection_missing": "Les données scientifiques nécessaires au bilan sont indisponibles.",
    "R14 NO VERIFIED PRACTITIONER SNAPSHOT": "La validation finale du praticien n'est pas confirmée.",
}

def clinical_term(value, fallback="Vérification nécessaire") -> str:
    """A practitioner label, never an invented interpretation."""
    if value is None or str(value).strip() == "":
        return fallback
    text = str(value).strip()
    if text in EXPLANATIONS:
        return EXPLANATIONS[text]
    if text in STATES:
        return STATES[text]
    # Machine identifiers, stage references, source-lock and similar artifacts
    # are omitted from the patient-facing document, not from the evidence graph.
    if ("_" in text or re.search(r"\bR1[1-4]\b|source-lock|\b[A-Z]+_[A-Z0-9_]+\b", text, re.I)
            or re.fullmatch(r"[A-Z0-9]+(?:_[A-Z0-9]+)+", text)):
        return fallback
    return text

def measurement_value(value, status) -> str:
    if status != "AVAILABLE" or str(value).strip() in ("NOT_COMPUTABLE", "None", "", "-"):
        return "Non calculable"
    return str(value)

def practitioner_stage(stage, index: int) -> str:
    title = clinical_term(stage.get("title"), "Étape de validation clinique")
    return f"Étape {index} — {title}"
