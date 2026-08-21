"""Source-of-truth helpers shared by connected clinical catalog flows."""

from __future__ import annotations

from typing import Any, Iterable


def flatten_catalog_acts(catalog: Iterable[dict[str, Any]], query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    """Flatten active tenant catalog acts while preserving the legacy public shape.

    The caller must load exactly one cabinet's R6 catalog. No global/legacy catalog
    fallback is performed here. Extra ``catalog_act_id`` and ``code`` fields are
    additive; existing consumers keep receiving id/name/base_price/category/is_habit.
    """
    needle = query.strip().casefold()
    results: list[dict[str, Any]] = []

    for specialty in catalog:
        specialty_name = str(specialty.get("name") or "").strip() or "Général"
        for act in specialty.get("acts") or []:
            if act.get("is_active") is False:
                continue
            name = str(act.get("name") or "").strip()
            if not name:
                continue
            code = str(act.get("code") or "").strip() or None
            haystack = " ".join(part for part in (name, code or "", specialty_name) if part).casefold()
            if needle and needle not in haystack:
                continue
            act_id = int(act["id"])
            price = float(act.get("base_price") or 0.0)
            results.append(
                {
                    "id": f"cat_{act_id}",
                    "catalog_act_id": act_id,
                    "name": name,
                    "code": code,
                    "base_price": price,
                    "price": price,
                    "category": specialty_name,
                    "is_habit": False,
                }
            )
            if len(results) >= max(1, limit):
                return results

    return results
