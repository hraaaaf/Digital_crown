from __future__ import annotations

from typing import Any


def is_devis_phase_presentation_row(item: Any) -> bool:
    """Return True only for legacy visual phase separators.

    P3 historically encoded headings such as ``--- PHASE 1 ---`` as zero-value
    financial rows. They are presentation metadata, never billable Devis items.
    """
    if not isinstance(item, dict):
        return False
    acte = str(item.get("acte") or "").strip()
    return acte.startswith("--- ") and acte.endswith(" ---")


def _normalize_structured_dents(item: Any) -> Any:
    """Canonicalize structured FDI values without mutating the caller's row."""
    if not isinstance(item, dict) or not isinstance(item.get("dents"), list):
        return item

    normalized: list[int] = []
    for value in item["dents"]:
        try:
            tooth = int(value)
        except (TypeError, ValueError):
            # DevisItem owns validation/error reporting for malformed FDI values.
            return item
        normalized.append(tooth)

    canonical = sorted(set(normalized))
    if canonical == item["dents"]:
        return item

    cloned = dict(item)
    cloned["dents"] = canonical
    return cloned


def strip_devis_phase_presentation_rows(items: list[Any] | None) -> list[Any]:
    """Remove legacy phase separators and canonicalize structured tooth lists."""
    return [
        _normalize_structured_dents(item)
        for item in (items or [])
        if not is_devis_phase_presentation_row(item)
    ]
