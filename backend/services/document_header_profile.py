"""Resolve document header lines from the cabinet's canonical specialty selection.

Historically ``specialty_ids`` and ``header_lines_fr/ar`` were persisted separately.
That allowed an upgraded cabinet to keep stale materialized header lines even after
all specialties were selected.  Documents must derive automatic headers from the
selection at render time, while explicit customized headers remain authoritative.
"""

from __future__ import annotations

from typing import Any


SPECIALTIES = (
    ("soins", "Soins", "علاج"),
    ("endo", "Endodontie", "علاج العصب"),
    ("paro", "Parodontologie", "أمراض اللثة"),
    ("ortho", "Orthodontie", "تقويم الأسنان"),
    ("prothese", "Prothèse", "تعويض الأسنان"),
    ("chirurgie", "Chirurgie", "جراحة"),
    ("implant", "Implantologie", "زراعة الأسنان"),
    ("blanchiment", "Blanchiment", "تبييض الأسنان"),
    ("esthetique", "Esthétique", "تجميل الأسنان"),
)


def _raw(config: Any, key: str, default=None):
    if config is None:
        return default
    if isinstance(config, dict):
        value = config.get(key, default)
    else:
        value = getattr(config, key, default)
    return default if value is None else value


def _clean(lines) -> list[str]:
    return [str(line).strip() for line in (lines or []) if str(line or "").strip()]


def _doctor_fr(config, stored: list[str]) -> str:
    if stored:
        return stored[0]
    name = str(_raw(config, "nom_praticien", "") or "").strip()
    if not name:
        return "Dr."
    prefixes = ("Dr.", "Dr ", "Pr.", "Pr ", "Docteur", "Professeur")
    return name if name.startswith(prefixes) else f"Dr. {name}"


def _doctor_ar(config, stored: list[str]) -> str:
    if stored:
        return stored[0]
    name = str(_raw(config, "nom_praticien_ar", "") or "").strip()
    if not name:
        return "د."
    if name.endswith(" .د") or name.startswith("د."):
        return name
    return f"{name} .د"


def _pair(values: list[str], *, reverse: bool = False) -> list[str]:
    rows: list[str] = []
    for index in range(0, len(values), 2):
        pair = values[index:index + 2]
        if reverse:
            pair = list(reversed(pair))
        rows.append(" - ".join(pair))
    return rows


def resolve_header_lines(config: Any, key: str, stored_value=None):
    """Return effective FR/AR header lines for a document render.

    Rules:
    - customized headers remain exactly as persisted;
    - automatic headers are regenerated from ``specialty_ids`` when that source
      contains at least one recognized specialty (or a custom specialty exists);
    - legacy cabinets with no specialty source keep their persisted lines unchanged.
    """
    if key not in {"header_lines_fr", "header_lines_ar"}:
        return stored_value

    stored_fr = _clean(_raw(config, "header_lines_fr", []))
    stored_ar = _clean(_raw(config, "header_lines_ar", []))
    if bool(_raw(config, "header_customized", False)):
        return stored_fr if key == "header_lines_fr" else stored_ar

    selected_ids = set(_raw(config, "specialty_ids", []) or [])
    selected = [entry for entry in SPECIALTIES if entry[0] in selected_ids]
    custom_fr = str(_raw(config, "custom_specialty_fr", "") or "").strip()
    custom_ar = str(_raw(config, "custom_specialty_ar", "") or "").strip()

    if not selected and not custom_fr and not custom_ar:
        return stored_fr if key == "header_lines_fr" else stored_ar

    fr_specialties = [entry[1] for entry in selected]
    ar_specialties = [entry[2] for entry in selected]
    if custom_fr:
        fr_specialties.append(custom_fr)
    if custom_ar:
        ar_specialties.append(custom_ar)

    fr_lines = [_doctor_fr(config, stored_fr), "Chirurgien Dentiste", *_pair(fr_specialties)]
    ar_lines = [_doctor_ar(config, stored_ar), "طبيب جراح للأسنان", *_pair(ar_specialties, reverse=True)]

    return fr_lines[:7] if key == "header_lines_fr" else ar_lines[:7]
