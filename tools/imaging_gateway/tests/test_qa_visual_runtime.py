"""Adversarial negative oracles for complete operational route inventories."""
import unittest
from tools.imaging_gateway.qa_visual_runtime import PREFLIGHT, route_delta, validate_route_transition

P = (PREFLIGHT, ("POST",))
EXISTING = ("/api/patients/{patient_id}/assets/import", ("POST",))


class RouteTransitionTests(unittest.TestCase):
    def test_duplicate_unrelated_route_is_not_hidden_by_set_comparison(self):
        before = [EXISTING]
        after = [EXISTING, EXISTING, P]
        extra, missing = route_delta(before, after)
        assert extra == sorted([EXISTING, P])
        assert missing == []
        assert extra != [P]


    def test_removed_duplicate_is_reported_even_if_route_remains(self):
        before = [EXISTING, EXISTING]
        after = [EXISTING, P]
        extra, missing = route_delta(before, after)
        assert extra == [P]
        assert missing == [EXISTING]


    def test_first_level_preflight_addition_is_strictly_accepted(self):
        assert validate_route_transition([EXISTING], [EXISTING, P])[0:2] == (0, 1)


    def test_stacked_child_preflight_preservation_is_strictly_accepted(self):
        assert validate_route_transition([EXISTING, P], [EXISTING, P])[0:2] == (1, 1)


    def test_stacked_child_rejects_duplicate_preflight_or_other_route(self):
        with self.assertRaises(AssertionError):
            validate_route_transition([EXISTING, P], [EXISTING, P, P])
        with self.assertRaises(AssertionError):
            validate_route_transition([EXISTING, P], [EXISTING, P, ("/unexpected", ("GET",))])


    def test_stacked_child_rejects_dropped_or_duplicated_existing_import(self):
        with self.assertRaises(AssertionError):
            validate_route_transition([EXISTING, P], [P])
        with self.assertRaises(AssertionError):
            validate_route_transition([EXISTING, P], [EXISTING, EXISTING, P])
