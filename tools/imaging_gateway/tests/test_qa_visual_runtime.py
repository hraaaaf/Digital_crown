"""Adversarial negative oracles for complete operational route inventories."""
import pytest
from tools.imaging_gateway.qa_visual_runtime import PREFLIGHT, route_delta, validate_route_transition

P = (PREFLIGHT, ("POST",))
EXISTING = ("/api/patients/{patient_id}/assets/import", ("POST",))


def test_duplicate_unrelated_route_is_not_hidden_by_set_comparison():
    before = [EXISTING]
    after = [EXISTING, EXISTING, P]
    extra, missing = route_delta(before, after)
    assert extra == sorted([EXISTING, P])
    assert missing == []
    assert extra != [P]


def test_removed_duplicate_is_reported_even_if_route_remains():
    before = [EXISTING, EXISTING]
    after = [EXISTING, P]
    extra, missing = route_delta(before, after)
    assert extra == [P]
    assert missing == [EXISTING]


def test_first_level_preflight_addition_is_strictly_accepted():
    assert validate_route_transition([EXISTING], [EXISTING, P])[0:2] == (0, 1)


def test_stacked_child_preflight_preservation_is_strictly_accepted():
    assert validate_route_transition([EXISTING, P], [EXISTING, P])[0:2] == (1, 1)


def test_stacked_child_rejects_duplicate_preflight_or_other_route():
    with pytest.raises(AssertionError):
        validate_route_transition([EXISTING, P], [EXISTING, P, P])
    with pytest.raises(AssertionError):
        validate_route_transition([EXISTING, P], [EXISTING, P, ("/unexpected", ("GET",))])


def test_stacked_child_rejects_dropped_or_duplicated_existing_import():
    with pytest.raises(AssertionError):
        validate_route_transition([EXISTING, P], [P])
    with pytest.raises(AssertionError):
        validate_route_transition([EXISTING, P], [EXISTING, EXISTING, P])
