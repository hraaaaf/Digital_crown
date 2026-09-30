import pytest

from backend import models
from backend.routers.mobile import _create_mobile_jwt
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_workstation_rate_limit(monkeypatch, tmp_path):
    from backend.utils import rate_limit

    monkeypatch.setattr(rate_limit, "_store_path", lambda: tmp_path / "workstation_rate_limit.json")
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = True
    yield
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False


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


def _configure_station(client, token: str) -> str:
    state = client.get("/api/workstation/state", headers=_headers(token))
    assert state.status_code == 200, state.text
    assert client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200
    changed = client.post(
        "/api/workstation/mode",
        headers=_headers(token),
        json={"mode": "station", "ownerPin": "2468"},
    )
    assert changed.status_code == 200, changed.text
    return changed.json()["workstationId"]


def test_ghost_insights_websocket_is_rejected_when_station_locked(client, db, dentiste):
    from starlette.websockets import WebSocketDisconnect

    token = _token(client, dentiste.email, "TestPass123!")
    _configure_station(client, token)

    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(
            f"/api/ai/ws/ghost-insights/{dentiste.id}?token={token}",
        ) as websocket:
            websocket.receive_json()
    assert closed.value.code == 1008


def test_ghost_insights_websocket_enforces_patients_permission(client, db, dentiste):
    from starlette.websockets import WebSocketDisconnect

    restricted = models.User(
        email="restricted.ws@cabinet.ma",
        hashed_password=get_password_hash("RestrictedPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Restricted WS",
        is_active=True,
        is_licensed=True,
        employer_id=dentiste.id,
        permissions={"agenda": True, "patients": False},
    )
    db.add(restricted)
    db.commit()
    token = _token(client, restricted.email, "RestrictedPass123!")

    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(
            f"/api/ai/ws/ghost-insights/{dentiste.id}?token={token}",
        ) as websocket:
            websocket.receive_json()
    assert closed.value.code == 1008


def test_ghost_insights_websocket_enforces_active_license(client, db, dentiste):
    from starlette.websockets import WebSocketDisconnect

    token = _token(client, dentiste.email, "TestPass123!")
    dentiste.is_licensed = False
    db.commit()

    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(
            f"/api/ai/ws/ghost-insights/{dentiste.id}?token={token}",
        ) as websocket:
            websocket.receive_json()
    assert closed.value.code == 1008


def test_ghost_insights_websocket_rejects_mobile_jwt(client, db, dentiste):
    from starlette.websockets import WebSocketDisconnect

    # Ghost insights is a Cabinet desktop channel. Pocket JWTs have a separate,
    # device-bound trust boundary and must never authenticate this socket.
    mobile_token = _create_mobile_jwt(
        dentiste.id,
        "DENTISTE",
        dentiste.id,
    )

    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect(
            f"/api/ai/ws/ghost-insights/{dentiste.id}?token={mobile_token}",
        ) as websocket:
            websocket.receive_json()
    assert closed.value.code == 1008


def test_ghost_insights_websocket_revalidates_after_cabinet_to_station(client, db, dentiste, monkeypatch):
    from starlette.websockets import WebSocketDisconnect
    from backend.routers import ai_feedback

    token = _token(client, dentiste.email, "TestPass123!")
    state = client.get("/api/workstation/state", headers=_headers(token))
    assert state.status_code == 200, state.text
    assert client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200

    original_sleep = ai_feedback.asyncio.sleep
    async def _fast_sleep(_seconds):
        await original_sleep(0.01)
    monkeypatch.setattr(ai_feedback.asyncio, "sleep", _fast_sleep)

    with client.websocket_connect(
        f"/api/ai/ws/ghost-insights/{dentiste.id}?token={token}",
    ) as websocket:
        first = websocket.receive_json()
        assert "insights" in first

        changed = client.post(
            "/api/workstation/mode",
            headers=_headers(token),
            json={"mode": "station", "ownerPin": "2468"},
        )
        assert changed.status_code == 200, changed.text

        with pytest.raises(WebSocketDisconnect) as closed:
            websocket.receive_json()
        assert closed.value.code == 1008


def test_station_backend_blocks_clinical_api_and_escape_is_session_bound(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    _configure_station(client, token)

    for path in (
        "/api/patients/",
        "/api/mobile/bridge-options",
        "/api/patient-companion/admin/patients/999/status",
    ):
        blocked = client.get(path, headers=_headers(token))
        assert blocked.status_code == 423, f"{path}: {blocked.text}"
        assert blocked.json()["detail"] == "WORKSTATION_STATION_LOCKED"

    escaped = client.post(
        "/api/workstation/station/escape",
        headers=_headers(token),
        json={"ownerPin": "2468"},
    )
    assert escaped.status_code == 200, escaped.text
    assert escaped.json()["expiresAt"] > 0

    allowed = client.get("/api/patients/", headers=_headers(token))
    assert allowed.status_code == 200, allowed.text

    # Same user, new access session/JTI: the previous Station escape must not carry over.
    second_token = _token(client, dentiste.email, "TestPass123!")
    stale_escape = client.get("/api/patients/", headers=_headers(second_token))
    assert stale_escape.status_code == 423, stale_escape.text
    state = client.get("/api/workstation/state", headers=_headers(second_token))
    assert state.status_code == 200
    assert state.json()["stationEscapeAuthorized"] is False


def test_station_lock_is_workstation_scoped_and_does_not_capture_paired_mobile(client, db, dentiste):
    desktop_token = _token(client, dentiste.email, "TestPass123!")
    _configure_station(client, desktop_token)

    # The enrolled desktop is locked even with a valid cabinet access session.
    blocked = client.get("/api/patients/", headers=_headers(desktop_token))
    assert blocked.status_code == 423, blocked.text
    assert blocked.json()["detail"] == "WORKSTATION_STATION_LOCKED"

    # Pocket is a separate paired-device trust boundary. The workstation cookie
    # carried by this TestClient must not globally lock an independently paired mobile.
    device_id = "00000000-0000-4000-8000-000000000003"
    db.add(models.MobilePairedDevice(
        device_id=device_id,
        user_id=dentiste.id,
        employer_id=dentiste.id,
        client_public_key_hex="04" + ("11" * 64),
        refresh_jti="workstation-scope-mobile-refresh",
    ))
    db.commit()
    mobile_token = _create_mobile_jwt(dentiste.id, "DENTISTE", dentiste.id, device_id)

    mobile = client.get("/api/mobile/patients", headers=_headers(mobile_token))
    assert mobile.status_code == 200, mobile.text


def test_station_escape_replay_is_rejected_after_mode_change(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    _configure_station(client, token)
    escaped = client.post(
        "/api/workstation/station/escape",
        headers=_headers(token),
        json={"ownerPin": "2468"},
    )
    assert escaped.status_code == 200, escaped.text
    captured_escape = client.cookies.get("dc_station_escape")
    assert captured_escape

    for mode in ("cabinet", "station"):
        changed = client.post(
            "/api/workstation/mode",
            headers=_headers(token),
            json={"mode": mode, "ownerPin": "2468"},
        )
        assert changed.status_code == 200, changed.text

    client.cookies.set("dc_station_escape", captured_escape)
    replay = client.get("/api/patients/", headers=_headers(token))
    assert replay.status_code == 423, replay.text
    assert replay.json()["detail"] == "WORKSTATION_STATION_LOCKED"


def test_station_escape_replay_is_rejected_after_pin_rotation(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    _configure_station(client, token)
    escaped = client.post(
        "/api/workstation/station/escape",
        headers=_headers(token),
        json={"ownerPin": "2468"},
    )
    assert escaped.status_code == 200, escaped.text
    captured_escape = client.cookies.get("dc_station_escape")
    assert captured_escape

    rotated = client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!", "newPin": "1357"},
    )
    assert rotated.status_code == 200, rotated.text

    client.cookies.set("dc_station_escape", captured_escape)
    replay = client.get("/api/patients/", headers=_headers(token))
    assert replay.status_code == 423, replay.text
    assert replay.json()["detail"] == "WORKSTATION_STATION_LOCKED"


def test_lost_or_tampered_workstation_identity_is_fail_closed_until_owner_reenrolls(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    initial = client.get("/api/workstation/state", headers=_headers(token))
    assert initial.status_code == 200
    first_id = initial.json()["workstationId"]

    client.cookies.delete("dc_workstation")
    blocked = client.get("/api/patients/", headers=_headers(token))
    assert blocked.status_code == 423
    assert blocked.json()["detail"] == "WORKSTATION_IDENTITY_REQUIRED"

    state = client.get("/api/workstation/state", headers=_headers(token))
    assert state.status_code == 423
    assert state.json()["detail"] == "WORKSTATION_ENROLLMENT_REQUIRED"

    bootstrap = client.get("/api/workstation/bootstrap", headers=_headers(token))
    assert bootstrap.status_code == 200
    assert bootstrap.json()["enrollmentRequired"] is True

    client.cookies.set("dc_workstation", "tampered-token")
    tampered = client.get("/api/patients/", headers=_headers(token))
    assert tampered.status_code == 423
    assert tampered.json()["detail"] == "WORKSTATION_IDENTITY_REQUIRED"
    client.cookies.delete("dc_workstation")

    rejected = client.post(
        "/api/workstation/enroll",
        headers=_headers(token),
        json={"accountPassword": "wrong"},
    )
    assert rejected.status_code == 403

    reenrolled = client.post(
        "/api/workstation/enroll",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!"},
    )
    assert reenrolled.status_code == 200, reenrolled.text
    assert reenrolled.json()["workstationId"] != first_id
    assert reenrolled.json()["enrollmentRequired"] is False

    allowed = client.get("/api/patients/", headers=_headers(token))
    assert allowed.status_code == 200, allowed.text


def test_workstation_pin_rate_limit_counts_failures_not_successes(client, db, dentiste):
    token = _token(client, dentiste.email, "TestPass123!")
    assert client.get("/api/workstation/state", headers=_headers(token)).status_code == 200
    assert client.post(
        "/api/workstation/owner-pin",
        headers=_headers(token),
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200

    # Legitimate successful privileged actions do not consume the failure budget.
    for mode in ["cabinet", "control_center", "cabinet", "control_center", "cabinet", "control_center"]:
        response = client.post(
            "/api/workstation/mode",
            headers=_headers(token),
            json={"mode": mode, "ownerPin": "2468"},
        )
        assert response.status_code == 200, response.text

    for _ in range(5):
        wrong = client.post(
            "/api/workstation/mode",
            headers=_headers(token),
            json={"mode": "station", "ownerPin": "0000"},
        )
        assert wrong.status_code == 403, wrong.text

    limited = client.post(
        "/api/workstation/mode",
        headers=_headers(token),
        json={"mode": "station", "ownerPin": "0000"},
    )
    assert limited.status_code == 429, limited.text
    assert int(limited.headers["Retry-After"]) > 0

    actions = [
        action
        for (action,) in db.query(models.AuditLog.action)
        .filter(models.AuditLog.employer_id == dentiste.id)
        .all()
    ]
    assert actions.count("WORKSTATION_MODE_REJECTED") >= 5
    assert "WORKSTATION_MODE_RATE_LIMITED" in actions


def test_logout_revokes_station_escape_cookie(client, db, dentiste):
    login = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")

    _configure_station(client, token)
    assert client.post(
        "/api/workstation/station/escape",
        headers=_headers(token),
        json={"ownerPin": "2468"},
    ).status_code == 200
    assert client.cookies.get("dc_station_escape")

    logged_out = client.post(
        "/api/auth/logout",
        headers=_headers(token),
        json={"refresh_token": refresh_token},
    )
    assert logged_out.status_code == 204, logged_out.text
    assert client.cookies.get("dc_station_escape") is None


def test_expired_station_escape_is_rejected_by_backend(client, db, dentiste):
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from backend.security import ALGORITHM, SECRET_KEY

    token = _token(client, dentiste.email, "TestPass123!")
    workstation_id = _configure_station(client, token)
    access_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    stale_escape = jwt.encode(
        {
            "type": "workstation_escape",
            "wsid": workstation_id,
            "tenant": dentiste.id,
            "sub": str(dentiste.id),
            "sid": access_payload["jti"],
            "iat": expired - timedelta(minutes=5),
            "exp": expired,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    client.cookies.set("dc_station_escape", stale_escape)

    state = client.get("/api/workstation/state", headers=_headers(token))
    assert state.status_code == 200
    assert state.json()["stationEscapeAuthorized"] is False
    assert state.json()["stationEscapeExpiresAt"] is None

    blocked = client.get("/api/patients/", headers=_headers(token))
    assert blocked.status_code == 423
    assert blocked.json()["detail"] == "WORKSTATION_STATION_LOCKED"


def test_failure_rate_limiter_is_thread_safe(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi import HTTPException
    from starlette.requests import Request
    from backend.utils import rate_limit

    monkeypatch.setattr(rate_limit, "_store_path", lambda: tmp_path / "thread_rate_limit.json")
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = True

    request = Request({"type": "http", "client": ("127.0.0.1", 4242), "headers": []})
    scope = "workstation-concurrent-test"

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _index: rate_limit.record_rate_limit_failure(request, scope), range(20)))

    key = f"{scope}:127.0.0.1"
    assert rate_limit._attempts[key][0] == 20
    with pytest.raises(HTTPException) as exc:
        rate_limit.enforce_failure_rate_limit(request, scope, max_attempts=5)
    assert exc.value.status_code == 429
