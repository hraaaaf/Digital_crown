from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.services.cmo_agent_service import CMOAgentService


def _query_returning(value):
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = value
    return query


def _db_with(pano=None, cephalo=None):
    db = MagicMock()
    db.query.side_effect = [_query_returning(pano), _query_returning(cephalo)]
    return db


def test_textual_findings_remain_signals_not_treatment_decisions():
    pano = SimpleNamespace(
        report_narrative="Carie, infection et dent de sagesse incluse visibles sur le compte rendu."
    )
    cephalo = SimpleNamespace()
    db = _db_with(pano=pano, cephalo=cephalo)

    with patch("backend.services.cmo_agent_service.ghost_memory.add_memory") as add_memory:
        result = CMOAgentService().generate_global_synthesis(db, patient_id=42, employer_id=7)

    rendered = " ".join(
        [
            result["synthese_clinique"],
            result["soins_prealables"],
            result["plan_orthodontique"],
            result["pronostic"],
        ]
    ).lower()

    assert result["requires_practitioner_validation"] is True
    assert result["decision_status"] == "NON_EVALUE"
    assert result["pronostic"] == "Non évalué automatiquement"
    assert {signal["code"] for signal in result["signals"]} == {
        "CARIES_TEXT_SIGNAL",
        "INFECTION_TEXT_SIGNAL",
        "WISDOM_TOOTH_TEXT_SIGNAL",
    }
    assert all(signal["source"] == "panoramic_report_narrative" for signal in result["signals"])
    assert all("Signal lexical uniquement" in signal["uncertainty"] for signal in result["signals"])

    for forbidden in (
        "traitement conservateur",
        "assainissement parodontal",
        "assainissement endodontique",
        "avulsion",
        "prêt pour orthodontie",
        "pronostic favorable",
        "pronostic réservé",
    ):
        assert forbidden not in rendered

    memory_kwargs = add_memory.call_args.kwargs
    assert memory_kwargs["employer_id"] == 7
    assert "Recommandation CMO" not in memory_kwargs["content"]
    assert "Validation praticien requise" in memory_kwargs["content"]


def test_absence_of_targeted_words_never_becomes_orthodontic_green_light():
    pano = SimpleNamespace(report_narrative="Compte rendu panoramique sans mention ciblée.")
    cephalo = SimpleNamespace()
    db = _db_with(pano=pano, cephalo=cephalo)

    with patch("backend.services.cmo_agent_service.ghost_memory.add_memory"):
        result = CMOAgentService().generate_global_synthesis(db, patient_id=5)

    plan = result["plan_orthodontique"].lower()
    assert result["signals"] == []
    assert result["requires_practitioner_validation"] is True
    assert result["decision_status"] == "NON_EVALUE"
    assert "feu vert thérapeutique" in plan
    assert "ne constitue pas" in plan
    assert "prêt pour orthodontie" not in plan


def test_empty_fallback_is_explicitly_non_evaluable():
    db = _db_with(pano=None, cephalo=None)

    result = CMOAgentService().generate_global_synthesis(db, patient_id=99)

    assert result["is_fallback"] is True
    assert result["signals"] == []
    assert result["requires_practitioner_validation"] is True
    assert result["decision_status"] == "NON_EVALUE"
    assert result["pronostic"] == "Non évalué automatiquement"
