"""Ephemeral GitHub Actions-only Cabinet server fixture for real iPhone testing.

NOT a production entry point. A deliberately isolated in-memory test database,
synthetic patient, and temporary externally reachable HTTPS tunnel only.
"""
from __future__ import annotations

import base64
import hashlib
import html
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import quote

# The test fixture sets a hard isolated :memory: database before imports.
assert os.environ.get("GITHUB_ACTIONS") == "true", "GitHub Actions-only"
assert os.environ.get("FIELD_LAB_ACK") == "synthetic-only", "Synthetic data required"
from backend.tests import conftest as fixture
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from backend import database, models
from backend.models_document_provenance_p3 import install_document_provenance_p3
from backend.config import settings
from backend.security import get_password_hash
from backend.routers.auth import get_current_user
from backend.routers.workstation_mode import WORKSTATION_COOKIE
from backend.services.qr_service import qr_service
from backend.tests.test_station_patient_session_v15 import _login, _patient_context, _station
from backend.tests.test_station_https_cross_process_v15 import _valid_finalized_pdf

# In-memory StaticPool from test fixtures; never access a Cabinet/production database.
assert os.environ["DATABASE_URL"] == "sqlite:///:memory:"
database.engine = fixture._engine
database.SessionLocal = fixture._SessionLocal
install_document_provenance_p3()
models.Base.metadata.create_all(bind=fixture._engine)

from backend.main import app  # noqa: E402

origin = os.environ["FIELD_PUBLIC_ORIGIN"].rstrip("/")
assert origin.startswith("https://") and origin.endswith(".trycloudflare.com")
settings.STATION_HANDOFF_PUBLIC_ORIGIN = origin
settings.APP_PUBLIC_URL = origin
settings.ALLOWED_ORIGINS = origin
field_key = secrets.token_urlsafe(28)
current: dict[str, str] = {}
run_id = os.environ["GITHUB_RUN_ID"]
email = f"field-{run_id}@example.com"
password = os.environ["FIELD_DEMO_PASSWORD"]
assert password == "TestPass123!", "Demo password must remain fixture-only"

# Seed with the same real service paths as the proven FastAPI HTTPS test.
db = fixture._SessionLocal()
owner = fixture.make_user(db, email=email, password=password)
client = TestClient(app)
try:
    staff, initial_station_id = _station(client, owner)
    client.cookies.delete(WORKSTATION_COOKIE)
    enrollment = client.post(
        "/api/workstation/enroll", headers=staff,
        json={"accountPassword": password},
    )
    assert enrollment.status_code == 200, enrollment.text
    assert enrollment.json()["workstationId"] != initial_station_id
    cabinet_mode = client.post(
        "/api/workstation/mode", headers=staff,
        json={"mode": "cabinet", "ownerPin": "2468"},
    )
    assert cabinet_mode.status_code == 200, cabinet_mode.text
    patient, _unused_access, _unused_token = _patient_context(
        db, owner, dossier=f"FIELD-{run_id}", name="Fictive",
    )
    document, expected_digest = _valid_finalized_pdf(db, patient)
    approved = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=staff,
    )
    assert approved.status_code == 200, approved.text
    invitation = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/local-invitation",
        headers=staff, json={"relationship_type": "SELF", "expires_in_minutes": 60},
    )
    assert invitation.status_code == 201, invitation.text
    manual_code = invitation.json()["manual_code"]
    assert len(manual_code) >= 6
    # Freeze primary keys before db.close(): SQLAlchemy may expire ORM attributes.
    owner_id = int(owner.id)
    document_id = int(document.id)
finally:
    client.close()
db.close()
cabinet_workstation_id = enrollment.json()["workstationId"]


class StationPublish(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    handoff_url: str = Field(min_length=32, max_length=1024)


def _require_field_key(key: str) -> None:
    if not secrets.compare_digest(key, field_key):
        raise HTTPException(404, "FIELD_NOT_FOUND")


_existing_route_count = len(app.router.routes)

@app.get("/field-lab", response_class=HTMLResponse, include_in_schema=False)
def field_landing(k: str = ""):
    _require_field_key(k)
    url = current.get("handoff_url", "")
    active = url.startswith(origin + "/companion?stationSession=")
    button = (
        f'<a class="action" href="{html.escape(url, quote=True)}">2. Ouvrir le QR Station actif</a>'
        if active else '<p>La Station distincte prepare un QR. Actualisez dans quelques secondes.</p>'
    )
    qr = (
        f'<img alt="QR de la Station de test" width="224" height="224" src="/field-lab/qr?k={quote(field_key)}">'
        if active else ""
    )
    page = f"""<!doctype html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store">
<title>Digital Crown · terrain hybride</title>
<style>
body {{ font: 17px/1.5 system-ui,sans-serif;max-width:590px;margin:30px auto;padding:0 18px;color:#1a2632 }}
h1 {{ font-size:25px }} .action {{ display:block;background:#123c6b;color:white;padding:15px;border-radius:10px;margin:12px 0 }}
code {{font-size:28px;letter-spacing:3px}} small {{color:#526176}} img {{display:block;margin:10px 0}}
</style></head><body>
<h1>Digital Crown — vrai iPhone + deux runners isoles</h1>
<p><strong>Donnees 100 % fictives.</strong> Ne saisissez aucun compte, nom ou document reel.</p>
<p>1. <a href="/companion">Ouvrir Patient Companion</a> et appairer via son code manuel :</p>
<p><code>{html.escape(manual_code)}</code></p>
<p>Le code d'appairage n'est valable qu'une fois. Puis revenez sur cette page.</p>
{qr}{button}
<p>Le QR Station change environ toutes les 80 secondes s'il n'a pas ete reclame. Ouvrez sa destination depuis ce telephone.</p>
<p><small>PDF fictif autorise, SHA-256 attendu : <code style="font-size:11px;letter-spacing:0">{expected_digest}</code></small></p>
<p><small>Fin automatique du labo a l'arret des jobs GitHub. Ce n'est ni un Cabinet de production, ni une validation NFC ou d'impression physique.</small></p>
</body></html>"""
    return HTMLResponse(page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@app.get("/field-lab/qr", include_in_schema=False)
def field_qr(k: str = ""):
    _require_field_key(k)
    url = current.get("handoff_url", "")
    if not url.startswith(origin + "/companion?stationSession="):
        raise HTTPException(404, "QR_NOT_READY")
    image = qr_service.generate_qr_bytes(url, qr_style="classic").getvalue()
    return Response(content=image, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.post("/field-lab/station-publish", include_in_schema=False)
def station_publish(
    body: StationPublish,
    user: models.User = Depends(get_current_user),
):
    # Only a synthetically authenticated owner can publish. Never accept
    # external URLs or a mismatched session ID.
    if user.id != owner_id or not body.handoff_url.startswith(origin + "/companion?stationSession="):
        raise HTTPException(403, "FIELD_STATION_REJECTED")
    session = fixture._SessionLocal()
    try:
        row = session.get(models.WorkstationPatientSession, body.session_id)
        if row is None or row.employer_id != owner_id or row.purged_at is not None:
            raise HTTPException(403, "FIELD_SESSION_REJECTED")
    finally:
        session.close()
    current.clear()
    current.update(session_id=body.session_id, handoff_url=body.handoff_url)
    return {"published": True}


@app.get("/field-lab/health", include_in_schema=False)
def field_health():
    return {"kind": "synthetic-gh-actions-cabinet", "run_id": run_id, "ready": True, "document_id": document_id, "cabinet_workstation_id": cabinet_workstation_id}


# Starlette uses first-match routing. The product may register a SPA catchall;
# place temporary lab-only endpoints before any catchall in this isolated process.
_lab_routes = app.router.routes[_existing_route_count:]
app.router.routes[:] = _lab_routes + app.router.routes[:_existing_route_count]

if __name__ == "__main__":
    import uvicorn
    print("FIELD_LAB_LANDING=" + origin + "/field-lab?k=" + quote(field_key), flush=True)
    print("FIELD_LAB_EXPECTED_PDF_SHA256=" + expected_digest, flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8005, lifespan="off", access_log=False, log_level="warning")
