from backend.services.cmo_agent_service import CMOAgentService


def test_cmo_text_signals_never_become_treatment_instructions():
    result = CMOAgentService()._build_non_prescriptive_synthesis(
        pano_text="Carie, infection et dent de sagesse incluse.",
        cephalo_available=True,
    )

    combined = " ".join(
        [
            result["synthese_clinique"],
            result["soins_prealables"],
            result["plan_orthodontique"],
            result["pronostic"],
        ]
    ).lower()

    assert result["automation_scope"] == "signal_only"
    assert result["practitioner_validation_required"] is True
    assert result["pronostic"] == "Non déterminé automatiquement"
    assert len(result["evidence"]) == 3

    forbidden = (
        "feu vert",
        "traitement conservateur",
        "assainissement parodontal",
        "assainissement total",
        "avulsion",
        "soins requis avant orthodontie",
        "prêt pour orthodontie",
        "pronostic favorable",
        "pronostic réservé",
    )
    for phrase in forbidden:
        assert phrase not in combined


def test_cmo_negated_text_is_only_a_mention_not_a_diagnosis():
    result = CMOAgentService()._build_non_prescriptive_synthesis(
        pano_text="Absence de carie et pas d'infection visible.",
        cephalo_available=False,
    )

    assert result["evidence"]
    assert "mentions textuelles" in result["uncertainty"]
    assert "ne tient pas lieu de diagnostic" in result["uncertainty"]
    assert result["practitioner_validation_required"] is True
    assert "aucune décision orthodontique" in result["plan_orthodontique"].lower()


def test_cmo_empty_fallback_remains_non_prescriptive():
    result = CMOAgentService()._empty_fallback()

    assert result["is_fallback"] is True
    assert result["evidence"] == []
    assert result["pronostic"] == "Non déterminé automatiquement"
    assert result["practitioner_validation_required"] is True
    assert result["automation_scope"] == "signal_only"
    assert "aucune conclusion thérapeutique automatique" in result["soins_prealables"].lower()
