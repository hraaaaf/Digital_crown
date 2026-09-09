"""Safety contract for the quarantined legacy cephalometric advisor."""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ADVISOR = REPO_ROOT / "backend/services/ai_advisor.py"


def test_legacy_advisor_contains_no_autonomous_treatment_vocabulary():
    source = ADVISOR.read_text(encoding="utf-8")
    forbidden = (
        "Mini-vis",
        "Multi-attaches auto-ligaturants",
        "Appareillage fonctionnel interceptif",
        "chirurgie.",
        "Rétroclinaison incisive mandibulaire nécessaire",
        "Contrôle vertical strict impératif",
    )
    for token in forbidden:
        assert token not in source, f"autonomous legacy advisor treatment token reintroduced: {token}"

    assert "Aucune stratégie thérapeutique n'est générée automatiquement" in source
    assert "Aucune interprétation diagnostique autonome" in source
