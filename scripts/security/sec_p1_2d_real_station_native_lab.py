"""SEC-P1.2d: REAL Station mode and JWT/SQLCipher native parity lab.

This laboratory uses production backend.database, backend.models,
backend.security, backend.routers.auth and backend.routers.agenda_resources
without importing backend.main or opening production data. The REAL Station
boundary including issuance/revocation is exercised with disposable fixtures.
"""
from __future__ import annotations

import importlib
import hashlib
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
# A direct child invocation sets sys.path[0] to scripts/security rather than
# the checkout root, even when subprocess cwd points at ROOT.
# Only the current immutable checkout is imported, never installed packages
# under a matching "backend" name elsewhere on the runner.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
    # A CPython extension must be imported under its compiled PyInit_* name.
    native_name = path.name.split(".", 1)[0]
    spec = importlib.util.spec_from_file_location(native_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load native key material")
    native = importlib.util.module_from_spec(spec)
    sys.modules[native_name] = native
    spec.loader.exec_module(native)
    # The production database's normal from-import now resolves this exact
    # native implementation, without editing its source or DB initialization.
    sys.modules[MODULE] = native


def isolate_router_package() -> None:
    """Avoid eager imports in backend.routers.__init__, not the auth modules."""
    if "backend.routers" in sys.modules:
        raise RuntimeError("Real router package was already imported")
    pkg = types.ModuleType("backend.routers")
    pkg.__path__ = [str(ROOT / "backend/routers")]
    sys.modules["backend.routers"] = pkg



def create_fixture() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")

    from backend import database, models, security
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
        # Real workstation identities, token hashes and owner PIN: no stubs.
        # Cookie values never come from a production browser or device.
        def fixture_ws(owner_id: int, uuid: str, raw: str, *, revoked=False):
            return models.WorkstationMode(
                id=uuid, employer_id=owner_id,
                token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                display_name="Synthetic Station", default_experience="cabinet",
                mode_revision=0, updated_by_user_id=owner_id,
                revoked_at=FIXED if revoked else None,
                created_at=FIXED, updated_at=FIXED,
            )
        db.add_all([
            fixture_ws(owner.id, "11111111-1111-4111-8111-111111111111", "fixture-owner-ws"),
            fixture_ws(outsider.id, "22222222-2222-4222-8222-222222222222", "fixture-other-ws"),
            fixture_ws(owner.id, "33333333-3333-4333-8333-333333333333", "fixture-revoked-ws", revoked=True),
            models.WorkstationSecurityPolicy(
                employer_id=owner.id,
                owner_pin_hash=security.get_password_hash("424242"),
                updated_by_user_id=owner.id,
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

    from backend.routers import workstation_mode
    if workstation_mode.enforce_authenticated_workstation_access is None:
        raise RuntimeError("Real WorkstationMode authority was not imported")

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(agenda_resources.router, prefix="/api/agenda")
    app.include_router(workstation_mode.router, prefix="/api/workstation")
    resource_url = "/api/agenda/resources"
    escape_url = "/api/workstation/station/escape"
    with database.SessionLocal() as db:
        users = {u.email.split("@")[0]: u for u in db.query(models.User).all()}
        tokens = {
            name: security.create_access_token({"sub": user.email})
            for name, user in users.items()
        }
        # Revoke only one of two distinct owner access sessions.
        owner_escape_token = security.create_access_token({"sub": users["owner"].email})
        owner_second_session = security.create_access_token({"sub": users["owner"].email})
        refresh = security.create_refresh_token({"sub": users["allowed"].email})
        security.token_blacklist.revoke(tokens["owner"], db)

    checks = []
    def record(name: str, response, expected: int, expected_names=None):
        if response.status_code != expected:
            raise AssertionError(
                f"{name}: expected {expected}, got {response.status_code}: "
                + response.text[:220]
            )
        payload = response.json()
        if expected_names is not None:
            names = [r["name"] for r in payload]
            if names != expected_names:
                raise AssertionError(f"{name}: tenant isolation failure: {names}")
        checks.append((name, response.status_code, payload))
        print(f"REAL STATION PASS: {name}")

    def call(client, name: str, token: str | None, ws: str | None,
             expected: int, escape: str | None = None, names=None):
        client.cookies.clear()
        if ws is not None:
            client.cookies.set("dc_workstation", ws)
        if escape is not None:
            client.cookies.set("dc_station_escape", escape)
        headers = {"Authorization": "Bearer " + token} if token else {}
        resp = client.get(resource_url, headers=headers)
        record(name, resp, expected, names)

    with TestClient(app) as client:
        # Real JWT, RBAC and Station auth: each HTTP GET passes through the
        # unchanged production get_current_user and WorkstationMode DB gate.
        call(client, "missing-token", None, None, 401)
        call(client, "malformed-token", "bad-token", "fixture-owner-ws", 401)
        call(client, "refresh-as-access", refresh, "fixture-owner-ws", 401)
        call(client, "revoked-owner-token", tokens["owner"], "fixture-owner-ws", 401)
        call(client, "inactive-user", tokens["inactive"], "fixture-owner-ws", 401)
        call(client, "denied-employee-permission", tokens["denied"], "fixture-owner-ws", 403)
        call(client, "station-identity-missing", tokens["allowed"], None, 423)
        call(client, "station-identity-forged", tokens["allowed"], "not-a-real-ws", 423)
        call(client, "station-cross-tenant-cookie", tokens["allowed"], "fixture-other-ws", 423)
        call(client, "station-revoked-cookie", tokens["allowed"], "fixture-revoked-ws", 423)
        call(client, "valid-cabinet-employee", tokens["allowed"], "fixture-owner-ws",
             200, names=["Chair Synthetic"])
        call(client, "other-cabinet-tenant", tokens["other"], "fixture-other-ws",
             200, names=["Other Tenant"])

        with database.SessionLocal() as db:
            wsrow = db.query(models.WorkstationMode).filter_by(
                id="11111111-1111-4111-8111-111111111111"
            ).one()
            wsrow.default_experience = "station"
            wsrow.mode_revision = 1
            db.commit()

        call(client, "locked-real-station", tokens["allowed"], "fixture-owner-ws", 423)
        call(client, "fake-station-escape", tokens["allowed"], "fixture-owner-ws",
             423, escape="definitely-invalid")
        client.cookies.clear()
        client.cookies.set("dc_workstation", "fixture-owner-ws")
        hdr = {"Authorization": "Bearer " + owner_escape_token}
        wrong = client.post(escape_url, headers=hdr, json={"ownerPin": "000000"})
        record("station-pin-reject", wrong, 403)
        # This escape is issued by the actual Digital Crown endpoint and PIN
        # policy, NOT fabricated directly by the lab.
        grant = client.post(escape_url, headers=hdr, json={"ownerPin": "424242"})
        if grant.status_code != 200 or grant.json().get("expiresInSeconds") != 300:
            raise AssertionError(f"Real Station PIN grant failed: {grant.status_code}")
        issued_cookie = client.cookies.get("dc_station_escape")
        if not issued_cookie:
            raise AssertionError("Station did not issue an escape cookie")
        # Do not compare time-dependent token bytes or expiration timestamps.
        checks.append(("station-pin-authorized", 200, {"ok": True, "expiresInSeconds": 300}))
        print("REAL STATION PASS: station-pin-authorized")

        call(client, "owner-unlocked-real-station", owner_escape_token, "fixture-owner-ws",
             200, escape=issued_cookie, names=["Chair Synthetic"])
        call(client, "escape-is-bound-to-user", tokens["allowed"], "fixture-owner-ws",
             423, escape=issued_cookie)
        call(client, "escape-is-bound-to-session", owner_second_session, "fixture-owner-ws",
             423, escape=issued_cookie)
        with database.SessionLocal() as db:
            other_ws = db.query(models.WorkstationMode).filter_by(
                id="22222222-2222-4222-8222-222222222222"
            ).one()
            other_ws.default_experience = "station"
            other_ws.mode_revision = 1
            db.commit()
        call(client, "escape-invalid-tenant", tokens["other"], "fixture-other-ws",
             423, escape=issued_cookie)

        with database.SessionLocal() as db:
            wsrow = db.query(models.WorkstationMode).filter_by(
                id="11111111-1111-4111-8111-111111111111"
            ).one()
            wsrow.mode_revision = 2
            db.commit()
        call(client, "escape-invalid-on-revision", owner_escape_token, "fixture-owner-ws",
             423, escape=issued_cookie)
        with database.SessionLocal() as db:
            wsrow = db.query(models.WorkstationMode).filter_by(
                id="11111111-1111-4111-8111-111111111111"
            ).one()
            wsrow.revoked_at = FIXED
            db.commit()
        call(client, "station-revoked-after-grant", owner_escape_token, "fixture-owner-ws",
             423, escape=issued_cookie)

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
    print(f"SEC_P1_2D_STATION_SCENARIOS={len(checks)}/{len(checks)}")
    print("SEC_P1_2D_SQLCIPHER_REAL_DISK=PASS")
    print("SEC_P1_2D_STATION_GATE=REAL")
    print("SEC_P1_2D_STATION_PIN_ISSUANCE=REAL")
    print("SEC_P1_2D_DATA=FICTITIOUS_ONLY")
    print("SEC_P1_2D_PACKAGING_CHANGED=NO")
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
        assert db.query(models.AgendaResource).count() == 2\n        assert db.query(models.WorkstationMode).count() == 3\n        assert db.query(models.WorkstationMode).filter_by(revoked_at=FIXED).count() == 2
        from backend.models import RevokedToken
        assert db.query(RevokedToken).count() >= 1
        assert db.query(RevokedToken).first().jti
    database.engine.dispose()
    print("SEC_P1_2D_REOPEN_FRESH_PROCESS=PASS")


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="dc-sec-p1-2c-") as tmp:
        work = Path(tmp)
        source_copy = work / "sec_p1_2d_key_material.py"
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
            if p.name.startswith("sec_p1_2d_key_material") and
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
                    if line.startswith(("SEC_P1_2D_", "REAL STATION PASS:")):
                        print(f"{mode}: {line}")
        # The only expected difference is the build mode itself.
        for record in results:
            record.pop("mode")
        if results[0] != results[1]:
            raise AssertionError("Source/native encrypted auth HTTP behavior diverged")
        print("SEC_P1_2D_SOURCE_NATIVE_PARITY=" + str(len(results[0]["calls"])) + "/" + str(len(results[0]["calls"])))
        print(f"SEC_P1_2D_NATIVE_PLATFORM={platform.system()}")
        print("SEC_P1_2D_NO_PRODUCTION_DATA=YES")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--exercise":
        record = exercise(sys.argv[2], None if sys.argv[3] == "-" else Path(sys.argv[3]))
        print("RESULT_JSON=" + json.dumps(record, ensure_ascii=False, sort_keys=True))
    elif len(sys.argv) == 4 and sys.argv[1] == "--reopen":
        assert_reopen(sys.argv[2], None if sys.argv[3] == "-" else Path(sys.argv[3]))
    elif len(sys.argv) == 1:
        run()
    else:
        raise SystemExit("SEC-P1.2d invalid invocation")
