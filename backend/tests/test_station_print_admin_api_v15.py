"""Isolated FastAPI HTTP tests for LOT04.8-B2c; all identities are synthetic.

This test deliberately stubs auth/PIN dependencies (not a proof of the
production login/workstation implementation) but uses the REAL router,
FastAPI validation, SQLite transaction store and trusted Station inventory.
"""
import importlib
import sys
import types

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table,
    create_engine, insert, select,
)
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from backend.services.station_document_print_store import (
    audit, configuration, schema,
)


class FakeUser:
    def __init__(self, user_id=10, employer_id=None):
        self.id = user_id
        self.employer_id = employer_id

    def get_employer_id(self):
        return self.id if self.employer_id is None else self.employer_id


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///" + str(tmp_path / "isolated-configuration.sqlite"),
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    workstation = Table(
        "workstation_modes", MetaData(),
        Column("id", String(36), primary_key=True),
        Column("employer_id", Integer, nullable=False),
        Column("default_experience", String(32)),
        Column("revoked_at", DateTime()),
    )
    workstation.metadata.create_all(engine)
    schema.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(workstation), [{
            "id": "station-10", "employer_id": 10,
            "default_experience": "station", "revoked_at": None,
        }])

    # Stub auth and PIN only inside this isolated test fixture; HTTP body,
    # FastAPI routing and SQLAlchemy store implementation are not mocked.
    fake_database = types.ModuleType("backend.database")
    fake_database.get_db = lambda: None
    fake_models = types.ModuleType("backend.models")
    fake_models.User = FakeUser
    fake_auth = types.ModuleType("backend.routers.auth")
    fake_auth.get_current_user = lambda: None
    fake_workstation = types.ModuleType("backend.routers.workstation_mode")

    def check_pin(_db, _user, pin):
        if pin != "1234":
            raise HTTPException(status_code=403, detail="Invalid owner PIN")
    fake_workstation._require_pin = check_pin

    utils = types.ModuleType("backend.utils")
    utils.__path__ = ["backend/utils"]
    fake_rate = types.ModuleType("backend.utils.rate_limit")
    fake_rate.enforce_failure_rate_limit = lambda *args, **kwargs: None
    fake_rate.record_rate_limit_failure = lambda *args, **kwargs: None
    routers = types.ModuleType("backend.routers")
    routers.__path__ = ["backend/routers"]

    for name, obj in (
        ("backend.database", fake_database),
        ("backend.models", fake_models),
        ("backend.routers", routers),
        ("backend.routers.auth", fake_auth),
        ("backend.routers.workstation_mode", fake_workstation),
        ("backend.utils", utils),
        ("backend.utils.rate_limit", fake_rate),
    ):
        monkeypatch.setitem(sys.modules, name, obj)
    monkeypatch.delitem(sys.modules, "backend.routers.station_print_config_admin", raising=False)
    route = importlib.import_module("backend.routers.station_print_config_admin")
    app = FastAPI()
    app.include_router(route.router, prefix="/api/admin")
    current = {"user": FakeUser()}

    def session_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[route.get_db] = session_override
    app.dependency_overrides[route.get_current_user] = lambda: current["user"]
    with TestClient(app, base_url="https://cabinet.example") as client:
        client.cookies.set("access_token", "fake-for-testing-only")
        yield client, current, engine
    engine.dispose()


def safe_headers():
    return {"origin": "https://cabinet.example", "sec-fetch-site": "same-origin"}


def disable_payload(rev=0, pin="1234"):
    return {
        "expectedRevision": rev, "ownerPin": pin, "mode": "disabled",
        "stationIds": [], "printerIds": [],
    }


def test_get_status_is_owner_only_and_default_disabled(api):
    client, current, engine = api
    r = client.get("/api/admin/station-print-config")
    assert r.status_code == 200
    assert r.json() == {
        "mode": "disabled", "revision": 0, "status": "not_configured",
        "printingAvailable": False, "configurationEnableSupported": False,
    }
    assert r.headers["cache-control"] == "no-store"
    current["user"] = FakeUser(11, 10)
    assert client.get("/api/admin/station-print-config").status_code == 403


def test_disable_uses_real_transaction_audit_and_stale_revision_refused(api):
    client, _, engine = api
    r = client.put(
        "/api/admin/station-print-config",
        json=disable_payload(), headers=safe_headers(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["revision"] == 1
    assert r.json()["printingAvailable"] is False
    assert r.headers["cache-control"] == "no-store"
    stale = client.put(
        "/api/admin/station-print-config",
        json=disable_payload(), headers=safe_headers(),
    )
    assert stale.status_code == 409
    with engine.connect() as conn:
        assert conn.execute(select(configuration.c.mode)).scalar_one() == "disabled"
        assert conn.execute(select(audit.c.revision)).scalars().all() == [1]


@pytest.mark.parametrize("bad_headers", [
    {"origin": "https://evil.example", "sec-fetch-site": "same-origin"},
    {"origin": "https://cabinet.example", "sec-fetch-site": "cross-site"},
    {"sec-fetch-site": "same-origin"},
])
def test_cookie_csrf_denied_without_mutation(api, bad_headers):
    client, _, engine = api
    result = client.put(
        "/api/admin/station-print-config",
        json=disable_payload(), headers=bad_headers,
    )
    assert result.status_code == 403, result.text
    with engine.connect() as conn:
        assert conn.execute(select(configuration.c.tenant_id)).all() == []


def test_employee_cannot_write_even_with_owner_pin(api):
    client, current, engine = api
    current["user"] = FakeUser(11, 10)
    r = client.put(
        "/api/admin/station-print-config",
        json=disable_payload(), headers=safe_headers(),
    )
    assert r.status_code == 403
    with engine.connect() as conn:
        assert conn.execute(select(configuration.c.tenant_id)).all() == []


@pytest.mark.parametrize("invalid", [
    {**disable_payload(), "mode": "both"},
    {**disable_payload(), "printerIds": ["desk-1"]},
    {**disable_payload(), "secureReleaseVerified": True},
    {**disable_payload(), "expectedRevision": -1},
])
def test_no_browser_enablement_or_forged_certification(api, invalid):
    client, _, engine = api
    r = client.put(
        "/api/admin/station-print-config", json=invalid,
        headers=safe_headers(),
    )
    assert r.status_code == 422, r.text
    with engine.connect() as conn:
        assert conn.execute(select(configuration.c.tenant_id)).all() == []


def test_wrong_pin_denied_before_save(api):
    client, _, engine = api
    r = client.put(
        "/api/admin/station-print-config",
        json=disable_payload(pin="9999"), headers=safe_headers(),
    )
    assert r.status_code == 403
    with engine.connect() as conn:
        assert conn.execute(select(configuration.c.tenant_id)).all() == []
