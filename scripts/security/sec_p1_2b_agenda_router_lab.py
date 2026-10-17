"""SEC-P1.2b: real Agenda Resources router, native-vs-source HTTP parity lab.

Uses the exact Digital Crown router and Pydantic schema, but replaces
authentication and persistence with fail-closed synthetic test dependencies
and an ephemeral SQLite in-memory model. Never imports backend.main or real DB.
"""
from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import tempfile
import types
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
ROUTER_SOURCE = ROOT / "backend/routers/agenda_resources.py"
SCHEMA_SOURCE = ROOT / "backend/schemas/agenda_resources.py"
NATIVE_NAME = "sec_p12b_agenda_resources"
FIXED_TIME = datetime(2026, 1, 2, 12, 0, 0)
FACTORY: sessionmaker | None = None


class Base(DeclarativeBase):
    pass


class AgendaResource(Base):
    """Ephemeral ORM substitute; uses the actual router's query operations."""
    __tablename__ = "lab_agenda_resources"
    __table_args__ = (UniqueConstraint("employer_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: FIXED_TIME)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: FIXED_TIME)


class SyntheticUser:
    def __init__(self, tenant: int):
        self.tenant = tenant

    def get_employer_id(self) -> int:
        return self.tenant


def get_db():
    if FACTORY is None:
        raise RuntimeError("SEC-P1.2b synthetic DB not provisioned")
    with FACTORY() as db:
        yield db


def require_permission(permission: str):
    # This is a laboratory substitute. It is NOT production auth/RBAC.
    if permission != "agenda":
        raise RuntimeError("Unexpected permission requested by real router")

    def authorized(
        x_lab_token: str = Header(default=""),
        x_lab_tenant: int = Header(default=101),
    ) -> SyntheticUser:
        if x_lab_token != "fixture-token-only":
            raise HTTPException(status_code=401, detail="synthetic auth required")
        if x_lab_tenant not in (101, 202):
            raise HTTPException(status_code=403, detail="synthetic tenant denied")
        return SyntheticUser(x_lab_tenant)

    return authorized


def _package(name: str, folder: Path) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = [str(folder)]
    sys.modules[name] = module
    return module


def install_test_imports() -> None:
    """Prevent real backend DB, auth, models and eager router imports."""
    backend = _package("backend", ROOT / "backend")
    routers = _package("backend.routers", ROOT / "backend/routers")
    schemas = _package("backend.schemas", ROOT / "backend/schemas")
    backend.routers = routers
    backend.schemas = schemas

    database = types.ModuleType("backend.database")
    database.get_db = get_db
    models = types.ModuleType("backend.models")
    models.User = SyntheticUser
    models.AgendaResource = AgendaResource
    auth = types.ModuleType("backend.routers.auth")
    auth.require_permission = require_permission
    for name, module in (
        ("backend.database", database),
        ("backend.models", models),
        ("backend.routers.auth", auth),
    ):
        sys.modules[name] = module
    backend.database = database
    backend.models = models
    routers.auth = auth
    importlib.import_module("backend.schemas.agenda_resources")


def suite(router) -> list[dict]:
    """Run identical sequential real-route calls against a fresh empty DB."""
    global FACTORY
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    FACTORY = sessionmaker(bind=engine, expire_on_commit=False)
    with FACTORY() as db:
        db.add_all([
            AgendaResource(id=1, employer_id=101, name="Fauteuil A", resource_type="CHAIR"),
            AgendaResource(id=2, employer_id=101, name="Salle A", resource_type="ROOM", is_active=False),
            AgendaResource(id=3, employer_id=202, name="Autre cabinet", resource_type="CHAIR"),
        ])
        db.commit()

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(router, prefix="/api/agenda")
    root = "/api/agenda/resources"
    user1 = {"X-Lab-Token": "fixture-token-only", "X-Lab-Tenant": "101"}
    user2 = {"X-Lab-Token": "fixture-token-only", "X-Lab-Tenant": "202"}
    wrong_tenant = {"X-Lab-Token": "fixture-token-only", "X-Lab-Tenant": "999"}
    calls = [
        ("GET", root, None, {}, 401),
        ("GET", root, None, wrong_tenant, 403),
        ("GET", root, None, user1, 200),
        ("GET", root + "?include_inactive=true", None, user1, 200),
        ("GET", root, None, user2, 200),
        ("POST", root, {"name": "  Studio  ", "resource_type": "OTHER"}, user1, 201),
        ("POST", root, {"name": "Studio", "resource_type": "OTHER"}, user1, 409),
        ("POST", root, {"name": "", "resource_type": "ROOM"}, user1, 422),
        ("POST", root, {"name": "Invalid", "resource_type": "VAN"}, user1, 422),
        ("POST", root, {"name": "Unauthorized", "resource_type": "CHAIR"}, {}, 401),
        ("PATCH", root + "/999", {"name": "Lost"}, user1, 404),
        ("PATCH", root + "/3", {"name": "Cross tenant"}, user1, 404),
        ("PATCH", root + "/1", {"name": " Fauteuil X "}, user1, 200),
        ("PATCH", root + "/1", {"name": "Salle A"}, user1, 409),
        ("PATCH", root + "/1", {"name": ""}, user1, 422),
        ("GET", root + "?include_inactive=true", None, user1, 200),
        ("GET", root, None, user2, 200),
    ]
    evidence: list[dict] = []
    try:
        with TestClient(app) as client:
            for index, (method, path, body, headers, expected) in enumerate(calls, 1):
                response = client.request(method, path, json=body, headers=headers)
                if response.status_code != expected:
                    raise AssertionError(
                        f"Scenario {index} {method} {path}: "
                        f"expected {expected} got {response.status_code}: {response.text[:200]}"
                    )
                data = response.json()
                if index == 3 and ([item["id"] for item in data] != [1]):
                    raise AssertionError("Inactive or cross-tenant resource leaked")
                if index == 4 and ([item["id"] for item in data] != [1, 2]):
                    raise AssertionError("Inactive scope not honored")
                if index in (5, 17) and [item["id"] for item in data] != [3]:
                    raise AssertionError("Cross-tenant access detected")
                if index == 6 and data["name"] != "Studio":
                    raise AssertionError("Create did not normalize whitespace")
                if index == 13 and data["name"] != "Fauteuil X":
                    raise AssertionError("Update did not normalize whitespace")
                evidence.append({"status": response.status_code, "body": data})
                print(f"REAL ROUTE PASS {index}/{len(calls)}")
        return evidence
    finally:
        FACTORY = None
        engine.dispose()


def verify(compiled_path: Path) -> None:
    if not (ROUTER_SOURCE.is_file() and SCHEMA_SOURCE.is_file()):
        raise RuntimeError("Missing real Digital Crown router or schema")
    install_test_imports()
    # Loads the unmodified real router source, not recreated endpoints.
    original = runpy.run_path(str(ROUTER_SOURCE), run_name="__sec_p12b_reference__")
    with compiled_path.open("rb") as native_binary:
        header = native_binary.read(4)
    system = platform.system()
    if system == "Windows":
        if compiled_path.suffix.lower() != ".pyd" or not header.startswith(b"MZ"):
            raise AssertionError("Expected native PE/PYD on Windows")
    elif system == "Linux":
        if not header.startswith(b"\x7fELF"):
            raise AssertionError("Expected native ELF on Linux")
    else:
        raise RuntimeError(f"Unsupported experimental OS: {system}")

    spec = importlib.util.spec_from_file_location(NATIVE_NAME, compiled_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import compiled real router")
    compiled = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiled)

    before = suite(original["router"])
    after = suite(compiled.router)
    if before != after:
        for idx, (a, b) in enumerate(zip(before, after, strict=True), 1):
            if a != b:
                raise AssertionError(f"Real router native HTTP mismatch, scenario {idx}")
    print(f"SEC_P1_2B_REAL_ROUTER_PARITY={len(before)}/{len(before)}")
    print("SEC_P1_2B_ROUTER=backend/routers/agenda_resources.py")
    print("SEC_P1_2B_SCHEMA=backend/schemas/agenda_resources.py")
    print(f"SEC_P1_2B_NATIVE_PLATFORM={system}")
    print("SEC_P1_2B_DATA=synthetic-memory-only")
    print("SEC_P1_2B_AUTH=stubbed-not-certified")
    print("SEC_P1_2B_RELEASE_PACKAGING_CHANGED=NO")


def run_lab() -> None:
    if not (ROUTER_SOURCE.is_file() and SCHEMA_SOURCE.is_file()):
        raise RuntimeError("Missing actual Agenda Resources router/schema")
    with tempfile.TemporaryDirectory(prefix="dc-sec-p12b-") as temp:
        work = Path(temp)
        copied_source = work / f"{NATIVE_NAME}.py"
        copied_source.write_bytes(ROUTER_SOURCE.read_bytes())
        out_dir = work / "native"
        out_dir.mkdir()
        compile_result = subprocess.run([
            sys.executable, "-m", "nuitka", "--mode=module", "--nofollow-imports",
            "--output-dir=" + str(out_dir), str(copied_source),
        ], cwd=str(work), capture_output=True, text=True, timeout=600, check=False)
        if compile_result.returncode:
            raise RuntimeError(
                f"Compile real router failed ({compile_result.returncode}):\n"
                + (compile_result.stdout + "\n" + compile_result.stderr)[-3000:]
            )
        libraries = [
            p for p in out_dir.iterdir()
            if p.name.startswith(NATIVE_NAME)
            and any(p.name.endswith(ext) for ext in importlib.machinery.EXTENSION_SUFFIXES)
        ]
        if len(libraries) != 1:
            raise RuntimeError("Expected exactly one native router extension")
        worker = subprocess.run([
            sys.executable, str(Path(__file__).resolve()), "--verify-native", str(libraries[0]),
        ], cwd=str(work), capture_output=True, text=True, timeout=120, check=False)
        if worker.returncode:
            raise RuntimeError(
                f"Real router verification failed ({worker.returncode}):\n"
                + (worker.stdout + "\n" + worker.stderr)[-3000:]
            )
        print(worker.stdout, end="")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-native":
        verify(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        run_lab()
    else:
        raise SystemExit("SEC-P1.2b unsupported command")
