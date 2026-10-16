"""Read-only, tenant-scoped patient selector for flagged Crown Bot preview.

Searches by internal ID, exact dossier number, or exact first/last name.
Never creates clinical actions or performs a tenant-global patient lookup.
"""
from __future__ import annotations

import re

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend import models

MAX_CHOICES = 5
_PREFIX = re.compile(r"^(id|dossier)\s*[:#]\s*(.+)$", re.I)
_HONORIFIC = re.compile(
    r"^(?:(?:mme|madame|mlle|mademoiselle|m|monsieur|mr|dr|docteur)\.?\s+)+",
    re.I,
)
_ID = re.compile(r"[1-9][0-9]{0,9}")


def lookup_patient_candidates(
    db: Session, *, employer_id: int, selector: str
) -> tuple[list[models.Patient], bool]:
    """Return at most MAX_CHOICES scoped candidates, plus overflow indicator.

    A purely numeric query checks BOTH dossier and internal ID. Distinct matches
    require explicit selection, never silently prefer an unrelated patient.
    'id:123' and 'dossier:123' disambiguate. Non-numeric dossiers are exact
    matches; names are exact full/first/surname matches, not fuzzy guesses.
    """
    if not isinstance(selector, str) or not 1 <= len(selector.strip()) <= 80:
        return [], False
    raw = " ".join(selector.strip().split())
    if any(ord(c) < 32 for c in raw):
        return [], False
    explicit = None
    m = _PREFIX.fullmatch(raw)
    if m:
        explicit, raw = m.group(1).lower(), m.group(2).strip()
    if not raw or len(raw) > 80:
        return [], False
    if explicit == "id" and not _ID.fullmatch(raw):
        return [], False

    base = db.query(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Patient.deleted_at.is_(None),
    )
    by_id = bool(_ID.fullmatch(raw)) and explicit != "dossier"
    by_dossier = explicit != "id"
    by_name = explicit is None and not raw.isdecimal()
    # All numeric identifiers are resolved against both ID and dossier fields.
    candidates: dict[int, models.Patient] = {}

    if by_id:
        patient = base.filter(models.Patient.id == int(raw)).first()
        if patient:
            candidates[patient.id] = patient
    if by_dossier:
        for patient in base.filter(
            func.lower(models.Patient.numero_dossier) == raw.lower()
        ).limit(MAX_CHOICES + 1):
            candidates[patient.id] = patient

    if by_name:
        normalized = _HONORIFIC.sub("", raw).strip().lower()
        if normalized:
            full = func.lower(func.trim(models.Patient.prenom + " " + models.Patient.nom))
            reverse = func.lower(func.trim(models.Patient.nom + " " + models.Patient.prenom))
            for patient in base.filter(or_(
                func.lower(models.Patient.nom) == normalized,
                func.lower(models.Patient.prenom) == normalized,
                full == normalized,
                reverse == normalized,
            )).limit(MAX_CHOICES + 1):
                candidates[patient.id] = patient

    sorted_candidates = sorted(candidates.values(), key=lambda p: p.id)
    return sorted_candidates[:MAX_CHOICES], len(sorted_candidates) > MAX_CHOICES
