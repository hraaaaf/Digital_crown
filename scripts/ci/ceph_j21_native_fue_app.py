"""GitHub Actions Windows-only NONCLINICAL FUE executable.

Separate from run.py / DigitalCrown.spec and the INSTALLABLE_CERTIFIED policy.
Never a clinic install; all DB, JWT, key and media bytes are synthetic and ephemeral.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

PORT = 8879
USERNAME = "j21-native-fue@cabinet.invalid"
PASSWORD = "TestPass123!"  # synthetic automation fixture, never real clinic credentials
FUE_MARKER = "GITHUB_WINDOWS_J21_SYNTHETIC_FUE_ONLY"


def paths() -> tuple[Path, Path]:
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("CI") != "true"
            or os.environ.get("CEPH_J21_NATIVE_FUE_ONLY") != FUE_MARKER):
        raise RuntimeError("Native FUE refused outside an explicitly authorized GitHub Windows test")
    if os.name != "nt" or sys.platform != "win32":
        raise RuntimeError("This nonclinical FUE executable is Windows runner only")
    temp_value = os.environ.get("RUNNER_TEMP", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    if not temp_value or not run_id.isdecimal():
        raise RuntimeError("GitHub runner temporary root and numeric run ID required")
    temp = Path(temp_value).resolve(strict=True)
    root = temp / ("ceph-j21-native-fue-" + run_id)
    if root.is_symlink() or temp not in root.resolve().parents:
        raise RuntimeError("Unsafe synthetic test root")
    return root, root / "ceph-j21-scene-app-fue.sqlite3"


def bootstrap_profile(root: Path, db_file: Path) -> None:
    if root.exists():
        raise RuntimeError("Refusing to overwrite any pre-existing test profile")
    root.mkdir()
    data = {
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "CEPH_J21_SCENE_APP_FUE_ONLY": "1",
        "DC_DOS05_FUE_ONLY": "1",
        "CEPH_J21_SCENE_APP_FUE_ROOT": str(root),
        "DATABASE_URL": "sqlite:///" + db_file.as_posix(),
        "CABINET_MASTER_KEY_HEX": secrets.token_hex(32),
        "SECRET_KEY": secrets.token_hex(32),
        "CLOUD_AI_ENABLED": "false",
        "TELEMETRY_ENABLED": "false",
    }
    (root / "private-fixture-env.json").write_text(json.dumps(data), encoding="utf-8")


def load_profile(root: Path, db_file: Path) -> None:
    if root.is_symlink() or db_file.is_symlink() or not root.is_dir():
        raise RuntimeError("Synthetic profile missing or symlinked")
    file = root / "private-fixture-env.json"
    if file.is_symlink():
        raise RuntimeError("Symlinked synthetic environment refused")
    data = json.loads(file.read_text(encoding="utf-8"))
    if data.get("DATABASE_URL") != "sqlite:///" + db_file.as_posix():
        raise RuntimeError("Non-test database path refused")
    for name, value in data.items():
        if name in ("ENVIRONMENT", "DIGITALCROWN_ISOLATED_RUNTIME",
                    "CEPH_J21_SCENE_APP_FUE_ONLY", "DC_DOS05_FUE_ONLY",
                    "CEPH_J21_SCENE_APP_FUE_ROOT", "DATABASE_URL"):
            pass
        os.environ[name] = value
    if not (os.environ["ENVIRONMENT"] == "test"
            and os.environ["DIGITALCROWN_ISOLATED_RUNTIME"] == "true"
            and os.environ["CEPH_J21_SCENE_APP_FUE_ONLY"] == "1"):
        raise RuntimeError("Test runtime guard absent")
    # No config fallback to backend/.env or a historical %APPDATA% cabinet.
    os.environ["DIGITALCROWN_ENV_FILE"] = str(root / "never-use-real-cabinet.env")
    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(root)
    os.environ["DIGITALCROWN_CONFIG_DIR"] = str(root)
    os.environ["DIGITALCROWN_RUNTIME_DIR"] = str(root)
    os.environ["DIGITALCROWN_LOG_DIR"] = str(root)
    os.environ["MEDIA_ROOT"] = str(root / "synthetic-media")


def make_app(root: Path, db_file: Path, *, create_schema: bool):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend import database, models
    from backend.models_ceph_premium_scene_fue import CephPremiumSceneFueSnapshot
    from backend.main import app
    from backend.routers.cephalo_study_media_binding import router as media_router
    from backend.routers.ceph_premium_scene_app_fue import router as scene_router
    from backend.services import clinical_asset_storage

    engine = create_engine(
        "sqlite:///" + db_file.as_posix(),
        connect_args={"check_same_thread": False},
    )
    database.engine = engine
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    database.SessionLocal = Session
    clinical_asset_storage.get_media_root = lambda: root / "synthetic-media"
    if create_schema:
        models.Base.metadata.create_all(bind=engine)
    else:
        from sqlalchemy import inspect
        if "ceph_premium_scene_fue_snapshots" not in inspect(engine).get_table_names():
            raise RuntimeError("Missing synthetic scene table on reopened database")

    def app_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[database.get_db] = app_db
    app.include_router(media_router, prefix="/api/ia")
    app.include_router(scene_router, prefix="/api/ia")
    return app, Session, engine


def seed_scene(root: Path, app, Session) -> dict:
    from fastapi.testclient import TestClient
    from backend import models
    from backend.security import get_password_hash
    from backend.tests.p2ter_bridge_synthetic_support import _case, _read
    from backend.tests.test_ceph_j21_m4_real_jwt_fue import (
        _scene_for_binding, _real_encrypted_test_png,
    )
    with Session() as session:
        user = models.User(
            email=USERNAME, hashed_password=get_password_hash(PASSWORD),
            role="DENTISTE", nom_complet="SYNTHETIC FUE ONLY",
            is_active=True, is_licensed=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id
        patient, study, _ = _case(session, user)
        patient_id, study_id = patient.id, study.id
        session.commit()

    with TestClient(app, raise_server_exceptions=True) as client:
        login = client.post("/api/auth/login", data={"username": USERNAME, "password": PASSWORD})
        if login.status_code != 200:
            raise RuntimeError("Synthetic JWT login failure")
        token = login.json()["access_token"]
        client.cookies.clear()
        headers = {"Authorization": "Bearer " + token}
        _, science = _read(client, study_id, headers)
        original = _real_encrypted_test_png()
        uploaded = client.post(
            f"/api/patients/{patient_id}/assets/import",
            headers=headers,
            data={"asset_type": "RADIOGRAPH", "source_kind": "UPLOAD", "timepoint": "T0"},
            files={"file": ("synthetic-nonclinical.png", original, "image/png")},
        )
        if uploaded.status_code != 201:
            raise RuntimeError(f"Synthetic AES-GCM import failed: {uploaded.status_code}")
        asset = uploaded.json()
        linked = client.post(
            f"/api/ia/analyses/{study_id}/media-bindings/RADIO_SOURCE",
            headers=headers,
            json={"patient_id": patient_id, "asset_id": asset["id"],
                  "expected_revision": science["revision"]},
        )
        if linked.status_code != 201:
            raise RuntimeError(f"Synthetic source binding failed: {linked.status_code}")
        with Session() as session:
            user = session.get(models.User, user_id)
            patient = session.get(models.Patient, patient_id)
            study = session.get(models.CephaloAnalysis, study_id)
            scene = _scene_for_binding(user, patient, study, science["revision"], asset, original)
        scene_json = scene.canonical_dict()
        scene_json["measurements"] = [
            {"id": "SNA", "unit": "DEG", "status": "RAW_NONCLINICAL", "value": 80.4}
        ]
        first = client.post(
            f"/api/ia/analyses/{study_id}/premium-scene-fue",
            headers=headers,
            json={"scene": scene_json, "expected_parent_sha256": None},
        )
        if first.status_code != 201:
            raise RuntimeError(f"Initial synthetic scene write failed: {first.status_code}")
        response = first.json()
        if response["verified_original"]["image_sha256"] != hashlib.sha256(original).hexdigest():
            raise RuntimeError("Synthetic source SHA mismatch")
        report = {
            "patient_id": patient_id, "study_id": study_id, "asset_id": asset["id"],
            "original_sha256": hashlib.sha256(original).hexdigest(),
            "first_scene_sha256": response["scene_sha256"],
            "landmarks": 38, "clinical_release": False,
        }
        (root / "fixture-id.json").write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
        return report


def mount_ui(app) -> None:
    from starlette.routing import Mount
    from starlette.staticfiles import StaticFiles
    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    if getattr(sys, "frozen", False):
        static = bundle / "fue-ui"
    else:
        static = bundle / "frontend" / "dist-ceph-j21-native-fue"
    if not (static / "index.html").is_file():
        raise RuntimeError("Missing isolated FUE frontend; no fallthrough to clinical frontend")
    app.router.routes.insert(0, Mount(
        "/__ceph_fue", app=StaticFiles(directory=str(static), html=True),
        name="synthetic-j21-fue",
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description="NONCLINICAL Windows CI-only FUE")
    parser.add_argument("operation", choices=("initialize", "serve"))
    args = parser.parse_args()
    root, db_file = paths()
    if args.operation == "initialize":
        bootstrap_profile(root, db_file)
    load_profile(root, db_file)
    if args.operation == "serve" and not db_file.is_file():
        raise RuntimeError("No pre-existing synthetic app database to reopen")
    app, Session, engine = make_app(root, db_file, create_schema=args.operation == "initialize")
    try:
        if args.operation == "initialize":
            result = seed_scene(root, app, Session)
            print("CEPH_NATIVE_FUE_SYNTHETIC_SEEDED " + json.dumps(result, sort_keys=True), flush=True)
            return 0
        mount_ui(app)
        import uvicorn
        print("CEPH_NATIVE_FUE_LOOPBACK_ONLY_READY", flush=True)
        uvicorn.run(
            app, host="127.0.0.1", port=PORT, lifespan="off", access_log=False,
            log_level="warning",
        )
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Avoid dumping keys, tokens or a local filesystem environment.
        print("CEPH_NATIVE_FUE_FAIL_CLOSED " + type(exc).__name__ + ": " + str(exc)[:250], file=sys.stderr)
        raise SystemExit(2)
