"""SEC-P1.2c: real JWT/permission and encrypted-disk integration, native vs Python.

This laboratory uses production backend.database, backend.models,
backend.security, backend.routers.auth and backend.routers.agenda_resources
without importing backend.main or opening production data. It substitutes only
the workstation boundary (declared NOT certified), running in a temp cabinet.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
MODULE = "backend.core.key_material"
SOURCE = ROOT / "backend/core/key_material.py"
FIXED = datetime(2026, 1, 2, 12, 0, 0)


def isolated_environment(work: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("DIGITALCROWN_") or key in {
            "DATABASE_URL", "ENVIRONMENT", "CABINET_MASTER_KEY_HEX",
            "SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX", "SECRET_KEY",
            "MEDIA_ROOT", "SUPERADMIN_EMAIL",
        }:
            env.pop(key, None)
    folders = {key: work / key.lower() for key in (
        "DATA", "CONFIG", "RUNTIME", "LOG", "MEDIA",
    )}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    env_path = folders["CONFIG"] / ".env"
    env_path.write_text("ENVIRONMENT=cabinet\n", encoding="utf-8")
    env.update({
        "ENVIRONMENT": "cabinet",
        "DATABASE_URL": "sqlite:///" + str(work / "fixture.db").replace("\\", "/"),
        "SECRET_KEY": "a" * 64,
        "SQLCIPHER_KEY_HEX": "c" * 64,
        "CABINET_MASTER_KEY_HEX": "b" * 64,
        "MOBILE_PAIRING_KEY_HEX": "d" * 64,
        "DIGITALCROWN_ENV_FILE": str(env_path),
        "DIGITALCROWN_USER_DATA_DIR": str(folders["DATA"]),
        "DIGITALCROWN_CONFIG_DIR": str(folders["CONFIG"]),
        "DIGITALCROWN_RUNTIME_DIR": str(folders["RUNTIME"]),
        "DIGITALCROWN_LOG_DIR": str(folders["LOG"]),
        "MEDIA_ROOT": str(folders["MEDIA"]),
        "SUPERADMIN_EMAIL": "none@fixture.invalid",
    })
    return env


def load_native(path: Path) -> None:
    """Inject byte-for-byte Nuitka build before production DB imports."""
    spec = importlib.util.spec_from_file_location(MODULE, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load native key material")
    native = importlib.util.module_from_spec(spec)
    sys.modules[MODULE] = native
    spec.loader.exec_module(native)


def isolate_router_package() -> None:
    """Avoid eager imports in backend.routers.__init__, not the auth modules."""
    if "backend.routers" in sys.modules:
        raise RuntimeError("Real router package was already imported")
    pkg = types.ModuleType("backend.routers")
    pkg.__path__ = [str(ROOT / "backend/routers")]
    sys.modules["backend.routers"] = pkg

    workstation = types.ModuleType("backend.routers.workstation_mode")

    def station_gate(request, db, user, session_jti=None):
        from fastapi import HTTPException
        if request.headers.get("X-Lab-Station") != "fixture-station-authorized":
            raise HTTPException(status_code=403, detail="Synthetic station boundary denied")
    workstation.enforce_authenticated_workstation_access = station_gate
    sys.modules["backend.routers.workstation_mode"] = workstation


def create_fixture() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")

    from backend import database, models
    with database.SessionLocal() as db:
        owner = models.User(
            email="owner@synthetic.invalid", hashed_password="fixture",
            role=models.UserRole.ADMIN, is_active=True, is_licensed=True,
        )
        outsider = models.User(
            email="other@synthetic.invalid", hashed_password="fixture",
            role=models.UserRole.ADMIN, is_active=True, is_licensed=True,
        )
        db.add_all([owner, outsider])
        db.flush()
        allowed = models.User(
            email="allowed@synthetic.invalid", hashed_password="fixture",
            role=models.UserRole.SECRETAIRE, employer_id=owner.id, is_active=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
            permissions={"agenda": True},
        )
        denied = models.User(
            email="denied@synthetic.invalid", hashed_password="fixture",
            role=models.UserRole.SECRETAIRE, employer_id=owner.id, is_active=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
            permissions={"agenda": False},
        )
        inactive = models.User(
            email="inactive@synthetic.invalid", hashed_password="fixture",
            role=models.UserRole.SECRETAIRE, employer_id=owner.id, is_active=False,
            approval_status=models.ApprovalStatus.APPROVED.value,
            permissions={"agenda": True},
        )
        db.add_all([allowed, denied, inactive])
        db.add_all([
            models.AgendaResource(
                employer_id=owner.id, name="Chair Synthetic",
                resource_type="CHAIR", is_active=True,
                created_at=FIXED, updated_at=FIXED,
            ),
            models.AgendaResource(
                employer_id=outsider.id, name="Other Tenant",
                resource_type="ROOM", is_active=True,
                created_at=FIXED, updated_at=FIXED,
            ),
        ])
        db.commit()
    database.engine.dispose()


def exercise(mode: str, native_file: Path | None) -> dict:
    if mode == "native":
        if native_file is None:
            raise RuntimeError("Native library missing")
        load_native(native_file)
    from backend.core.key_material import sqlcipher_passphrase
    if sqlcipher_passphrase() != "c" * 64:
        raise AssertionError("Real key_material contract not used")

    create_fixture()
    isolate_router_package()
    from backend import database, models, security
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.routers import agenda_resources

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(agenda_resources.router, prefix="/api/agenda")
    path = "/api/agenda/resources"
    with database.SessionLocal() as db:
        owners = {u.email.split("@")[0]: u for u in db.query(models.User).all()}
        tokens = {
            name: security.create_access_token({"sub": user.email})
            for name, user in owners.items()
        }
        refresh = security.create_refresh_token({"sub": owners["allowed"].email})
        security.token_blacklist.revoke(tokens["owner"], db)

    calls = [
        ("missing-token", None, None, 401),
        ("malformed-token", "bad-token", "fixture-station-authorized", 401),
        ("refresh-as-access", refresh, "fixture-station-authorized", 401),
        ("revoked-owner", tokens["owner"], "fixture-station-authorized", 401),
        ("inactive", tokens["inactive"], "fixture-station-authorized", 401),
        ("denied-permission", tokens["denied"], "fixture-station-authorized", 403),
        ("station-denied", tokens["allowed"], None, 403),
        ("valid-employee", tokens["allowed"], "fixture-station-authorized", 200),
        ("tenant-isolated", tokens["other"], "fixture-station-authorized", 200),
    ]

    checks = []
    with TestClient(app) as client:
        for name, token, station, status in calls:
            headers = {}
            if token is not None:
                headers["Authorization"] = "Bearer " + token
            if station is not None:
                headers["X-Lab-Station"] = station
            response = client.get(path, headers=headers)
            if response.status_code != status:
                raise AssertionError(
                    f"{name}: expected {status}, got {response.status_code}: "
                    + response.text[:200]
                )
            payload = response.json()
            if name == "valid-employee" and [r["name"] for r in payload] != ["Chair Synthetic"]:
                raise AssertionError("Allowed employee returned unexpected tenant resources")
            if name == "tenant-isolated" and [r["name"] for r in payload] != ["Other Tenant"]:
                raise AssertionError("Other tenant saw resources from another cabinet")
            checks.append((name, response.status_code, payload))
            print(f"REAL AUTH PASS: {name}")

    path_db = Path(os.environ["DATABASE_URL"].replace("sqlite:///", ""))
    if not path_db.exists() or path_db.read_bytes().startswith(b"SQLite format 3"):
        raise AssertionError("SQLCipher file missing or plaintext")
    from sqlcipher3 import dbapi2 as sqlcipher
    wrong = sqlcipher.connect(str(path_db))
    try:
        wrong.execute("PRAGMA key = 'wrong-fixture-key'")
        try:
            wrong.execute("SELECT count(*) FROM users").fetchone()
        except sqlcipher.DatabaseError:
            pass
        else:
            raise AssertionError("Encrypted database accepted an invalid key")
    finally:
        wrong.close()

    with database.SessionLocal() as db:
        if not db.query(models.User).count() == 5:
            raise AssertionError("Fixture user data unexpectedly changed")
        if not security.token_blacklist.is_revoked(
            __import__("jose").jwt.get_unverified_claims(tokens["owner"])["jti"], db
        ):
            raise AssertionError("Real revocation not persisted")
    database.engine.dispose()
    print(f"SEC_P1_2C_AUTH_SCENARIOS={len(checks)}/{len(calls)}")
    print("SEC_P1_2C_SQLCIPHER_REAL_DISK=PASS")
    print("SEC_P1_2C_WORKSTATION=STUBBED_NOT_CERTIFIED")
    print("SEC_P1_2C_DATA=FICTITIOUS_ONLY")
    print("SEC_P1_2C_PACKAGING_CHANGED=NO")
    return {"calls": checks, "mode": mode}


def assert_reopen(mode: str, native_file: Path | None) -> None:
    if mode == "native":
        if native_file is None:
            raise RuntimeError("Native library missing on reopen")
        load_native(native_file)
    from backend import database, models
    from backend.security import TokenBlacklist
    with database.SessionLocal() as db:
        assert db.query(models.User).count() == 5
        assert db.query(models.AgendaResource).count() == 2
        from backend.models import RevokedToken
        assert db.query(RevokedToken).count() >= 1
        assert db.query(RevokedToken).first().jti
    database.engine.dispose()
    print("SEC_P1_2C_REOPEN_FRESH_PROCESS=PASS")


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="dc-sec-p1-2c-") as tmp:
        work = Path(tmp)
        source_copy = work / "sec_p1_2c_key_material.py"
        source_copy.write_bytes(SOURCE.read_bytes())
        compiled_dir = work / "compiled"
        compiled_dir.mkdir()
        build = subprocess.run([
            sys.executable, "-m", "nuitka", "--mode=module", "--nofollow-imports",
            "--output-dir=" + str(compiled_dir), str(source_copy),
        ], cwd=str(work), text=True, capture_output=True, timeout=600, check=False)
        if build.returncode:
            raise RuntimeError(
                f"Nuitka failed ({build.returncode}):\n"
                + (build.stdout + "\n" + build.stderr)[-3000:]
            )
        import importlib.machinery
        libraries = [p for p in compiled_dir.iterdir()
            if p.name.startswith("sec_p1_2c_key_material") and
            any(p.name.endswith(x) for x in importlib.machinery.EXTENSION_SUFFIXES)]
        if len(libraries) != 1:
            raise RuntimeError("Expected exactly one native key-material extension")
        native = libraries[0]
        if platform.system() == "Windows":
            if native.suffix.lower() != ".pyd" or native.read_bytes()[:2] != b"MZ":
                raise AssertionError("Expected Windows PE/PYD")
        elif platform.system() == "Linux":
            if native.read_bytes()[:4] != b"\x7fELF":
                raise AssertionError("Expected Linux ELF")
        else:
            raise RuntimeError("Unsupported OS")

        results = []
        for mode in ("source", "native"):
            case_dir = work / mode
            case_dir.mkdir()
            env = isolated_environment(case_dir)
            target = str(native) if mode == "native" else "-"
            for command in ("--exercise", "--reopen"):
                test = subprocess.run([
                    sys.executable, "-B", str(Path(__file__).resolve()),
                    command, mode, target,
                ], cwd=str(ROOT), env=env, capture_output=True, text=True,
                    timeout=300, check=False)
                if test.returncode:
                    raise RuntimeError(
                        f"{mode} {command} failed ({test.returncode}):\n"
                        + (test.stdout + "\n" + test.stderr)[-4000:]
                    )
                if command == "--exercise":
                    result_line = next((line.removeprefix("RESULT_JSON=")
                        for line in test.stdout.splitlines()
                        if line.startswith("RESULT_JSON=")), None)
                    if result_line is None:
                        raise AssertionError("Missing scenario result from worker")
                    results.append(json.loads(result_line))
                for line in test.stdout.splitlines():
                    if line.startswith(("SEC_P1_2C_", "REAL AUTH PASS:")):
                        print(f"{mode}: {line}")
        # The only expected difference is the build mode itself.
        for record in results:
            record.pop("mode")
        if results[0] != results[1]:
            raise AssertionError("Source/native encrypted auth HTTP behavior diverged")
        print(f"SEC_P1_2C_SOURCE_NATIVE_PARITY=9/9")
        print(f"SEC_P1_2C_NATIVE_PLATFORM={platform.system()}")
        print("SEC_P1_2C_NO_PRODUCTION_DATA=YES")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--exercise":
        record = exercise(sys.argv[2], None if sys.argv[3] == "-" else Path(sys.argv[3]))
        print("RESULT_JSON=" + json.dumps(record, ensure_ascii=False, sort_keys=True))
    elif len(sys.argv) == 4 and sys.argv[1] == "--reopen":
        assert_reopen(sys.argv[2], None if sys.argv[3] == "-" else Path(sys.argv[3]))
    elif len(sys.argv) == 1:
        run()
    else:
        raise SystemExit("SEC-P1.2c invalid invocation")
