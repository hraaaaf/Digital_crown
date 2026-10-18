#!/usr/bin/env python3
"""GLOBAL-G10-S: doctrine-only gate for two FUE and one transversal review.

No FUE browser execution, clinical review, patient data or physical devices
are certified by this static check. Actual FUE evidence remains a separate gate.
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
    "agents": [
        "Deux FUE de première utilisation + UNE revue adversariale transversale",
        "FUE-A — métier/UX",
        "FUE-B — autre persona",
        "UNE revue adversariale transversale (APRÈS les FUE)",
        "FUE-0 :",
        "login UI",
        "NOT RUN",
        "9.4/10",
    ],
    "rpg": [
        "Two executed FUE journeys + ONE transversal adversarial review",
        "FUE-A = first useful outcome",
        "FUE-B = a complementary user/role",
        "ONE transversal adversarial review AFTER the FUE",
        "Real user-journey evidence is mandatory",
        "RPG-P remain distinct",
    ],
    "scoring": [
        "FUE-A",
        "FUE-B",
        "UNE revue adversariale transversale",
        "9.4/10",
        "VERIFIED",
    ],
    "techdoubt": [
        "Two real FUE journeys + one transversal adversarial review",
        "Unproven execution: OPEN",
        "There is **no separate missing second review**",
    ],
}
FORBIDDEN_ACTIVE = {
    "agents": [
        "LA CONVERSATION EXÉCUTE ELLE-MÊME DEUX REVUES ADVERSARIALES INTERNES A/B",
        "- écrire **au minimum deux prompts adversariaux distincts**",
        "deux revues adversariales restent requis",
        "deux perspectives adversariales (vérité UX",
    ],
    "rpg": [
        "ChatGPT executes the two reviews itself",
        "then two adversarial reviews on the same HEAD",
    ],
    "scoring": [
        "les deux revues adversariales internes spécialisées",
        "les deux revues A/B spécialisées",
    ],
}
def main() -> int:
    evidence: list[dict[str, object]] = []
    for category, path in SOURCES.items():
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            evidence.append({"id": f"{category}:file", "pass": False, "reason": str(exc)})
            continue
        for fragment in REQUIRED[category]:
            evidence.append({"id": f"{category}:required:{fragment}", "pass": fragment in content})
        for fragment in FORBIDDEN_ACTIVE.get(category, []):
            evidence.append({"id": f"{category}:obsolete:{fragment}", "pass": fragment not in content})

    passed = sum(1 for entry in evidence if entry["pass"])
    report = {
        "gate": "GLOBAL_G10S_TWO_FUE_ONE_TRANSVERSAL_REVIEW_DOCTRINE",
        "head": os.environ.get("GITHUB_SHA", "local"),
        "scope": "Documentation contract only; FUE-A/FUE-B NOT RUN by this test",
        "status": "PASS" if passed == len(evidence) else "FAIL",
        "checks_total": len(evidence),
        "checks_passed": passed,
        "checks_failed": len(evidence) - passed,
        "assertions": evidence,
    }
    path = ROOT / "artifacts/g0-interactive-inventory" / "fue-transversal-doctrine.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
