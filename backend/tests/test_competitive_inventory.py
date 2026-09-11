from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs" / "competitive" / "digital_crown_inventory.json"


def test_competitive_inventory_is_unique_and_resolvable() -> None:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert payload["scope"] == "benchmark_relevant_surface_inventory"
    assert len(payload["baseline_ref"]) == 40

    ids: set[str] = set()
    missing: list[str] = []
    for item in payload["items"]:
        assert item["id"] not in ids
        ids.add(item["id"])
        if not (ROOT / item["path"]).exists():
            missing.append(item["path"])

    assert len(ids) == 23
    assert missing == [], "missing benchmark inventory paths: " + ", ".join(missing)
