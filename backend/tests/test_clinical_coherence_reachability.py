from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = "backend/services/clinical_coherence.py"
TOKENS = ("clinical_coherence", "coherence_service", "ClinicalCoherenceService")


def test_legacy_clinical_coherence_has_no_runtime_consumers():
    consumers = []

    for path in (ROOT / "backend").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if relative == TARGET or relative.startswith("backend/tests/"):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        matched = sorted(token for token in TOKENS if token in source)
        if matched:
            consumers.append((relative, matched))

    assert not consumers, f"clinical_coherence still has runtime consumers: {consumers}"
