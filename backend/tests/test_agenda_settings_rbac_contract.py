import inspect

from backend.routers import agenda_settings


def _permissions_for(path: str, method: str) -> list[str]:
    route = next(
        r for r in agenda_settings.router.routes
        if getattr(r, "path", None) == path and method in getattr(r, "methods", set())
    )
    permissions = []
    for dependency in route.dependant.dependencies:
        call = dependency.call
        if not callable(call):
            continue
        try:
            closure = inspect.getclosurevars(call).nonlocals
        except (TypeError, ValueError):
            continue
        permission = closure.get("permission_name")
        if isinstance(permission, str):
            permissions.append(permission)
    return permissions


def test_structural_agenda_update_requires_settings():
    assert "settings" in _permissions_for("/agenda/settings", "PUT")


def test_agenda_read_remains_available_to_agenda_role():
    assert "agenda" in _permissions_for("/agenda/settings", "GET")


def test_operational_exceptions_remain_agenda_scoped():
    assert "agenda" in _permissions_for("/agenda/exceptions", "POST")
    assert "agenda" in _permissions_for("/agenda/exceptions/{exc_id}", "DELETE")
