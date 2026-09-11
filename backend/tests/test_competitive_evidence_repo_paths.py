from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAPABILITIES = ROOT / "docs" / "competitive" / "capabilities.json"


def test_all_competitive_repo_evidence_paths_exist() -> None:
    payload = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    missing: list[str] = []

    for capability in payload["capabilities"]:
        for side in ("digital_crown", "orthalis"):
            for evidence in capability[side]["evidence"]:
                if evidence["type"] != "repo_path":
                    continue
                path = evidence["path"]
                if not (ROOT / path).exists():
                    missing.append(f"{capability['id']}:{side}:{path}")

    assert missing == [], "stale competitive evidence paths: " + ", ".join(missing)
