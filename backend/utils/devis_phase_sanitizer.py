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


def strip_devis_phase_presentation_rows(items: list[Any] | None) -> list[Any]:
    """Remove legacy phase separators while preserving real quote rows verbatim."""
    return [item for item in (items or []) if not is_devis_phase_presentation_row(item)]
