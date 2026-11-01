"""C05B03G isolated FastAPI real JWT/session/workstation guard + SQLCipher receipt.

No route in backend.main, no real login credential, no product device issuer.
The session JWT is signed by the real backend helper from a synthetic fixture.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from threading import Event

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, update
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as sqlcipher

from backend import models
from backend.routers import auth
from backend.security import create_access_token, create_refresh_token
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    BridgeRejected, _counts, _issue, bridge,
)

class ClaimBody(BaseModel):
    capture: str
    asset_id: int
    version: int
    digest: str
    device_token: str


def _make_fixture(bridge):
    _fixture_engine, claim, device_token, station_token, media_root, tmp = bridge
    # FastAPI sync Depends and async JWT may execute on different worker threads.
    # A dedicated SQLCipher NullPool engine for this SYNTHETIC TestClient only;
    # no changes to cabinet database engine or global SQLCipher policy.
    key = os.environ["DC06B_TEST_SQLCIPHER_KEY"]
    file = media_root.parent / "clinical-asset-lab.db"
    def connect():
        con = sqlcipher.connect(str(file), timeout=30, check_same_thread=False)
        try:
            con.execute("PRAGMA key = '" + key + "'")
            if not con.execute("PRAGMA cipher_version").fetchone():
                raise RuntimeError("HTTP_LAB_REQUIRES_SQLCIPHER")
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=NORMAL")
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
            return con
        except BaseException:
            con.close()
            raise
    engine = create_engine("sqlite://", creator=connect, poolclass=NullPool)
    models.RevokedToken.__table__.create(bind=engine, checkfirst=True)
    with Session(engine) as db:
        staff = db.get(models.User, claim.staff)
        owner = db.get(models.User, claim.tenant)
        staff_email, owner_email = staff.email, owner.email

    app = FastAPI(title="C05B03G synthetic HTTP only")
    def lab_db():
        with Session(engine) as db:
            yield db

    # ONLY the database source is redirected. JWT validation, blacklist,
    # User permissions and workstation-mode guard remain the actual backend.
    app.dependency_overrides[auth.get_db] = lab_db

    @app.post("/isolated/lot06/receipt")
    def synthetic_receipt(
        body: ClaimBody, current_user: models.User = Depends(auth.get_current_user),
    ):
        if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC06C05B03G_TEST_ONLY") != "1"):
            raise HTTPException(503, "ISOLATED_HTTP_DISABLED")
        if current_user.id != claim.staff or current_user.get_employer_id() != claim.tenant:
            raise HTTPException(403, "STAFF_CAPTURE_NOT_AUTHORIZED")
        if (body.capture != claim.capture or body.asset_id != claim.asset_id
            or body.digest != claim.digest or body.version != claim.version):
            raise HTTPException(409, "CAPTURE_BINDING_CONFLICT")
        try:
            receipt = _issue(engine,claim,body.device_token,station_token,media_root)
        except BridgeRejected:
            raise HTTPException(409, "CAPTURE_AUTHORITY_DENIED")
        return {"receipt_id": receipt, "clinical_receipt_authorized": False}

    request = {
        "capture": claim.capture, "asset_id": claim.asset_id,
        "digest": claim.digest, "version": claim.version, "device_token": device_token,
    }
    return app, engine, claim, station_token, staff_email, owner_email, request, tmp


def _post(client, body, jwt_token=None):
    headers = {"Authorization": "Bearer " + jwt_token} if jwt_token else {}
    return client.post("/isolated/lot06/receipt", json=body, headers=headers)


def test_c05b03g_real_jwt_workstation_and_replay_fail_closed(bridge):
    app, engine, claim, station_token, staff_email, owner_email, body, tmp = _make_fixture(bridge)
    token = create_access_token({"sub": staff_email})
    owner_token = create_access_token({"sub": owner_email})
    expired = create_access_token({"sub": staff_email}, expires_delta=timedelta(seconds=-1))
    refresh = create_refresh_token({"sub": staff_email})
    with TestClient(app) as client:
        assert _post(client, body).status_code == 401
        assert _post(client, body, "malformed").status_code == 401
        assert _post(client, body, refresh).status_code == 401
        assert _post(client, body, expired).status_code == 401
        assert _post(client, body, token).status_code == 423
        client.cookies.set("dc_workstation","wrong-station-credential")
        assert _post(client, body, token).status_code == 423
        client.cookies.set("dc_workstation",station_token)
        assert _post(client, body, owner_token).status_code == 403
        assert _post(client, {**body,"version":body["version"]+1}, token).status_code == 409
        assert _post(client, {**body,"device_token":"wrong"}, token).status_code == 409
        assert _counts(engine) == (0,0,0)
        a=_post(client,body,token)
        assert a.status_code == 200, (a.status_code,a.text[:350])
        assert a.json()["clinical_receipt_authorized"] is False
        receipt=a.json()["receipt_id"]
        b=_post(client,body,token)
        assert b.status_code==200 and b.json()["receipt_id"]==receipt
        assert _counts(engine)==(1,1,1)
        # Revoking the workstation invalidates a valid JWT immediately.
        with engine.begin() as conn:
            conn.execute(update(models.WorkstationMode.__table__).where(
                models.WorkstationMode.__table__.c.id==claim.station
            ).values(revoked_at=datetime.utcnow()))
        assert _post(client,body,token).status_code==423
        with engine.begin() as conn:
            conn.execute(update(models.WorkstationMode.__table__).where(
                models.WorkstationMode.__table__.c.id==claim.station
            ).values(revoked_at=None))
            conn.execute(update(models.User.__table__).where(
                models.User.__table__.c.id==claim.staff
            ).values(is_active=False))
        assert _post(client,body,token).status_code==401
        assert _counts(engine)==(1,1,1)

    evidence=Path(os.getenv("DC06C05B03G_EVIDENCE_DIR",str(tmp)))
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/"lot06c05b03g-http-jwt.json").write_text(json.dumps({
       "kind":"C05B03G_ISOLATED_REAL_JWT_WORKSTATION_SQLCIPHER_HTTP",
       "real_fastapi_dependency_get_current_user_executed":True,
       "actual_access_jwt_validation_executed":True,
       "refresh_expired_and_invalid_jwt_denied":True,
       "workstation_cookie_identity_and_revocation_denied":True,
       "wrong_staff_identity_denied":True,
       "device_token_and_claim_binding_denied":True,
       "idempotent_receipt_readback_sqlcipher":True,
       "staff_revocation_denies_existing_receipt":True,
       "isolated_route_only_not_product":True,
       "real_password_login_executed":False,
       "product_device_enrollment_verified":False,
       "one_time_human_review_verified":False,
       "clinical_receipt_authorized":False,
       "product_ready":False,
       "clinical_go":False,
    },sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("C05B03G_REAL_JWT_WORKSTATION_SQLCIPHER_ISOLATED_HTTP_PASS")


def test_c05b03g_inflight_staff_revocation_after_http_auth_blocks_receipt(bridge, monkeypatch):
    app, engine, claim, station_token, staff_email, _, body, _ = _make_fixture(bridge)
    token=create_access_token({"sub":staff_email})
    entered, proceed = Event(), Event()
    original=_issue

    def paused_issue(*args, **kwargs):
        entered.set()
        assert proceed.wait(timeout=15), "POST_AUTH_PAUSE_TIMEOUT"
        return original(*args,**kwargs)

    monkeypatch.setattr(
      "isolated_fue_lot06c.test_sqlcipher_http_jwt_capture_bridge_v15._issue",
      paused_issue,
    )
    def submit():
        with TestClient(app,raise_server_exceptions=False) as client:
            client.cookies.set("dc_workstation",station_token)
            return _post(client,body,token)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(submit)
        try:
            assert entered.wait(timeout=15), "HTTP_JWT_NOT_ENTERED"
            with engine.begin() as conn:
                conn.execute(update(models.User.__table__).where(
                    models.User.__table__.c.id==claim.staff
                ).values(permissions={"patients":False}))
        finally:
            proceed.set()
        response=pending.result(timeout=20)
    assert response.status_code==409,(response.status_code,response.text[:250])
    assert "receipt_id" not in response.text
    assert _counts(engine)==(0,0,0)
    print("C05B03G_INFLIGHT_REAL_HTTP_JWT_STAFF_REVOKED_BEFORE_ISSUE_DENIED")


def test_c05b03g_production_flag_denied(bridge, monkeypatch):
    app, engine, claim, station_token, staff_email, _, body, _ = _make_fixture(bridge)
    token=create_access_token({"sub":staff_email})
    with TestClient(app) as client:
        client.cookies.set("dc_workstation",station_token)
        monkeypatch.setenv("ENVIRONMENT","cabinet")
        assert _post(client,body,token).status_code==503
    assert _counts(engine)==(0,0,0)
    print("C05B03G_CABINET_HTTP_DISABLED_PASS")
