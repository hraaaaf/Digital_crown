"""Isolated ZERO-LLM Crown Bot proof-of-concept.

No FastAPI route, DB access, patient lookup, clinical decision or action execution.
The caller must authenticate, authorize, resolve records and revalidate actions.
"""

from dataclasses import dataclass, field
from datetime import date
import re
from typing import Any, Dict, Optional


PROCEDURES = {
    "consultation": "CONSULTATION",
    "detartrage": "DETARTRAGE",
    "détartrage": "DETARTRAGE",
    "couronne": "COURONNE",
}
DURATIONS = {"15", "30", "45", "60"}
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIME_RE = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
PATIENT_ID_RE = re.compile(r"[1-9][0-9]{0,9}")


@dataclass(frozen=True)
class PocTurn:
    status: str
    message: str
    proposal: Optional[Dict[str, Any]] = None


@dataclass
class PocConversation:
    """One in-memory interaction, intentionally never authoritative."""

    today: date
    state: str = "idle"
    workflow: Optional[str] = None
    slots: Dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        self.state = "idle"
        self.workflow = None
        self.slots = {}

    def handle(self, text: str) -> PocTurn:
        message = text.strip() if isinstance(text, str) else ""
        normalized = message.casefold()

        if normalized in {"/annuler", "/cancel"}:
            self.reset()
            return PocTurn("cancelled", "Demande annulée. Aucune action effectuée.")

        if self.state == "idle":
            return self._start(normalized)

        if self.state == "patient":
            if not PATIENT_ID_RE.fullmatch(message):
                return PocTurn("clarification", "Indiquez un identifiant patient numérique valide, sans nom.")
            self.slots["patient_id"] = int(message)
            if self.workflow == "patient":
                result = {
                    "type": "QUERY_PATIENT",
                    "params": {"patient_id": self.slots["patient_id"]},
                }
                self.reset()
                return PocTurn("read_request", "Recherche à autoriser côté serveur.", result)
            if self.workflow == "rdv":
                self.state = "date"
                return PocTurn("clarification", "Date du rendez-vous au format AAAA-MM-JJ ?")
            self.state = "procedure"
            return PocTurn("clarification", "Acte : consultation, détartrage ou couronne ?")

        if self.state == "date":
            if not DATE_RE.fullmatch(message):
                return PocTurn("clarification", "Date requise : AAAA-MM-JJ.")
            try:
                wanted = date.fromisoformat(message)
            except ValueError:
                return PocTurn("clarification", "Date invalide. Réessayez au format AAAA-MM-JJ.")
            if wanted < self.today:
                return PocTurn("clarification", "La date ne peut pas être passée.")
            self.slots["target_date"] = wanted.isoformat()
            self.state = "time"
            return PocTurn("clarification", "Heure du rendez-vous au format HH:MM (24 h) ?")

        if self.state == "time":
            if not TIME_RE.fullmatch(message):
                return PocTurn("clarification", "Heure invalide. Exemple : 14:30.")
            self.slots["time"] = message
            self.state = "duration"
            return PocTurn("clarification", "Durée : 15, 30, 45 ou 60 minutes ?")

        if self.state == "duration":
            if message not in DURATIONS:
                return PocTurn("clarification", "Choisissez 15, 30, 45 ou 60 minutes.")
            self.slots["duration_minutes"] = int(message)
            self.state = "motif"
            return PocTurn("clarification", "Motif : consultation, détartrage ou couronne ?")

        if self.state == "motif":
            code = PROCEDURES.get(normalized)
            if code is None:
                return PocTurn("clarification", "Motif requis : consultation, détartrage ou couronne.")
            self.slots["motif"] = code
            self.state = "confirm"
            return PocTurn(
                "confirmation_required",
                "Proposition : patient #"
                f"{self.slots['patient_id']}, {self.slots['target_date']} "
                f"{self.slots['time']} ({self.slots['duration_minutes']} min), "
                f"motif {code}. Tapez CONFIRMER ou /annuler.",
            )

        if self.state == "procedure":
            code = PROCEDURES.get(normalized)
            if code is None:
                return PocTurn("clarification", "Acte non reconnu : consultation, détartrage ou couronne.")
            self.slots["procedure"] = code
            self.state = "confirm"
            return PocTurn(
                "confirmation_required",
                f"Devis en brouillon : patient #{self.slots['patient_id']}, "
                f"acte {code}. Tapez CONFIRMER ou /annuler.",
            )

        if self.state == "confirm":
            if normalized != "confirmer":
                return PocTurn("confirmation_required", "Seul CONFIRMER prépare l'action, sinon /annuler.")
            if self.workflow == "rdv":
                result = {
                    "type": "CREATE_APPOINTMENT",
                    "params": {
                        "patient_id": self.slots["patient_id"],
                        "datetime_start": (
                            f"{self.slots['target_date']}T{self.slots['time']}:00"
                        ),
                        "duration_minutes": self.slots["duration_minutes"],
                        "motif": self.slots["motif"],
                    },
                }
            else:
                result = {
                    "type": "OPEN_DEVIS_EDITOR",
                    "params": {
                        "patient_id": self.slots["patient_id"],
                        "procedure": self.slots["procedure"],
                        "draft_only": True,
                    },
                }
            self.reset()
            return PocTurn(
                "proposal_only",
                "Proposition construite, NON exécutée. "
                "Autorisation, contrôle métier, action ID et confirmation serveur requis.",
                result,
            )

        self.reset()
        return PocTurn("error", "État inconnu. Session réinitialisée.")

    def _start(self, command: str) -> PocTurn:
        workflows = {
            "/patient": "patient",
            "/rdv": "rdv",
            "/devis": "devis",
        }
        if command not in workflows:
            return PocTurn(
                "help",
                "Commandes exactes : /patient, /rdv, /devis. "
                "Annulation à tout moment : /annuler.",
            )
        self.workflow = workflows[command]
        self.state = "patient"
        return PocTurn(
            "clarification",
            "Identifiant numérique du patient ? "
            "La sélection et les droits devront être vérifiés côté serveur.",
        )
