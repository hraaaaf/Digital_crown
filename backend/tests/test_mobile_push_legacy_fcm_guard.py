"""LOT E E0 regression guard: Web Push is the only active OS-push registration API."""


def test_legacy_fcm_registration_route_is_not_mounted():
    from backend.routers import mobile

    legacy_fcm_routes = [
        route
        for route in mobile.router.routes
        if getattr(route, "path", None) == "/register-device"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]

    assert legacy_fcm_routes == []


def test_canonical_web_push_registration_route_is_mounted_once():
    from backend.routers import mobile

    web_push_routes = [
        route
        for route in mobile.router.routes
        if getattr(route, "path", None) == "/push/subscription"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]

    assert len(web_push_routes) == 1
