"""Formatting-only parser for practitioner-authored panoramic report prose.

The parser never infers radiographic findings, normality, diagnoses or acts.
It preserves bullet AND paragraph content from stored markdown, including
free-text clinical questions and conclusions, for PDF presentation.
"""
from __future__ import annotations

import re
from typing import Dict, List

_HEADING = re.compile(r"^\s{0,3}#{1,4}\s+(.+?)\s*$")
_BULLET = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")
_RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")


def _plain_markdown_inline(value: str) -> str:
    """Remove only presentational bold markers; escape HTML in Jinja later."""
    return _BOLD.sub(lambda match: match.group(1) or match.group(2), value.strip())


def _kind(title: str) -> str:
    folded = title.strip().upper()
    if folded in {"QUESTION CLINIQUE", "INDICATION", "INDICATION CLINIQUE", "MOTIF"}:
        return "indication"
    if folded in {"TECHNIQUE", "QUALITÉ", "QUALITE", "TECHNIQUE ET QUALITÉ", "TECHNIQUE ET QUALITE"}:
        return "technique"
    if folded in {"RÉPONSE À LA QUESTION CLINIQUE", "REPONSE A LA QUESTION CLINIQUE"}:
        return "response"
    if folded in {"SYNTHÈSE", "SYNTHESE", "CONCLUSION"}:
        return "conclusion"
    return "observation"


def parse_panoramic_report(markdown: str | None) -> List[Dict]:
    """Return ordered sections with *every* substantive author-provided line.

    Existing deterministic report-engine headings map to their corresponding
    editorial PDF style; other headings are passed through unchanged.
    No default 'normal' finding or invented indication is ever inserted.
    """
    if not isinstance(markdown, str) or not markdown.strip():
        return [{
            "name": "Observations radiographiques",
            "kind": "observation",
            "findings": ["Aucune observation documentée ; bilan non conclu."],
        }]

    sections: List[Dict] = []
    current: Dict | None = None
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or _RULE.fullmatch(line):
            continue
        # Do not interpret raw HTML as markup; output will be escaped by
        # Jinja Environment(autoescape=True).
        heading = _HEADING.match(line)
        if heading:
            title = _plain_markdown_inline(heading.group(1))
            if not title:
                continue
            current = {"name": title, "kind": _kind(title), "findings": []}
            sections.append(current)
            continue

        bullet = _BULLET.match(line)
        item = _plain_markdown_inline(bullet.group(1) if bullet else line)
        if not item:
            continue
        if current is None:
            current = {
                "name": "Observations complémentaires",
                "kind": "observation",
                "findings": [],
            }
            sections.append(current)
        current["findings"].append(item)

    non_empty = [section for section in sections if section["findings"]]
    if non_empty:
        return non_empty
    return [{
        "name": "Observations radiographiques",
        "kind": "observation",
        "findings": ["Aucune observation documentée ; bilan non conclu."],
    }]
