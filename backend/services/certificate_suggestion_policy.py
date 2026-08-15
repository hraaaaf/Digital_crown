from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

SURGICAL_KEYWORDS = ("extraction", "chirurgie", "implant", "lambeau", "resection", "résection")
ORTHO_KEYWORDS = ("ortho", "bagues", "appareil", "ajustement")
APTITUDE_KEYWORDS = ("aptitude", "sport")


def certificate_same_day_bounds(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def build_certificate_context_signal(motif_text: str, *, has_same_day_visit: bool) -> Optional[dict]:
    motif = (motif_text or "").strip().lower()
    if not has_same_day_visit or not motif:
        return None

    if any(keyword in motif for keyword in APTITUDE_KEYWORDS):
        # A motif alone is insufficient evidence to suggest a fitness certificate.
        return None

    if any(keyword in motif for keyword in SURGICAL_KEYWORDS):
        return {
            "type": "Arrêt de travail",
            "confidence": "context",
            "reason": "Acte chirurgical réalisé aujourd’hui. Évaluer si un repos est nécessaire ; type et durée restent à déterminer par le praticien.",
        }

    if any(keyword in motif for keyword in ORTHO_KEYWORDS):
        return {
            "type": "Certificat de Présence",
            "confidence": "context",
            "reason": "Passage orthodontique détecté aujourd’hui. Une attestation de présence peut être envisagée si elle est demandée par le patient.",
        }

    return {
        "type": "Certificat de Présence",
        "confidence": "context",
        "reason": "Passage au cabinet détecté aujourd’hui. Une attestation de présence peut être envisagée si elle est demandée par le patient.",
    }
