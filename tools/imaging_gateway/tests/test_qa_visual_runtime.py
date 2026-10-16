"""Adversarial negative oracles for complete operational route inventories."""
from tools.imaging_gateway.qa_visual_runtime import PREFLIGHT, route_delta

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
