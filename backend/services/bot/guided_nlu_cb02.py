"""CB-02 guided French NLU: deterministic, preview-only, pure and tenant-agnostic.

Source-only phase: NOT wired to FastAPI, ActionDispatcher, staff UI or a database.
The owner/tenant-bound server must authenticate, authorize and disambiguate
the patient before any canonical read or action.  No LLM, action ID or writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import re
import unicodedata

INTENTS = ("AGENDA_READ", "PATIENT_LOOKUP", "RDV_PREPARE")
QUESTIONS = {
    "patient": "Quel patient ? Précisez un nom ou numéro de dossier.",
    "date": "Quelle date ? Dites aujourd'hui, demain ou AAAA-MM-JJ.",
    "time": "À quelle heure ? Indiquez HH:MM ou 10h30.",
    "motif": "Quel motif : contrôle, consultation ou détartrage ?",
}
MOTIFS = {"controle": "CONTROLE", "consultation": "CONSULTATION",
          "detartrage": "DETARTRAGE"}
STOP_NAME = {
    "demain", "aujourd", "aujourdhui", "apres", "le", "la", "pour", "avec",
    "a", "vers", "et", "rdv", "rendez", "controle", "consultation",
    "detartrage", "lundi", "mardi", "mercredi", "jeudi", "vendredi",
    "samedi", "dimanche", "puis", "maintenant", "svp",
}
BLOCKED = re.compile(
    r"\b(?:confirme(?:r|z)?|execute(?:r|z)?|enregistre(?:r|z)?|"
    r"supprime(?:r|z)?|efface(?:r|z)?|annul\w*|valid\w*|"
    r"reserv\w*|sauvegard\w*|prescri(?:s|re)|ordonnance|"
    r"prescription|diagnostic|facture|paye(?:r|z)?|"
    r"ignore[rz]?|bypass|sans autorisation|autre cabinet)\b"
)
PERSON = re.compile(
    r"\b(?:mme|madame|monsieur|mr|m)\.?\s+"
    r"([a-z][a-z'-]{1,39}(?:\s+[a-z][a-z'-]{1,39})?)\b"
)
IDENTIFIER = re.compile(r"\b(?:patient|dossier)\s*(?:n[°o]\s*|#\s*|:\s*)?(\d{1,9})\b")
TIMES = re.compile(
    r"\b(?:(\d{1,2})\s*h\s*(\d{0,2})|(\d{1,2}):(\d{2}))\b"
)
ISO_DAY = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
REL_DAY = re.compile(r"\b(apres[\s-]*demain|demain|aujourd[' ]?hui)\b")
WEEK_DAY = re.compile(r"\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b")


@dataclass(frozen=True)
class GuidedResult:
    status: str
    intent: str | None = None
    fields: dict[str, dict[str, str]] = field(default_factory=dict)
    question: str | None = None
    reason: str | None = None
    bound_scope: str | None = None
    executable: bool = False


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold().replace("’", "'"))
    return re.sub(r"\s+", " ", "".join(
        char for char in value if not unicodedata.combining(char)
    ).replace("–", "-").replace("‑", "-")).strip()


def _field(value: str, source: str, detail: str) -> dict[str, str]:
    return {"value": value, "source": source, "rule": detail}


def _refuse(reason: str) -> GuidedResult:
    return GuidedResult(status="refused", reason=reason)


def _intent(text: str) -> str | None:
    rdv = bool(re.search(r"\b(?:prepar\w*|propos\w*|planifi\w*|prend\w*|"
                         r"prends|fixe\w*|cree\w*)\b", text)
               and re.search(r"\b(?:rdv|rendez[\s-]*vous|controle|consultation)\b", text))
    agenda = bool(re.search(r"\b(?:agenda|planning|programme|mes rdv|mes rendez[\s-]*vous)\b", text))
    # A patient selector inside a RDV draft is NOT a second "lookup" intent.
    # Conversely an explicit "find" command mixed with RDV/agenda is refused.
    find_verb = bool(re.search(r"\b(?:trouv\w*|cherch\w*|recherch\w*|"
                               r"retrouv\w*|fiche|ouvre)\b", text))
    patient_marker = bool(re.search(r"\b(?:mme|madame|monsieur|mr|patient|dossier)\b", text))
    lookup = patient_marker and (find_verb or
                                 (not rdv and not agenda and
                                  bool(re.search(r"\b(?:patient|dossier)\b", text))))
    matches = [name for name, yes in (
        ("RDV_PREPARE", rdv), ("AGENDA_READ", agenda), ("PATIENT_LOOKUP", lookup),
    ) if yes]
    return matches[0] if len(matches) == 1 else None


def _patient(text: str) -> tuple[str | None, str | None]:
    names = []
    for match in PERSON.finditer(text):
        words = match.group(1).split()
        if len(words) == 2 and words[1] in STOP_NAME:
            words.pop()
        names.append(" ".join(words))
    ids = IDENTIFIER.findall(text)
    identities = set(("name", n) for n in names) | set(("dossier", v) for v in ids)
    if len(identities) > 1:
        return None, "Identités patient contradictoires ou multiples."
    if not identities:
        return None, None
    kind, value = next(iter(identities))
    if kind == "dossier" and int(value) < 1:
        return None, "Identifiant patient invalide."
    return f"{kind}:{value}", None


def _day(text: str, today: date) -> tuple[str | None, str | None]:
    days = set()
    for match in ISO_DAY.finditer(text):
        try:
            days.add(date.fromisoformat(match.group()).isoformat())
        except ValueError:
            return None, "Date invalide."
    for match in REL_DAY.finditer(text):
        term = match.group()
        days.add((today + timedelta(days=2 if term.startswith("apres") else
                                    1 if term == "demain" else 0)).isoformat())
    if len(days) > 1:
        return None, "Dates contradictoires."
    if not days and WEEK_DAY.search(text):
        return None, "Jour de semaine ambigu sans date explicite."
    return next(iter(days)) if days else None, None


def _time(text: str) -> tuple[str | None, str | None]:
    hours = set()
    for match in TIMES.finditer(text):
        groups = match.groups()
        hour = int(groups[0] if groups[0] is not None else groups[2])
        minute = int((groups[1] or "00") if groups[0] is not None else groups[3])
        if hour > 23 or minute > 59:
            return None, "Heure invalide."
        hours.add(f"{hour:02d}:{minute:02d}")
    if len(hours) > 1:
        return None, "Heures contradictoires."
    if not hours and re.search(r"\b(?:matin|apres-midi|soir)\b", text):
        return None, "Plage horaire imprécise."
    return next(iter(hours)) if hours else None, None


def _finish(intent: str, fields: dict[str, dict[str, str]], scope: str, today: date) -> GuidedResult:
    required = {
        "AGENDA_READ": ("date",),
        "PATIENT_LOOKUP": ("patient",),
        "RDV_PREPARE": ("patient", "date", "time", "motif"),
    }[intent]
    for name in required:
        if name not in fields:
            return GuidedResult("clarification", intent, fields, QUESTIONS[name],
                                bound_scope=scope)
    if intent == "RDV_PREPARE" and fields["date"]["value"] < today.isoformat():
        return _refuse("Aucun rendez-vous passé n'est proposé.")
    # This is a CLIENT-INDEPENDENT syntax draft, NOT a permission check,
    # tenant lookup, a booked slot, an executable proposal, or a medical act.
    return GuidedResult("preview_only" if intent == "RDV_PREPARE"
                        else "requires_server_authorization", intent,
                        fields, bound_scope=scope)


def parse_guided_french(
    message: str, *, cabinet_today: date, principal_scope: str,
    previous: GuidedResult | None = None,
) -> GuidedResult:
    """Classify three explicit French workflows; never grant an action.

    The server must provide clinic-local today and a bound principal/tenant
    scope. Caller-supplied prior drafts are NOT authentication/authorization.
    """
    if not isinstance(cabinet_today, date) or isinstance(cabinet_today, __import__("datetime").datetime):
        return _refuse("Date de référence serveur requise.")
    if not isinstance(principal_scope, str) or not principal_scope.strip():
        return _refuse("Contexte principal/cabinet requis.")
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 160:
        return _refuse("Texte invalide ou trop long.")
    if any(ord(c) < 32 or ord(c) == 127 for c in message):
        return _refuse("Caractères de contrôle interdits.")
    text = _normalize(message)
    if BLOCKED.search(text) or re.search(r"\b(?:/bot/execute|action_id|pending_action_id)\b", text):
        return _refuse("Action directe ou commande hors périmètre CB-02.")

    correction = bool(re.search(r"\b(?:corrige|rectifie|change|remplace)\b", text))
    if correction:
        if (previous is None or previous.bound_scope != principal_scope or
                previous.intent != "RDV_PREPARE" or previous.status not in
                ("clarification", "preview_only")):
            return _refuse("Correction refusée : brouillon isolé absent.")
        changing_time = bool(re.search(r"\b(?:heure|horaire)\b", text))
        changing_date = bool(re.search(r"\bdate\b", text))
        if changing_time == changing_date:
            return _refuse("Précisez un seul champ à corriger : date ou heure.")
        value, error = (_time(text) if changing_time else _day(text, cabinet_today))
        if error or value is None:
            return _refuse(error or "Nouvelle valeur requise.")
        if changing_time and _day(text, cabinet_today)[0] is not None:
            return _refuse("Correction de deux champs refusée.")
        if changing_date and _time(text)[0] is not None:
            return _refuse("Correction de deux champs refusée.")
        # Carried patient text is still NOT a selected/authorized dossier.
        updated = {k: {**v, "source": ("carried_unverified_patient"
                                      if k == "patient" else "carried_prior_draft")}
                   for k, v in previous.fields.items()}
        key = "time" if changing_time else "date"
        updated[key] = _field(value, "explicit_correction", "CB02_CORRECTION")
        return _finish("RDV_PREPARE", updated, principal_scope, cabinet_today)

    intent = _intent(text)
    if not intent:
        return _refuse("Intention absente, mélangée ou non prise en charge.")
    patient, pe = _patient(text)
    target_day, de = _day(text, cabinet_today)
    clock, te = _time(text)
    if pe or de or te:
        return _refuse(pe or de or te or "Ambiguïté.")
    if intent == "AGENDA_READ" and (patient or clock):
        return _refuse("Agenda : patient ou heure non prévus dans ce contrat.")
    if intent == "PATIENT_LOOKUP" and (target_day or clock):
        return _refuse("Recherche patient : date et heure non prévues.")
    motifs = {value for key, value in MOTIFS.items()
              if re.search(r"\b" + re.escape(key) + r"\b", text)}
    if len(motifs) > 1:
        return _refuse("Motifs contradictoires.")
    if intent != "RDV_PREPARE" and motifs:
        return _refuse("Motif hors périmètre de lecture.")
    fields: dict[str, dict[str, str]] = {}
    if patient:
        fields["patient"] = _field(patient, "explicit_unverified",
                                    "SERVER_MUST_AUTHORIZE_DISAMBIGUATE")
    if target_day:
        fields["date"] = _field(target_day, "deterministic_relative_or_explicit",
                                 "CABINET_LOCAL_DAY")
    if clock:
        fields["time"] = _field(clock, "explicit", "STRICT_24H_TIME")
    if motifs:
        fields["motif"] = _field(next(iter(motifs)), "explicit", "MOTIF_WHITELIST")
    return _finish(intent, fields, principal_scope, cabinet_today)
