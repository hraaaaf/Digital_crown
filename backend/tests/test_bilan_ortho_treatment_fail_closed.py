"""Treatment-generation safety contracts for BilanOrthoEngine."""
from pathlib import Path

from backend import schemas
from backend.services.bilan_ortho_engine import bilan_ortho_engine


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE = REPO_ROOT / "backend/services/bilan_ortho_engine.py"


def test_legacy_plan_generator_returns_only_practitioner_plan():
    clinical = schemas.ClinicalData(plan_traitement="Plan validé par le praticien")
    result = bilan_ortho_engine._generate_plan_traitement(None, clinical)
    assert result == "Plan validé par le praticien"


def test_legacy_plan_generator_fails_closed_without_practitioner_plan():
    clinical = schemas.ClinicalData()
    result = bilan_ortho_engine._generate_plan_traitement(None, clinical)
    assert "Aucune stratégie thérapeutique n'est générée automatiquement" in result


def test_legacy_generator_contains_no_device_or_mechanics_prescription():
    source = ENGINE.read_text(encoding="utf-8")
    legacy = source.split("def _generate_plan_traitement", 1)[1]
    forbidden = (
        "DAMON",
        "ALIGNEURS",
        "Invisalign",
        "IPR",
        "Multi-attaches Conventionnel",
        "TRAITEMENT INTERCEPTIF",
    )
    for token in forbidden:
        assert token not in legacy, f"legacy treatment generator reintroduced: {token}"
