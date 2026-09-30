import pytest

from backend import models
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_workstation_rate_limit(monkeypatch):
    monkeypatch.setattr("backend.routers.workstation_mode.check_rate_limit", lambda *args, **kwargs: None)


def _token(client, email: str, password: str) -> str:
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return token


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_first_launch_creates_user_independent_workstation_state(client, db, dentiste):
    owner_token = _token(client, dentiste.email, "TestPass123!")
    first = client.get("/api/workstation/state", headers=_headers(owner_token))
    assert first.status_code == 200, first.text
    payload = first.json()
    assert payload["defaultExperience"] is None
    assert payload["pinConfigured"] is False
    assert payload["stationLocked"] is False
    workstation_id = payload["workstationId"]
    raw_cookie = client.cookies.get("dc_workstation")
    stored = db.query(models.WorkstationMode).filter(models.WorkstationMode.id == workstation_id).one()
    assert raw_cookie
    assert stored.token_hash != raw_cookie
    assert stored.token_hash == __import__("hashlib").sha256(raw_cookie.encode("utf-8")).hexdigest()

    bootstrap = client.get("/api/workstation/bootstrap")
    assert bootstrap.status_code == 200
    assert bootstrap.json()["workstationId"] == workstation_id
    assert bootstrap.json()["defaultExperience"] is None

    employee = models.User(
        email="admin.employee@cabinet.ma",
        hashed_password=get_password_hash("EmployeePass123!"),
        role=models.UserRole.ADMIN,
        nom_complet="Admin Employee",
        is_active=True,
        is_licensed=True,
        employer_id=dentiste.id,
    )
    db.add(employee)
    db.commit()
    employee_token = _token(client, employee.email, "EmployeePass123!")

    same = client.get("/api/workstation/state", headers=_headers(employee_token))
    assert same.status_code == 200
    assert same.json()["workstationId"] == workstation_id
    assert same.json()["defaultExperience"] is None


def test_mode_change_requires_server_verified_owner_pin(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    state = client.get("/api/workstation/state", headers=_headers(token))
    assert state.status_code == 200

    blocked = client.post(
        "/api/workstation/mode",
        headers=_headers(token),
        json={"mode": "station", "ownerPin": "1234"},
    )
    assert blocked.status_code == 409
    wrong_password = client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "wrong", "newPin": "2468"},
    )
    assert wrong_password.status_code == 403

    configured = client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    )
    assert configured.status_code == 200

    wrong_pin = client.post(
        "/api/workstation/mode",
        headers=_headers(token),
        json={"mode": "station", "ownerPin": "0000"},
    )
    assert wrong_pin.status_code == 403

    changed = client.post(
        "/api/workstation/mode",
        headers=_headers(token),
        json={"mode": "station", "ownerPin": "2468"},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["defaultExperience"] == "station"
    assert changed.json()["stationLocked"] is True
    locked = client.get("/api/workstation/state", headers=_headers(token))
    assert locked.status_code == 200
    assert locked.json()["stationEscapeAuthorized"] is False

    escaped = client.post(
        "/api/workstation/station/escape",
        headers=_headers(token),
        json={"ownerPin": "2468"},
    )
    assert escaped.status_code == 200, escaped.text

    unlocked = client.get("/api/workstation/state", headers=_headers(token))
    assert unlocked.status_code == 200
    assert unlocked.json()["stationEscapeAuthorized"] is True

    audited_actions = {
        action
        for (action,) in db.query(models.AuditLog.action)
        .filter(models.AuditLog.employer_id == dentiste.id)
        .all()
    }
    assert {
        "WORKSTATION_REGISTERED",
        "WORKSTATION_OWNER_PIN_CONFIGURED",
        "WORKSTATION_MODE_CHANGED",
        "WORKSTATION_STATION_ESCAPE_AUTHORIZED",
    }.issubset(audited_actions)


def test_owner_pin_setup_is_primary_owner_only(client, db, dentiste):
    employee = models.User(
        email="employee.only@cabinet.ma",
        hashed_password=get_password_hash("EmployeePass123!"),
        role=models.UserRole.ADMIN,
        nom_complet="Employee",
        is_active=True,
        is_licensed=True,
        employer_id=dentiste.id,
    )
    db.add(employee)
    db.commit()
    token = _token(client, employee.email, "EmployeePass123!")
    response = client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "EmployeePass123!", "newPin": "1357"},
    )
    assert response.status_code == 403


def test_station_escape_is_not_reused_by_another_user_on_same_workstation(client, db, dentiste):
    owner_token = _token(client, dentiste.email, "TestPass123!")
    assert client.get("/api/workstation/state", headers=_headers(owner_token)).status_code == 200
    assert client.post(
        "/api/workstation/owner-pin",
        headers=_headers(owner_token),
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200
    assert client.post(
        "/api/workstation/mode",
        headers=_headers(owner_token),
        json={"mode": "station", "ownerPin": "2468"},
    ).status_code == 200
    assert client.post(
        "/api/workstation/station/escape",
        headers=_headers(owner_token),
        json={"ownerPin": "2468"},
    ).status_code == 200

    employee = models.User(
        email="station.employee@cabinet.ma",
        hashed_password=get_password_hash("EmployeePass123!"),
        role=models.UserRole.ADMIN,
        nom_complet="Station Employee",
        is_active=True,
        is_licensed=True,
        employer_id=dentiste.id,
    )
    db.add(employee)
    db.commit()
    employee_token = _token(client, employee.email, "EmployeePass123!")

    bootstrap = client.get("/api/workstation/bootstrap", headers=_headers(employee_token))
    assert bootstrap.status_code == 200
    assert bootstrap.json()["defaultExperience"] == "station"
    assert bootstrap.json()["stationEscapeAuthorized"] is False

    state = client.get("/api/workstation/state", headers=_headers(employee_token))
    assert state.status_code == 200
    assert state.json()["stationEscapeAuthorized"] is False


def test_workstation_cookie_does_not_cross_tenant_authority(client, db, dentiste):
    first_token = _token(client, dentiste.email, "TestPass123!")
    first = client.get("/api/workstation/state", headers=_headers(first_token))
    assert first.status_code == 200
    first_workstation_id = first.json()["workstationId"]

    other_owner = models.User(
        email="other.owner@cabinet.ma",
        hashed_password=get_password_hash("OtherOwnerPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Other Owner",
        is_active=True,
        is_licensed=True,
        employer_id=None,
    )
    db.add(other_owner)
    db.commit()
    other_token = _token(client, other_owner.email, "OtherOwnerPass123!")

    other = client.get("/api/workstation/state", headers=_headers(other_token))
    assert other.status_code == 200
    assert other.json()["workstationId"] != first_workstation_id
    assert other.json()["defaultExperience"] is None

    bootstrap = client.get("/api/workstation/bootstrap", headers=_headers(other_token))
    assert bootstrap.status_code == 200
    assert bootstrap.json()["workstationId"] == other.json()["workstationId"]
