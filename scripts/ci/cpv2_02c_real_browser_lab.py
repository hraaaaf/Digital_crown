"""CI-only CPV2-02C real browser -> FastAPI -> disposable SQLCipher lab.

No real clinic records; no production schema changes. Browser asserts are in
frontend/scripts/certify-cpv2-02c-real-browser.mjs (no backend API mocks).
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if not (
    os.getenv("GITHUB_ACTIONS") == "true"
    and os.getenv("CPV2_02C_REAL_BROWSER_LAB") == "1"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    and os.getenv("ENVIRONMENT") == "test"
):
    raise RuntimeError("FUE réelle interdite hors laboratoire GitHub isolé")

HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert HEAD == os.environ["CPV2_REAL_BROWSER_SHA"], "Source HEAD non attestée"
temp = Path(os.environ["RUNNER_TEMP"]).resolve()
lab = temp / ("cpv2-02c-real-browser-" + os.environ["GITHUB_RUN_ID"])
if lab.exists():
    raise RuntimeError("Laboratoire déjà présent : refus de réutiliser une DB")
lab.mkdir(mode=0o700)
media = lab / "media"
media.mkdir(mode=0o700)
database_file = lab / "synthetic-only.db"
db_url = "sqlite:///" + str(database_file)
os.environ.update({
    "DATABASE_URL": db_url,
    "MEDIA_ROOT": str(media),
    "ALLOWED_ORIGINS": "http://127.0.0.1:5174,http://localhost:5174",
    "SECRET_KEY": "cpv2-real-browser-isolated-synthetic-secret-32chars",
    "MOBILE_PAIRING_KEY_HEX": "22" * 32,
    "TELEMETRY_ENABLED": "false",
    "CLOUD_AI_ENABLED": "false",
    "DEBUG": "false",
})
from backend.core.runtime_safety import database_target_fingerprint, is_known_cabinet_database

assert not is_known_cabinet_database(db_url)
os.environ["DIGITALCROWN_ISOLATION_DB_FINGERPRINT"] = database_target_fingerprint(db_url)

from backend import database, models
from backend.models_document_provenance_p3 import install_document_provenance_p3
from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt,
    PocketReceiptBase,
)
from backend.routers.mobile import _create_mobile_jwt

if database_file.exists():
    raise RuntimeError("La DB de test ne peut pas préexister")
assert database.engine.dialect.name == "sqlite"
install_document_provenance_p3()
models.Base.metadata.create_all(bind=database.engine)
PocketReceiptBase.metadata.create_all(bind=database.engine)
with database.SessionLocal() as db:
    user = models.User(
        email="cpv2-browser@synthetic.invalid",
        hashed_password="synthetic-no-desktop-login",
        role=models.UserRole.DENTISTE, nom_complet="Dr Browser Fictif",
        is_active=True, is_licensed=True, approval_status="approved",
    )
    db.add(user)
    db.flush()
    cabinet = models.CabinetConfig(
        owner_id=user.id, nom_cabinet="Cabinet Fictif CPV2",
        nom_praticien="Dr Browser Fictif", nom_praticien_ar="",
    )
    db.add(cabinet)
    patient_ids = []
    for name in ("FICTIF-A", "FICTIF-B"):
        patient = models.Patient(
            nom=name, prenom="Patient", date_naissance=datetime(1991, 1, 1),
            sexe="M", employer_id=user.id,
        )
        db.add(patient)
        db.flush()
        patient_ids.append(patient.id)
    device_id = str(uuid.uuid4())
    db.add(models.MobilePairedDevice(
        device_id=device_id, user_id=user.id, employer_id=user.id,
        client_public_key_hex="04" + "11" * 64,
        refresh_jti="cpv2-real-browser-" + uuid.uuid4().hex,
    ))
    db.commit()
    token = _create_mobile_jwt(user.id, models.UserRole.DENTISTE.value, user.id, device_id)
    user_id = user.id

fixture = lab / "browser-credentials.json"
fixture.write_text(json.dumps({
    "publicId": "0123456789abcdef",
    "masterKey": "22" * 32,
    "access_token": token,
    "device_id": device_id,
    "api_base_url": "http://127.0.0.1:8005",
    "patients": patient_ids,
}), encoding="utf-8")
fixture.chmod(0o600)
out = ROOT / "artifacts" / "cpv2-02c-real-browser"
out.mkdir(parents=True, exist_ok=True)
log_backend = (lab / "backend.log").open("w", encoding="utf-8")
log_frontend = (lab / "frontend.log").open("w", encoding="utf-8")
server = None
vite = None


def await_ready(url: str, process, logfile: Path) -> None:
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError("Service de test arrêté : " + logfile.read_text()[-2800:])
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.3)
    raise RuntimeError("Service de test injoignable : " + logfile.read_text()[-2800:])


try:
    server = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "127.0.0.1", "--port", "8005", "--lifespan", "off",
    ], cwd=ROOT, env=os.environ.copy(), stdout=log_backend, stderr=subprocess.STDOUT)
    await_ready("http://127.0.0.1:8005/openapi.json", server, lab / "backend.log")
    vite = subprocess.Popen([
        "npm", "run", "dev", "--", "--host", "127.0.0.1",
        "--port", "5174", "--strictPort",
    ], cwd=ROOT / "frontend", env=os.environ.copy(),
       stdout=log_frontend, stderr=subprocess.STDOUT)
    await_ready("http://127.0.0.1:5174/mobile/demo?demo=1", vite, lab / "frontend.log")

    child_env = os.environ.copy()
    child_env["CPV2_REAL_BROWSER_CREDS_FILE"] = str(fixture)
    child_env["CPV2_REAL_BROWSER_OUTPUT"] = str(out)
    subprocess.run([
        "node", "scripts/certify-cpv2-02c-real-browser.mjs",
    ], cwd=ROOT / "frontend", env=child_env, check=True, timeout=270)

    report = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
    assert report["sourceHead"] == HEAD and report["allPassed"] is True
    assert len(report["documents"]) == 2
    with database.SessionLocal() as db:
        rows = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id.in_(patient_ids)
        ).all()
        receipts = db.query(MobileDocumentArchiveReceipt).filter_by(
            tenant_id=user_id, actor_id=user_id, device_id=device_id
        ).all()
        assert len(rows) == len(receipts) == 2
        assert all(r.state == "COMPLETED" and r.archive_id for r in receipts)
        for receipt in receipts:
            row = next(r for r in rows if r.id == receipt.archive_id)
            assert receipt.patient_id == row.patient_id and row.file_hash == receipt.archive_sha256
            assert row.file_path.startswith("static/archives/")
            path = media / row.file_path.removeprefix("static/")
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row.file_hash
        device = db.query(models.MobilePairedDevice).filter_by(device_id=device_id).one()
        device.revoked_at = datetime.utcnow()
        db.commit()
    denied = requests.get(
        "http://127.0.0.1:8005/api/mobile/documents/archive/receipt/" + report["documents"][0]["intentKey"],
        headers={"Authorization": "Bearer " + token}, timeout=15,
    )
    assert denied.status_code == 401, "Revoked device still able to recover PDF"
    report["postconditions"] = {
        "uniqueDocumentRows": 2, "uniqueCompletedReceipts": 2,
        "allArchivedSha256Match": True, "revokedDeviceGet": denied.status_code,
        "db": "disposable local SQLite or SQLCipher only",
    }
    (out / "evidence.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FUE browser real FastAPI + two PDFs + receipts + revoked JWT = PASS")
finally:
    for process in (vite, server):
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
    log_backend.close()
    log_frontend.close()
    fixture.unlink(missing_ok=True)
