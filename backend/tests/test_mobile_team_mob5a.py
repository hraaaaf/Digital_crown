import inspect

from backend.routers import mobile, mobile_legacy


def test_mobile_dentists_route_is_unique_and_uses_canonical_legacy_endpoint():
    routes = [
        route
        for route in mobile.router.routes
        if getattr(route, "path", None) == "/dentists"
        and "GET" in (getattr(route, "methods", set()) or set())
    ]

    assert len(routes) == 1
    assert routes[0].endpoint is mobile_legacy.get_mobile_dentists


def test_mobile_dentists_contract_keeps_agenda_permission_and_tenant_scope():
    source = inspect.getsource(mobile_legacy.get_mobile_dentists)

    assert 'Depends(get_mobile_employer_id)' in source
    assert 'Depends(require_mobile_permission("agenda"))' in source
    assert 'models.User.employer_id == employer_id' in source
    assert 'models.Appointment.employer_id == employer_id' in source
