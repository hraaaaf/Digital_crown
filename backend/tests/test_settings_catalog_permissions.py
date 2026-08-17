from backend import models
from backend.routers.auth import has_permission


def _user(role, employer_id=None, permissions=None):
    return models.User(
        email=f"{role.value.lower()}-{employer_id or 'root'}@cabinet.test",
        hashed_password="x",
        role=role,
        employer_id=employer_id,
        permissions=permissions,
        is_active=True,
        is_licensed=True,
    )


def test_secretary_legacy_defaults_cannot_mutate_settings_catalog():
    secretary = _user(models.UserRole.SECRETAIRE, employer_id=10, permissions={})
    assert has_permission(secretary, "agenda") is True
    assert has_permission(secretary, "settings") is False


def test_explicit_settings_permission_allows_employee_mutation():
    employee = _user(
        models.UserRole.DENTISTE,
        employer_id=10,
        permissions={"settings": True, "agenda": True},
    )
    assert has_permission(employee, "settings") is True


def test_root_dentist_retains_settings_control():
    owner = _user(models.UserRole.DENTISTE, employer_id=None, permissions={})
    assert has_permission(owner, "settings") is True
