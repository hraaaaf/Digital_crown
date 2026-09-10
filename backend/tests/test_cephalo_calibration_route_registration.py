"""Reachability contract for the provenance-aware calibration facade."""
from backend.routers import ia


def test_exactly_one_calibration_post_route_is_registered():
    routes = [
        route
        for route in ia.router.routes
        if getattr(route, "path", None) == "/analyses/{analysis_id}/calibrate"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]
    assert len(routes) == 1
    assert routes[0].endpoint.__name__ == "calibrate_analysis_with_provenance"
