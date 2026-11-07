#!/usr/bin/env python3
"""RESTORE-03 Windows GitHub-only real source backend + P4 persistence rehearsal.

No EXE build or cabinet installation is attempted. A production EXE requires
INSTALLABLE_CERTIFIED, and DigitalCrown.spec MUST reject uncertified checkouts.
Starts the real run.py FastAPI backend after explicit Alembic migration on an
independently attested, disposable SQLCipher test database. Checks /health over
real loopback HTTP and portable rebind persisted through actual SQLAlchemy.
No patient data, Firebase secrets, scientific model substitutes, or Vercel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MARKER = "RESTORE03_WINDOWS_NATIVE_SOURCE_RUNTIME_NOT_INSTALLABLE_NO_CLINICAL_GO"
PROOF = "restore03-windows-source-runtime-lab-evidence.json"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _env_and_target(work: Path) -> tuple[dict[str, str], Path, int]:
    # Fail closed on inherited clinical DB/appdata/keys; supply isolated values.
    for name in (
        "DATABASE_URL", "DIGITALCROWN_USER_DATA_DIR", "DIGITALCROWN_ENV_FILE",
        "SQLCIPHER_KEY_HEX", "CABINET_MASTER_KEY_HEX", "MEDIA_ROOT",
    ):
        _assert(not os.getenv(name), "INHERITED_CLINICAL_ENV_PRESENT:" + name)
    from backend.core.runtime_safety import database_target_fingerprint

    db = work / "rehearsal-clinical_vault-SYNTHETIC.db"
    db_url = "sqlite:///" + db.as_posix()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "restore03_rehearsal",
        "DEBUG": "false",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DIGITALCROWN_ISOLATION_DB_FINGERPRINT": database_target_fingerprint(db_url),
        "DATABASE_URL": db_url,
        "SECRET_KEY": secrets.token_hex(32),
        "CABINET_MASTER_KEY_HEX": secrets.token_hex(32),
        "SQLCIPHER_KEY_HEX": secrets.token_hex(32),
        "MOBILE_PAIRING_KEY_HEX": secrets.token_hex(32),
        "PAIRING_CODE_PEPPER": secrets.token_hex(32),
        "DIGITALCROWN_USER_DATA_DIR": str(work / "rehearsal-data"),
        "DIGITALCROWN_CONFIG_DIR": str(work / "rehearsal-config"),
        "DIGITALCROWN_RUNTIME_DIR": str(work / "rehearsal-runtime"),
        "DIGITALCROWN_LOG_DIR": str(work / "rehearsal-logs"),
        "MEDIA_ROOT": str(work / "rehearsal-media"),
        "CABINET_HOST": "127.0.0.1",
        "CABINET_PORT": str(port),
        "ALLOWED_ORIGINS": f"http://127.0.0.1:{port}",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
        "PATIENT_COMPANION_RELAY_URL": "",
        "PATIENT_COMPANION_RELAY_BOOTSTRAP_SECRET": "",
        "PATIENT_COMPANION_TURN_SECRET": "",
        "SENTRY_DSN": "",
        "DIGITALCROWN_RESTORE_RESTART": "1",
        "PYTHONPATH": str(ROOT),
    })
    return env, db, port


def _subprocess(label: str, cmd: list[str], env: dict[str, str], work: Path) -> None:
    with (work / (label + "-private.log")).open("wb") as log:
        result = subprocess.run(
            cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            check=False, timeout=200,
        )
    _assert(result.returncode == 0, label.upper() + "_FAILED")


def _assert_uncertified_spec_refusal(env: dict[str, str], work: Path) -> None:
    """Run REAL PyInstaller spec; refuse packaging without genuine certificates."""
    from backend.release_certification import (
        ReleaseCertificationError, verify_installable_release_directory,
    )

    try:
        verify_installable_release_directory(ROOT)
    except ReleaseCertificationError as exc:
        _assert("Missing release-certification.json" in str(exc), "UNEXPECTED_CERT_GATE")
    else:
        raise AssertionError("UNEXPECTED_INSTALLABLE_CERTIFICATION_IN_PR_CHECKOUT")

    proc = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", str(work / "forbidden-executable-dist"),
            "--workpath", str(work / "forbidden-work"),
            str(ROOT / "DigitalCrown.spec"),
        ],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False, timeout=120,
    )
    detail = proc.stdout.decode("utf-8", errors="replace")
    # Fail on unrelated build errors: they do not prove the protection works.
    _assert(
        proc.returncode != 0
        and "Missing release-certification.json" in detail
        and "ReleaseCertificationError" in detail,
        "PYINSTALLER_CERTIFICATION_GUARD_NOT_PROVEN",
    )
    _assert(
        not list((work / "forbidden-executable-dist").rglob("*.exe"))
        if (work / "forbidden-executable-dist").exists() else True,
        "UNCERTIFIED_EXE_EMITTED",
    )


def _real_http_health(env: dict[str, str], work: Path, port: int) -> None:
    log = (work / "native-source-backend-private.log").open("wb")
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-u", "run.py"],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.monotonic() + 110
        while time.monotonic() < deadline:
            _assert(process.poll() is None, "BACKEND_PROCESS_EXITED_BEFORE_HEALTH")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    _assert(response.status == 200, "ACTUAL_HTTP_NON_200")
                    _assert(payload.get("status") == "ok", "ACTUAL_HTTP_STATUS_NOT_OK")
                    _assert(payload.get("db") == "ok", "ACTUAL_HTTP_DB_NOT_OK")
                    return
            except AssertionError:
                raise
            except Exception:
                time.sleep(1)
        raise AssertionError("REAL_BACKEND_HEALTH_TIMEOUT")
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=12)
        log.close()


def _persisted_portable_rebind(env: dict[str, str], db: Path) -> None:
    # All SQLAlchemy access happens on the freshly migrated disposable DB.
    # Never import database until env is fully isolated.
    os.environ.update(env)
    from backend import database, models
    from backend.services.portability_license_rebind import rebind_portable_restore
    from backend.security import token_blacklist

    _assert(db.is_file(), "NO_SYNTHETIC_MIGRATED_DB")
    synthetic_email = "restore03-win-rebind-only@example.invalid"
    clinic_id = "restore03-synthetic-ci"
    expires = datetime.utcnow() + timedelta(days=60)

    with database.SessionLocal() as session:
        _assert(session.query(models.CabinetConfig).count() == 0, "FIXTURE_NOT_EMPTY")
        owner = models.User(
            email=synthetic_email,
            hashed_password="NOT_A_REAL_PASSWORD_OR_LOGIN",
            role=models.UserRole.DENTISTE,
            nom_complet="RESTORE03 SYNTHETIC",
            is_active=True,
            is_licensed=True,
            license_expires_at=expires,
        )
        session.add(owner)
        session.flush()
        oid = int(owner.id)
        session.add(models.CabinetConfig(
            owner_id=oid,
            clinic_id=clinic_id,
            public_id="restore03synthetic",
            nom_cabinet="SYNTHETIC ONLY - NEVER A PATIENT",
            nom_praticien="SYNTHETIC",
        ))
        session.commit()

    # This is the actual P4 function; its token-blacklist layer performs commit.
    result = rebind_portable_restore()
    _assert(result["cabinet_count"] == 1, "CABINET_COUNT_INCORRECT")
    _assert(result["licence_revalidation_required"] is True, "LICENSE_RECHECK_NOT_REQUIRED")
    _assert(result["mobile_access_revoked"] is True, "MOBILE_REVOKE_NOT_CONFIRMED")
    _assert(result["cabinets"][0]["clinic_id"] == clinic_id, "CLINIC_ID_MISMATCH")

    # Force an entirely fresh session after engine disposal; assert persistence.
    database.engine.dispose()
    with database.SessionLocal() as session:
        user = session.query(models.User).filter(models.User.id == oid).one()
        _assert(user.is_licensed is False, "LICENSE_NOT_PERSISTENTLY_REVOKED")
        _assert(user.license_expires_at is None, "EXPIRY_NOT_PERSISTENTLY_CLEARED")
        from backend.models import RevokedToken
        cutoff = session.query(RevokedToken).filter(
            RevokedToken.jti.like(f"{token_blacklist.MOBILE_EPOCH_PREFIX}{oid}:%")
        ).count()
        _assert(cutoff >= 1, "MOBILE_CUTOFF_NOT_PERSISTED")
        _assert(session.query(models.CabinetConfig).filter(
            models.CabinetConfig.clinic_id == clinic_id
        ).count() == 1, "CABINET_ID_NOT_PRESERVED")
    database.engine.dispose()


def main() -> int:
    _assert(os.name == "nt", "WINDOWS_REQUIRED")
    _assert(os.getenv("GITHUB_ACTIONS") == "true", "GITHUB_WINDOWS_ONLY")
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", required=True, type=Path)
    a = cli.parse_args()
    output = a.output.absolute()
    _assert(not output.exists(), "OUTPUT_DIRECTORY_MUST_BE_NEW")
    _assert(os.getenv("RUNNER_TEMP", "") != "", "RUNNER_TEMP_REQUIRED")
    root = Path(os.environ["RUNNER_TEMP"]).resolve()
    _assert(output.parent.resolve() == root, "OUTPUT_NOT_INSIDE_RUNNER_TEMP")
    output.mkdir()
    work = output / "private-rehearsal"
    work.mkdir()
    env, db, port = _env_and_target(work)
    try:
        _assert_uncertified_spec_refusal(env, work)
        _subprocess("alembic-baseline", [sys.executable, "-m", "alembic", "upgrade", "head"], env, work)
        _assert(db.exists(), "ALEMBIC_MISSING_SQLCIPHER_DATABASE")
        _real_http_health(env, work, port)
        _persisted_portable_rebind(env, db)
        # A second true application start proves the persisted DB is still usable
        # after licence invalidation. No Firebase sync or clinical writes.
        _real_http_health(env, work, port)
        report = {
            "marker": MARKER,
            "tested_sha": os.environ.get("GITHUB_SHA"),
            "os": "windows",
            "runtime": "real run.py FastAPI process, NOT frozen EXE",
            "schema_migration": "alembic-upgrade-head-on-disposable-db",
            "database_engine": "sqlcipher3-on-SQLite",
            "health_before_rebind": "HTTP_200_STATUS_OK_DB_OK",
            "health_after_rebind": "HTTP_200_STATUS_OK_DB_OK",
            "portable_license_rebind": "REAL_SQLALCHEMY_COMMITTED_AND_REOPENED",
            "mobile_revocation_marker": "PERSISTED_IN_DATABASE",
            "pyinstaller_uncertified_executable": "REFUSED_BY_INSTALLABLE_GATE",
            "installable_certification": "ABSENT",
            "production_executable_installed": False,
            "full_guided_restore_on_executable": "NOT_RUN",
            "clinical_go": False,
            "physical_cabinet_pc": "NOT_RUN",
            "nas_smb": "NOT_RUN",
        }
    finally:
        import shutil
        # Logs, SQLCipher DB, generated secrets, and work files are never artifacts.
        shutil.rmtree(work, ignore_errors=True)
    (output / PROOF).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _assert([p.name for p in output.iterdir()] == [PROOF], "PRIVATE_DATA_LEAK")
    print(MARKER + " REAL_SOURCE_RUNTIME_AND_P4_PERSISTENCE_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        safe_frames = traceback.extract_tb(exc.__traceback__)[-6:]
        locations = ";".join(f"{Path(x.filename).name}:{x.lineno}" for x in safe_frames)
        print(
            "RESTORE03_WINDOWS_NATIVE_RUNTIME_FAIL:"
            + type(exc).__name__ + ":" + locations,
            file=sys.stderr,
        )
        raise SystemExit(2) from None
