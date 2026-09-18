from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOTS = [ROOT / "backend", ROOT / "frontend" / "src"]
FORBIDDEN = (
    "docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_",
    "PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv",
    "PRESCRIPTION_PHARMACOLOGY_MOROCCO_MEDICINE_CURRENT_STATUS_PROJECTION_V1_2026-09-17.csv",
)


def test_reconstructed_pharmacology_reference_remains_audit_only():
    violations = []
    for root in RUNTIME_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "tests" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            hits = [token for token in FORBIDDEN if token in text]
            if hits:
                violations.append((str(path.relative_to(ROOT)), hits))
    assert not violations, violations
