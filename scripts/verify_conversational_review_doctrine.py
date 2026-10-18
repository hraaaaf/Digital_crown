#!/usr/bin/env python3
"""GLOBAL-G10-S: check conversational A/B reviewer doctrine (not execution proof).

Designed for the existing manually dispatchable G0 Global Interactive Inventory
GitHub Actions workflow. It asserts canonical *written* rules, not that two
reviews, browser journeys, or physical tests actually occurred.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "agents": ROOT / "AGENTS.md",
    "rpg": ROOT / "docs/quality/REALITY_PROOF_GATE.md",
    "scoring": ROOT / ".claude/rules/execution-scoring-verification.md",
    "techdoubt": ROOT / "techdoubt.md",
}

REQUIRED = {
    "agents": (
        "LA CONVERSATION EXÉCUTE ELLE-MÊME DEUX REVUES ADVERSARIALES INTERNES A/B",
        "Ne jamais mettre un lot en attente",
        "revues adversariales internes A/B",
        "plafonnée à `9.4/10`",
        "vrai login UI",
    ),
    "rpg": (
        "ChatGPT executes the two reviews itself",
        "Do not wait for two external reviewers",
        "real UI login",
        "Human approval, clinical validation and RPG-P stay separate",
    ),
    "scoring": (
        "Ne jamais répondre",
        "il reste les deux vraies revues indépendantes",
        "auto-revue conversationnelle",
        "9.4/10",
        "VERIFIED",
    ),
    "techdoubt": (
        "RESOLVED AS A FALSE DEPENDENCY",
        "internal A/B double-review procedure",
        "These tests have NOT been executed",
    ),
}

FORBIDDEN_ACTIVE = {
    "agents": (
        "laisser ouvert le gate BLIND USERS applicable",
        "deux agents BLIND USERS isolés",
        "deux agents IA BLIND USERS spécialisés, et NON",
    ),
    "rpg": (
        "Do not claim the blind-user gate passed without actual separated executions",
        "Reviewer A and B for FUE user testing are two distinct AI agents",
    ),
}
def main() -> int:
    checks: list[dict[str, object]] = []
    for key, path in SOURCES.items():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            checks.append({"check": f"{key}:file", "passed": False, "error": str(exc)})
            continue
        for token in REQUIRED[key]:
            checks.append({"check": f"{key}:required:{token[:72]}", "passed": token in text})
        for token in FORBIDDEN_ACTIVE.get(key, ()):
            checks.append({"check": f"{key}:obsolete:{token[:72]}", "passed": token not in text})
    failures = [entry for entry in checks if not entry["passed"]]
    result = {
        "gate": "GLOBAL-G10-S_CONVERSATIONAL_A_B_DOCTRINE",
        "head": os.environ.get("GITHUB_SHA", "local"),
        "status": "PASS" if not failures else "FAIL",
        "scope": "documentary wording only — no claim of executed A/B reviews, login FUE or physical proof",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failures),
        "checks_failed": len(failures),
        "checks": checks,
    }
    output = ROOT / "artifacts/g0-interactive-inventory"
    output.mkdir(parents=True, exist_ok=True)
    (output / "conversational-review-doctrine.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
