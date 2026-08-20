"""Source-of-truth helpers shared by connected clinical catalog flows."""

from __future__ import annotations

from typing import Any, Iterable


def flatten_catalog_acts(catalog: Iterable[dict[str, Any]], query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    """Flatten active tenant catalog acts while preserving the public search contract.

    The caller is responsible for loading the catalog for exactly one tenant.
    No legacy/global fallback is performed here.
    """
    needle = query.strip().casefold()
    results: list[dict[str, Any]] = []

    for specialty in catalog:
        if specialty.get("is_active") is False:
            continue
        specialty_name = str(specialty.get("name") or "").strip()
        for act in specialty.get("acts") or []:
            if act.get("is_active") is False:
                continue
            name = str(act.get("name") or "").strip()
            code = str(act.get("code") or "").strip() or None
            haystack = " ".join(part for part in (name, code or "", specialty_name) if part).casefold()
            if needle and needle not in haystack:
                continue
            results.append(
                {
                    "id": int(act["id"]),
                    "name": name,
                    "code": code,
                    "price": float(act.get("base_price") or 0.0),
                }
            )
            if len(results) >= max(1, limit):
                return results

    return results
