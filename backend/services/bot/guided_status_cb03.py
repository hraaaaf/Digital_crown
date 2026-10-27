"""CB-03 G1-B deterministic, fail-closed status preparation grammar.

This grammar only recognizes an explicit request to PREPARE one status change.
Appointment ID is a separate explicit UI selection (never inferred by this parser).
No cloud NLU, free-form instruction, transition on confirmed appointment, or write.
"""
from __future__ import annotations

import re
import unicodedata

from backend.models import AppointmentStatus

# Small, deliberately explicit state graph. Frontdesk / patient confirmations
# are NOT in scope; neither is reactivation of terminal states.
ALLOWED_TRANSITIONS: dict[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.PREVU: frozenset({
        AppointmentStatus.EN_SALLE_ATTENTE,
        AppointmentStatus.ANNULE,
    }),
    AppointmentStatus.CONFIRME: frozenset({
        AppointmentStatus.EN_SALLE_ATTENTE,
        AppointmentStatus.ANNULE,
    }),
    AppointmentStatus.EN_SALLE_ATTENTE: frozenset({
        AppointmentStatus.EN_FAUTEUIL,
        AppointmentStatus.ANNULE,
    }),
    AppointmentStatus.EN_FAUTEUIL: frozenset({
        AppointmentStatus.TERMINE,
    }),
}

_STATUS_PHRASES: dict[str, AppointmentStatus] = {
    "salle d'attente": AppointmentStatus.EN_SALLE_ATTENTE,
    "salle attente": AppointmentStatus.EN_SALLE_ATTENTE,
    "attente": AppointmentStatus.EN_SALLE_ATTENTE,
    "fauteuil": AppointmentStatus.EN_FAUTEUIL,
    "termine": AppointmentStatus.TERMINE,
    "terminee": AppointmentStatus.TERMINE,
    "annule": AppointmentStatus.ANNULE,
    "annulee": AppointmentStatus.ANNULE,
}
_STATUS_LABELS: dict[AppointmentStatus, str] = {
    AppointmentStatus.EN_SALLE_ATTENTE: "En salle d'attente",
    AppointmentStatus.EN_FAUTEUIL: "En fauteuil",
    AppointmentStatus.TERMINE: "Terminé",
    AppointmentStatus.ANNULE: "Annulé",
}

# Only an anchored explicit preparation command; other intentions, pasted
# prompts, multiple statuses and unrecognized free text fail closed.
_PREPARE = re.compile(
    r"^prepare (?:le )?(?:changement de )?statut (?:du )?"
    r"(?:rdv|rendez vous) (?:en|a) ([a-z' ]+)$"
)


def parse_status_preparation(utterance: str) -> tuple[AppointmentStatus, str] | None:
    if (not isinstance(utterance, str) or
            not 1 <= len(utterance.strip()) <= 160 or
            any(ord(char) < 32 or ord(char) == 127 for char in utterance)):
        return None
    normalized = unicodedata.normalize("NFKD", utterance.casefold().replace("’", "'"))
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r"\s+", " ", normalized.replace("-", " ")).strip()
    match = _PREPARE.fullmatch(normalized)
    if not match:
        return None
    status = _STATUS_PHRASES.get(match.group(1).strip())
    return (status, _STATUS_LABELS[status]) if status is not None else None


def transition_allowed(current: AppointmentStatus, target: AppointmentStatus) -> bool:
    """Conservative G1-B policy, to be rechecked under G2's transaction."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())
