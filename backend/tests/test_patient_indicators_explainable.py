from pathlib import Path
from types import SimpleNamespace

from backend.services.rag_context import _extract_cephalo_trend


BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend" / "src"


def test_cephalo_trend_is_factual_delta_not_improvement_judgment():
    recent = SimpleNamespace(angles_data={"IMPA": {"valeur": 98.0}})
    previous = SimpleNamespace(angles_data={"IMPA": {"valeur": 94.5}})
    assert _extract_cephalo_trend([recent, previous]) == "ΔIMPA +3.5° entre les deux dernières analyses"


def test_habits_language_describes_observed_facts():
    text = (BACKEND / "services" / "habits_engine.py").read_text(encoding="utf-8")
    assert '"title": "Risque No-Show Élevé"' not in text
    assert '"title": "Risque Perte Patient"' not in text
    assert '"title": "Gap Ortho Critique"' not in text
    assert '"title": "Annulations fréquentes"' in text
    assert '"title": "Annulations consécutives sans rebooking"' in text
    assert '"title": "Suivi ortho à replanifier"' in text


def test_global_intelligence_score_is_no_longer_computed_or_presented():
    elite = (BACKEND / "services" / "elite_manager.py").read_text(encoding="utf-8")
    assert "intel_score = self._calculate_intelligence_score" not in elite
    hover = (FRONTEND / "features" / "patients" / "components" / "PatientSummaryHoverCard.tsx").read_text(encoding="utf-8")
    assert "data.intelligence_score" not in hover
    assert "Assistant Virtuel ODF" not in hover
    assert "Alertes IA & Suggestion" not in hover


def test_patient_page_surfaces_nba_reason_and_unmounts_dead_flash_summary():
    details = (FRONTEND / "features" / "patients" / "PatientDetailsInner.tsx").read_text(encoding="utf-8")
    assert "res.data.nba.message" in details
    assert "<FlashSummary" not in details
    assert "import { FlashSummary }" not in details
