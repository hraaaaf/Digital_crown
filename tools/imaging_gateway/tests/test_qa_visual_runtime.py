"""Adversarial negative oracles for complete operational route inventories."""
import unittest
from tools.imaging_gateway.qa_visual_runtime import PREFLIGHT, LAB_OPERATIONAL, route_delta, validate_route_transition

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


    def test_exact_lab_operational_route_is_the_only_extra_get_allowed(self):
        lab = (LAB_OPERATIONAL, ("GET",))
        old = [EXISTING]
        new = [EXISTING, P, lab]
        proof = validate_route_transition(old, new)
        assert proof[4] == sorted([P, lab])
        assert proof[5] == []
        # A pre-existing LAB route must remain single, not be duplicated.
        assert validate_route_transition(new, new)[4:6] == ([], [])
        with self.assertRaises(AssertionError):
            validate_route_transition(old, new + [lab])
        with self.assertRaises(AssertionError):
            validate_route_transition(new, [EXISTING, P])
        with self.assertRaises(AssertionError):
            validate_route_transition(old, new + [("/unreviewed", ("GET",))])
        with self.assertRaises(AssertionError):
            validate_route_transition(old, new + [(LAB_OPERATIONAL, ("POST",))])

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


    def test_exact_lab_http_routes_are_allowed_only_as_complete_private_bundle(self):
        from tools.imaging_gateway.qa_visual_runtime import LAB_HTTP
        baseline = [EXISTING, P, (LAB_OPERATIONAL, ("GET",))]
        complete = baseline + list(LAB_HTTP)
        assert validate_route_transition(baseline, complete)[4] == sorted(LAB_HTTP)
        assert validate_route_transition(complete, complete)[4:6] == ([], [])
        for index in range(len(LAB_HTTP)):
            with self.assertRaises(AssertionError):
                validate_route_transition(baseline, baseline + [
                    route for n, route in enumerate(LAB_HTTP) if n != index
                ])
        with self.assertRaises(AssertionError):
            validate_route_transition(complete, baseline)
        with self.assertRaises(AssertionError):
            validate_route_transition(baseline, complete + [LAB_HTTP[0]])
        with self.assertRaises(AssertionError):
            validate_route_transition(baseline, complete + [
                ("/api/imaging-acquisitions/lab/receipt", ("POST",))
            ])
        with self.assertRaises(AssertionError):
            validate_route_transition(baseline, complete + [("/api/clinical/new", ("POST",))])
