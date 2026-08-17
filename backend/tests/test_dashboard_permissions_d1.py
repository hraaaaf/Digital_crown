"""D1 Dashboard — matrice RBAC canonique et endpoints sensibles fail-closed."""
from types import SimpleNamespace

from backend import models
from backend.routers.auth import has_permission
from backend.security import get_password_hash


def _policy_user(role, employer_id, permissions=None, email="rbac-d1@test.invalid"):
    return SimpleNamespace(
        email=email,
        role=role,
        employer_id=employer_id,
        permissions={} if permissions is None else permissions,
    )


def _db_user(db, email, role="DENTISTE", employer_id=None, permissions=None, licensed=True):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="D1 Test",
        is_active=True,
        is_licensed=licensed,
        employer_id=employer_id,
        permissions={} if permissions is None else permissions,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_permission_matrix_d1_is_fail_closed():
    owner = _policy_user("DENTISTE", None)
    assert has_permission(owner, "patients") is True
    assert has_permission(owner, "accounting") is True
    assert has_permission(owner, "admin") is True

    employee = _policy_user("DENTISTE", 10)
    assert has_permission(employee, "patients") is True
    assert has_permission(employee, "agenda") is True
    assert has_permission(employee, "prescriptions") is True
    assert has_permission(employee, "panoramic") is True
    assert has_permission(employee, "cephalo") is True
    assert has_permission(employee, "accounting") is False
    assert has_permission(employee, "payments") is False
    assert has_permission(employee, "settings") is False
    assert has_permission(employee, "admin") is False

    secretary = _policy_user("SECRETAIRE", 10)
    assert has_permission(secretary, "patients") is True
    assert has_permission(secretary, "agenda") is True
    assert has_permission(secretary, "accounting") is False
    assert has_permission(secretary, "admin") is False

    explicit = _policy_user(
        "DENTISTE",
        10,
        permissions={"patients": False, "accounting": True},
    )
    assert has_permission(explicit, "patients") is False
    assert has_permission(explicit, "accounting") is True
    assert has_permission(explicit, "agenda") is False

    unknown = _policy_user("UNKNOWN", 10)
    assert has_permission(unknown, "patients") is False
    assert has_permission(unknown, "accounting") is False


def test_legacy_employee_can_read_patient_dashboard_but_not_finance(client, db):
    owner = _db_user(db, "owner-d1@test.ma", licensed=True)
    employee = _db_user(
        db,
        "employee-d1@test.ma",
        employer_id=owner.id,
        permissions={},
        licensed=True,
    )
    headers = _headers(client, employee)

    dashboard = client.get("/api/admin/dashboard/stats", headers=headers)
    financial = client.get("/api/stats/financial", headers=headers)
    forecast = client.get("/api/intelligence/forecast-semaine", headers=headers)

    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["pending_team_requests"] == 0
    assert dashboard.json()["team_quota"] is None
    assert financial.status_code == 403, financial.text
    assert forecast.status_code == 403, forecast.text


def test_explicit_accounting_permission_unlocks_finance_but_not_patient_dashboard(client, db):
    owner = _db_user(db, "owner-accounting-d1@test.ma", licensed=True)
    employee = _db_user(
        db,
        "employee-accounting-d1@test.ma",
        employer_id=owner.id,
        permissions={"accounting": True},
        licensed=True,
    )
    headers = _headers(client, employee)

    dashboard = client.get("/api/admin/dashboard/stats", headers=headers)
    financial = client.get("/api/stats/financial", headers=headers)
    forecast = client.get("/api/intelligence/forecast-semaine", headers=headers)

    assert dashboard.status_code == 403, dashboard.text
    assert financial.status_code == 200, financial.text
    assert forecast.status_code == 200, forecast.text


def test_explicit_patient_denial_blocks_patient_dashboard(client, db):
    owner = _db_user(db, "owner-deny-patients-d1@test.ma", licensed=True)
    employee = _db_user(
        db,
        "employee-deny-patients-d1@test.ma",
        employer_id=owner.id,
        permissions={"patients": False},
        licensed=True,
    )
    headers = _headers(client, employee)

    response = client.get("/api/admin/dashboard/stats", headers=headers)
    assert response.status_code == 403, response.text
