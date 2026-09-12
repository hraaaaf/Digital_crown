"""Contract tests for the fail-closed COM/CRANIOM evidence-debt ledger."""

from backend.services.cephalo_com_evidence_ledger import (
    COM_EVIDENCE_DEBT_BY_ID,
    COM_EVIDENCE_DEBTS,
    COM_SOURCE_INDEX,
    ComEvidenceState,
    patient_classification_references,
)


def test_com_backlog_is_complete_and_no_drop():
    assert len(COM_EVIDENCE_DEBTS) == 17
    assert len(COM_EVIDENCE_DEBT_BY_ID) == 17
    assert len({item.debt_id for item in COM_EVIDENCE_DEBTS}) == 17

    expected = {
        "COM_OVERJET_1P5_3_MM",
        "COM_OVERBITE_1P5_3_MM",
        "COM_IMPA_90_PM5",
        "COM_IMPA_DYNAMIC_COMPENSATION",
        "COM_U1_FH_107_PM5",
        "COM_U1_FH_COMP_97_120",
        "COM_INTERINCISAL_131_PM3",
        "COM_INTERINCISAL_COMP_120_142",
        "COM_FMA_26_PM4",
        "COM_CRANIOM_ABP_9Y",
        "COM_CRANIOM_ABP_ADULT",
        "COM_CRANIOM_A_NVERT_9Y",
        "COM_CRANIOM_A_NVERT_ADULT",
        "COM_CRANIOM_B_NVERT_9Y",
        "COM_CRANIOM_B_NVERT_ADULT",
        "COM_CRANIOM_S_NVERT_DEPTH_9Y",
        "COM_CRANIOM_S_NVERT_DEPTH_ADULT",
    }
    assert set(COM_EVIDENCE_DEBT_BY_ID) == expected


def test_no_research_debt_is_active_for_patient_classification():
    assert patient_classification_references() == ()
    assert all(not item.active_for_patient_classification for item in COM_EVIDENCE_DEBTS)


def test_every_debt_has_explicit_blocker_and_next_exact():
    for item in COM_EVIDENCE_DEBTS:
        assert item.blocker.strip()
        assert item.next_exact.strip()
        assert item.historical_value.strip()
        assert item.state in set(ComEvidenceState)


def test_tweed_impa_numeric_evidence_is_source_locked_but_geometry_blocked():
    item = COM_EVIDENCE_DEBT_BY_ID["COM_IMPA_90_PM5"]
    assert item.state == ComEvidenceState.SOURCE_LOCKED_CONSTRUCTION_BLOCKED
    assert item.source_ids == ("TWEED_1954_FMIA",)
    assert item.construction_gate == "TWEED_MANDIBULAR_PLANE_EXACT_REQUIRED"
    assert "Go-Me" in item.blocker
    assert COM_SOURCE_INDEX["TWEED_1954_FMIA"]["source_level"] == "PRIMARY"


def test_tweed_compensation_is_preserved_as_dynamic_rule_not_fake_fixed_norm():
    item = COM_EVIDENCE_DEBT_BY_ID["COM_IMPA_DYNAMIC_COMPENSATION"]
    assert item.state == ComEvidenceState.SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED
    assert "dynamic rule" in item.historical_value
    assert "80-100" in item.historical_value
    assert "FMA 35 -> IMPA 80" in item.next_exact


def test_known_unverified_historical_values_remain_blocked():
    assert (
        COM_EVIDENCE_DEBT_BY_ID["COM_FMA_26_PM4"].state
        == ComEvidenceState.PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING
    )
    assert (
        COM_EVIDENCE_DEBT_BY_ID["COM_INTERINCISAL_131_PM3"].state
        == ComEvidenceState.PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED
    )
    assert (
        COM_EVIDENCE_DEBT_BY_ID["COM_U1_FH_COMP_97_120"].state
        == ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND
    )
    assert (
        COM_EVIDENCE_DEBT_BY_ID["COM_INTERINCISAL_COMP_120_142"].state
        == ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND
    )


def test_craniom_secondary_values_are_not_promoted_to_primary_norms():
    craniom_rows = [
        item for item in COM_EVIDENCE_DEBTS if item.debt_id.startswith("COM_CRANIOM_")
    ]
    assert len(craniom_rows) == 8
    assert all("CRANIOM_PART2_2011" in item.source_ids for item in craniom_rows)
    assert all(
        item.state
        in {
            ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
            ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING,
        }
        for item in craniom_rows
    )


def test_known_craniom_divergences_remain_explicit():
    a_adult = COM_EVIDENCE_DEBT_BY_ID["COM_CRANIOM_A_NVERT_ADULT"]
    depth_9 = COM_EVIDENCE_DEBT_BY_ID["COM_CRANIOM_S_NVERT_DEPTH_9Y"]

    assert "3.0" in a_adult.historical_value and "3.3" in a_adult.historical_value
    assert "61.3" in depth_9.historical_value and "62" in depth_9.historical_value
    assert a_adult.state == ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING
    assert depth_9.state == ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING
