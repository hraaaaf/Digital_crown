from types import SimpleNamespace
from unittest.mock import Mock

from backend.services import cmo_agent_service
from backend.services.cmo_agent_service import CMOAgentService


class _QueryStub:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.value


class _DBStub:
    def __init__(self, *query_results):
        self.query_results = list(query_results)

    def query(self, *args, **kwargs):
        return _QueryStub(self.query_results.pop(0))


def _analysis(report_narrative=None):
    return SimpleNamespace(report_narrative=report_narrative)


def _all_text(result):
    return " ".join(
        str(result.get(key, ""))
        for key in (
            "synthese_clinique",
            "soins_prealables",
            "plan_orthodontique",
            "pronostic",
            "uncertainty",
        )
    ).lower()


def test_cmo_text_signal_cannot_become_autonomous_treatment_decision(monkeypatch):
    memory = Mock()
    monkeypatch.setattr(cmo_agent_service, "ghost_memory", memory)
    db = _DBStub(
        _analysis("Carie avec infection et lésion parodontale. Dent de sagesse incluse."),
        _analysis(),
    )

    result = CMOAgentService().generate_global_synthesis(db, patient_id=42, employer_id=7)

    assert result["decision_status"] == "NON_PRESCRIPTIVE"
    assert result["practitioner_validation_required"] is True
    assert result["evidence"]
    assert result["uncertainty"]
    assert result["pronostic"] == "Non déterminé automatiquement"

    rendered = _all_text(result)
    for forbidden in (
        "feu vert",
        "impératif",
        "doit être reportée",
        "prêt pour orthodontie",
        "soins requis avant orthodontie",
    ):
        assert forbidden not in rendered

    memory.add_memory.assert_called_once()
    call = memory.add_memory.call_args.kwargs
    assert call["insight_type"] == "CMO_SIGNAL"
    assert "aucune décision thérapeutique automatisée" in call["content"].lower()
    assert "prêt pour orthodontie" not in call["content"].lower()
    assert "soins requis avant orthodontie" not in call["content"].lower()


def test_cmo_exposes_independent_periodontal_evidence(monkeypatch):
    memory = Mock()
    monkeypatch.setattr(cmo_agent_service, "ghost_memory", memory)
    db = _DBStub(_analysis("Infection avec atteinte parodontale."), None)

    result = CMOAgentService().generate_global_synthesis(db, patient_id=12)

    signals = set(result["signals"])
    assert "infection" in signals
    assert "parodontal" in signals
    evidence_signals = {item["signal"] for item in result["evidence"]}
    assert evidence_signals == signals
    assert result["practitioner_validation_required"] is True


def test_cmo_no_targeted_signal_does_not_create_readiness_claim(monkeypatch):
    memory = Mock()
    monkeypatch.setattr(cmo_agent_service, "ghost_memory", memory)
    db = _DBStub(_analysis("Panoramique sans terme ciblé."), _analysis())

    result = CMOAgentService().generate_global_synthesis(db, patient_id=9)

    assert result["signals"] == []
    assert result["evidence"] == []
    assert result["decision_status"] == "NON_PRESCRIPTIVE"
    assert "aucune décision" in result["plan_orthodontique"].lower()
    assert "prêt pour orthodontie" not in memory.add_memory.call_args.kwargs["content"].lower()


def test_cmo_empty_fallback_is_fail_safe(monkeypatch):
    memory = Mock()
    monkeypatch.setattr(cmo_agent_service, "ghost_memory", memory)
    db = _DBStub(None, None)

    result = CMOAgentService().generate_global_synthesis(db, patient_id=3)

    assert result["is_fallback"] is True
    assert result["decision_status"] == "NON_PRESCRIPTIVE"
    assert result["practitioner_validation_required"] is True
    assert result["signals"] == []
    assert result["evidence"] == []
    assert result["uncertainty"]
    assert result["pronostic"] == "Non déterminé automatiquement"
    memory.add_memory.assert_not_called()
