"""C05B-03H: gateway Ed25519 possession + password reauth + one-use clinical grant.

ISOLATED SYNTHETIC FASTAPI ONLY. This authenticates a *gateway key*, not an
imaging sensor. No production device issuer, hardware key persistence or clinic.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import secrets
import time

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import Depends, HTTPException, Request
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy import update

from backend import models
from backend.routers import auth
from backend.security import create_access_token, get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from isolated_fue_lot06c.test_sqlcipher_http_jwt_capture_bridge_v15 import _make_fixture, _post
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    BridgeRejected, _counts, _hash, _issue, bridge,
)

PASSWORD = "only-synthetic-reauth-passphrase-not-user-data"
EXPIRY = 120

def _guard():
    if not (os.getenv("ENVIRONMENT") == "test"
            and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.getenv("DC06C05B03H_TEST_ONLY") == "1"):
        raise HTTPException(503, "C05B03H_DISABLED")

def _msg(kind, record):
    return (kind + "|" + json.dumps(record, sort_keys=True, separators=(",", ":"))).encode()

def _verify(public_hex, signature_hex, message):
    try:
        pub = bytes.fromhex(public_hex)
        sig = bytes.fromhex(signature_hex)
        if len(pub) != 32 or len(sig) != 64:
            raise ValueError("bad key length")
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, message)
    except (ValueError, InvalidSignature, TypeError):
        raise HTTPException(409, "INVALID_GATEWAY_PROOF")

def _init(engine):
    _guard()
    # This lab schema is NOT in the runtime Alembic revision graph.
    with engine.begin() as conn:
        conn.exec_driver_sql("""CREATE TABLE c05b03h_enroll (
            nonce TEXT PRIMARY KEY, tenant INTEGER NOT NULL, device TEXT NOT NULL,
            station TEXT NOT NULL, generation INTEGER NOT NULL,
            public_hex TEXT NOT NULL, expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)""")
        conn.exec_driver_sql("""CREATE TABLE c05b03h_devices (
            tenant INTEGER NOT NULL, device TEXT NOT NULL, station TEXT NOT NULL,
            generation INTEGER NOT NULL, public_hex TEXT NOT NULL,
            active INTEGER NOT NULL, PRIMARY KEY (tenant,device))""")
        conn.exec_driver_sql("""CREATE TABLE c05b03h_capture (
            nonce TEXT PRIMARY KEY, tenant INTEGER NOT NULL, device TEXT NOT NULL,
            binding TEXT NOT NULL, expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)""")
        conn.exec_driver_sql("""CREATE TABLE c05b03h_grants (
            nonce TEXT PRIMARY KEY, staff INTEGER NOT NULL, session_jti TEXT NOT NULL,
            expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(nonce) REFERENCES c05b03h_capture(nonce))""")

def _session_jti(request, user):
    raw = request.headers.get("authorization", "")
    if not raw.startswith("Bearer "):
        raise HTTPException(401, "ACCESS_TOKEN_REQUIRED")
    try:
        claims = jwt.decode(raw[7:], SECRET_KEY, algorithms=[ALGORITHM])
        if claims.get("type") != "access" or claims.get("sub") != user.email:
            raise ValueError()
        return str(claims["jti"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "INVALID_SESSION")

def _station(request, db, claim):
    station_token = request.cookies.get("dc_workstation") or ""
    row = db.get(models.WorkstationMode, claim.station)
    if (not row or row.employer_id != claim.tenant or row.revoked_at is not None
            or row.mode_revision != claim.station_revision
            or not station_token
            or not secrets.compare_digest(row.token_hash, _hash(station_token))):
        raise HTTPException(423, "BOUND_STATION_REQUIRED")
    return station_token

def _bind(app, engine, claim, media_root):
    _init(engine)

    @app.post("/isolated/h/enroll/start")
    def start_enroll(payload: dict, request: Request,
                     current_user: models.User = Depends(auth.get_current_user)):
        _guard()
        with Session(engine) as db:
            _station(request, db, claim)
            if (current_user.id != claim.tenant or current_user.employer_id is not None
                    or not current_user.is_active or current_user.is_archived
                    or current_user.is_suspended):
                raise HTTPException(403, "OWNER_REQUIRED")
            if payload.get("device") != claim.device:
                raise HTTPException(409, "DEVICE_MISMATCH")
            try:
                pub = bytes.fromhex(payload.get("public_hex", ""))
            except ValueError:
                raise HTTPException(422, "INVALID_PUBLIC_KEY")
            if len(pub) != 32:
                raise HTTPException(422, "INVALID_PUBLIC_KEY")
            if db.connection().exec_driver_sql(
                "SELECT 1 FROM c05b03h_devices WHERE tenant=? AND device=?",
                (claim.tenant, claim.device),
            ).first():
                raise HTTPException(409, "ALREADY_ENROLLED")
            nonce=secrets.token_hex(24)
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03h_enroll VALUES(?,?,?,?,?,?,?,0)",
                (nonce,claim.tenant,claim.device,claim.station,claim.generation,
                 pub.hex(),int(time.time())+EXPIRY),
            )
            db.commit()
            return {"nonce":nonce}

    @app.post("/isolated/h/enroll/finish")
    def finish_enroll(payload: dict, request: Request,
                      current_user: models.User = Depends(auth.get_current_user)):
        _guard()
        with Session(engine) as db:
            _station(request, db, claim)
            if current_user.id != claim.tenant:
                raise HTTPException(403, "OWNER_REQUIRED")
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            row=db.connection().exec_driver_sql(
                "SELECT tenant,device,station,generation,public_hex,expires,used "
                "FROM c05b03h_enroll WHERE nonce=?", (payload.get("nonce"),)
            ).mappings().first()
            if (not row or row["used"] or row["expires"] < time.time()
                or row["tenant"]!=claim.tenant or row["device"]!=claim.device
                or row["station"]!=claim.station):
                raise HTTPException(409,"ENROLL_CHALLENGE_REJECTED")
            statement=dict(nonce=payload["nonce"],tenant=row["tenant"],device=row["device"],
                           station=row["station"],generation=row["generation"],public_hex=row["public_hex"])
            _verify(row["public_hex"],payload.get("signature",""),_msg("ENROLL",statement))
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03h_devices VALUES(?,?,?,?,?,1)",
                (row["tenant"],row["device"],row["station"],row["generation"],row["public_hex"]))
            db.connection().exec_driver_sql("UPDATE c05b03h_enroll SET used=1 WHERE nonce=?",
                                           (payload["nonce"],))
            db.commit()
            return {"gateway_enrolled_lab":True}

    @app.post("/isolated/h/capture/start")
    def start_capture(request: Request, current_user: models.User = Depends(auth.get_current_user)):
        _guard()
        with Session(engine) as db:
            _station(request,db,claim)
            if current_user.id != claim.staff:
                raise HTTPException(403,"STAFF_REQUIRED")
            device=db.connection().exec_driver_sql(
                "SELECT station,generation,active FROM c05b03h_devices "
                "WHERE tenant=? AND device=?", (claim.tenant,claim.device)
            ).mappings().first()
            if (not device or not device["active"] or device["station"]!=claim.station
                or device["generation"]!=claim.generation):
                raise HTTPException(409,"GATEWAY_REVOKED_OR_UNENROLLED")
            nonce=secrets.token_hex(24)
            statement=dict(nonce=nonce, **claim.values())
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03h_capture VALUES(?,?,?,?,?,0)",
                (nonce,claim.tenant,claim.device,
                 json.dumps(statement,sort_keys=True,separators=(",",":")),
                 int(time.time())+EXPIRY))
            db.commit()
            return {"nonce":nonce,"binding":statement}

    @app.post("/isolated/h/approve")
    def approve(payload: dict, request: Request,
                current_user: models.User = Depends(auth.get_current_user)):
        _guard()
        sid=_session_jti(request,current_user)
        with Session(engine) as db:
            _station(request,db,claim)
            staff=db.get(models.User,current_user.id)
            if (current_user.id != claim.staff or not staff or not staff.is_active
                or staff.is_archived or staff.is_suspended
                or not auth.has_permission(staff,"patients")
                or not verify_password(payload.get("password",""),staff.hashed_password)):
                raise HTTPException(403,"HUMAN_REAUTH_REQUIRED")
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            challenge=db.connection().exec_driver_sql(
                "SELECT binding,expires,used FROM c05b03h_capture WHERE nonce=?",
                (payload.get("nonce"),)
            ).mappings().first()
            dev=db.connection().exec_driver_sql(
                "SELECT station,generation,public_hex,active FROM c05b03h_devices "
                "WHERE tenant=? AND device=?", (claim.tenant,claim.device)
            ).mappings().first()
            expected=dict(nonce=payload.get("nonce"),**claim.values())
            if (not challenge or challenge["used"] or challenge["expires"] < time.time()
                or challenge["binding"]!=json.dumps(expected,sort_keys=True,separators=(",",":"))
                or not dev or not dev["active"] or dev["station"]!=claim.station
                or dev["generation"]!=claim.generation):
                raise HTTPException(409,"CAPTURE_CHALLENGE_DENIED")
            _verify(dev["public_hex"],payload.get("signature",""),_msg("CAPTURE",expected))
            if db.connection().exec_driver_sql(
                "SELECT 1 FROM c05b03h_grants WHERE nonce=?", (payload["nonce"],)
            ).first():
                raise HTTPException(409, "ALREADY_HUMAN_CONFIRMED")
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03h_grants VALUES(?,?,?,?,0)",
                (payload["nonce"],current_user.id,sid,int(time.time())+EXPIRY))
            db.commit()
            return {"human_confirmed_lab":True}

    @app.post("/isolated/h/issue")
    def issue(payload: dict, request: Request,
              current_user: models.User = Depends(auth.get_current_user)):
        _guard()
        sid=_session_jti(request,current_user)
        with Session(engine) as db:
            station_token=_station(request,db,claim)
            if current_user.id!=claim.staff:
                raise HTTPException(403,"STAFF_REQUIRED")
        nonce=payload.get("nonce")
        signature=payload.get("signature","")
        def _one_shot(locked_db, approved_claim):
            # Same locked SQLCipher transaction as AES readback + receipt/outbox.
            con=locked_db.connection()
            capture=con.exec_driver_sql(
                "SELECT binding,expires,used FROM c05b03h_capture WHERE nonce=?",
                (nonce,)
            ).mappings().first()
            grant=con.exec_driver_sql(
                "SELECT staff,session_jti,expires,used FROM c05b03h_grants WHERE nonce=?",
                (nonce,)
            ).mappings().first()
            device=con.exec_driver_sql(
                "SELECT station,generation,public_hex,active FROM c05b03h_devices "
                "WHERE tenant=? AND device=?", (claim.tenant,claim.device)
            ).mappings().first()
            binding=dict(nonce=nonce,**approved_claim.values())
            if (not capture or capture["used"] or capture["expires"]<time.time()
                or capture["binding"]!=json.dumps(binding,sort_keys=True,separators=(",",":"))
                or not grant or grant["used"] or grant["expires"]<time.time()
                or grant["staff"]!=current_user.id or grant["session_jti"]!=sid
                or not device or device["active"]!=1
                or device["station"]!=claim.station
                or device["generation"]!=claim.generation):
                raise BridgeRejected("ONE_SHOT_AUTHORITY_DENIED")
            try:
                _verify(device["public_hex"],signature,_msg("CAPTURE",binding))
            except HTTPException:
                raise BridgeRejected("GATEWAY_SIGNATURE_DENIED")
            con.exec_driver_sql("UPDATE c05b03h_capture SET used=1 WHERE nonce=?", (nonce,))
            con.exec_driver_sql("UPDATE c05b03h_grants SET used=1 WHERE nonce=?", (nonce,))
        try:
            receipt=_issue(engine,claim,
                 os.environ["DC06C05B03H_LEGACY_DEVICE_TOKEN"],
                 station_token,media_root,
                 fail_at=payload.get("lab_failpoint"),
                 locked_authorize=_one_shot)
        except BridgeRejected:
            raise HTTPException(409,"LAB_ISSUANCE_DENIED")
        return {"receipt_id":receipt,"clinical_receipt_authorized":False}

def test_h_ed25519_gateway_and_single_use_human_authority(bridge,monkeypatch,tmp_path):
    _guard()
    app,engine,claim,station_token,staff_email,owner_email,body,_=_make_fixture(bridge)
    media_root=bridge[4]
    dev_token=bridge[2]
    monkeypatch.setenv("DC06C05B03H_LEGACY_DEVICE_TOKEN",dev_token)
    with Session(engine) as db:
        db.execute(update(models.User.__table__).where(
            models.User.__table__.c.id==claim.staff
        ).values(hashed_password=get_password_hash(PASSWORD)))
        db.commit()
    _bind(app,engine,claim,media_root)
    owner_jwt=create_access_token({"sub":owner_email})
    staff_jwt=create_access_token({"sub":staff_email})
    other_session=create_access_token({"sub":staff_email})
    gateway=Ed25519PrivateKey.generate()
    attacker=Ed25519PrivateKey.generate()
    pubhex=gateway.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    def call(client,path,token,payload=None):
        return client.post("/isolated/h/"+path,json=payload or {},
                           headers={"Authorization":"Bearer "+token})
    with TestClient(app) as client:
        client.cookies.set("dc_workstation",station_token)
        bad=call(client,"enroll/start",staff_jwt,{"device":claim.device,"public_hex":pubhex})
        assert bad.status_code==403
        start=call(client,"enroll/start",owner_jwt,{"device":claim.device,"public_hex":pubhex})
        assert start.status_code==200,(start.status_code,start.text[:300])
        enonce=start.json()["nonce"]
        ebind=dict(nonce=enonce,tenant=claim.tenant,device=claim.device,
                   station=claim.station,generation=claim.generation,public_hex=pubhex)
        assert call(client,"enroll/finish",owner_jwt,{
            "nonce":enonce,"signature":attacker.sign(_msg("ENROLL",ebind)).hex()
        }).status_code==409
        assert call(client,"enroll/finish",owner_jwt,{
            "nonce":enonce,"signature":gateway.sign(_msg("ENROLL",ebind)).hex()
        }).status_code==200
        assert call(client,"enroll/finish",owner_jwt,{
            "nonce":enonce,"signature":gateway.sign(_msg("ENROLL",ebind)).hex()
        }).status_code==409
        challenge=call(client,"capture/start",staff_jwt)
        assert challenge.status_code==200,(challenge.status_code,challenge.text[:300])
        nonce=challenge.json()["nonce"]
        binding=challenge.json()["binding"]
        sig=gateway.sign(_msg("CAPTURE",binding)).hex()
        assert call(client,"approve",staff_jwt,{"nonce":nonce,"signature":sig,
                        "password":"wrong"}).status_code==403
        assert call(client,"approve",staff_jwt,{"nonce":nonce,
                        "signature":attacker.sign(_msg("CAPTURE",binding)).hex(),
                        "password":PASSWORD}).status_code==409
        assert call(client,"approve",staff_jwt,{"nonce":nonce,"signature":sig,
                        "password":PASSWORD}).status_code==200
        assert call(client,"approve",staff_jwt,{"nonce":nonce,"signature":sig,
                        "password":PASSWORD}).status_code==409
        assert call(client,"issue",other_session,{"nonce":nonce,"signature":sig}).status_code==409
        assert call(client,"issue",staff_jwt,{"nonce":nonce,
                      "signature":attacker.sign(_msg("CAPTURE",binding)).hex()}).status_code==409
        with engine.begin() as conn:
            conn.exec_driver_sql("UPDATE c05b03h_devices SET active=0")
        assert call(client,"issue",staff_jwt,{"nonce":nonce,"signature":sig}).status_code==409
        with engine.begin() as conn:
            conn.exec_driver_sql("UPDATE c05b03h_devices SET active=1")
        assert _counts(engine)==(0,0,0)
        # Rollback across grant consumption, receipt and outbox is atomic.
        assert call(client,"issue",staff_jwt,{"nonce":nonce,"signature":sig,
                            "lab_failpoint":"after_audit"}).status_code==409
        assert _counts(engine)==(0,0,0)
        accepted=call(client,"issue",staff_jwt,{"nonce":nonce,"signature":sig})
        assert accepted.status_code==200,(accepted.status_code,accepted.text[:300])
        assert accepted.json()["clinical_receipt_authorized"] is False
        assert accepted.json()["receipt_id"].startswith("LAB-ONLY-")
        assert _counts(engine)==(1,1,1)
        assert call(client,"issue",staff_jwt,{"nonce":nonce,"signature":sig}).status_code==409
        with engine.connect() as conn:
            assert conn.exec_driver_sql("SELECT used FROM c05b03h_capture WHERE nonce=?",(nonce,)).scalar_one()==1
            assert conn.exec_driver_sql("SELECT used FROM c05b03h_grants WHERE nonce=?",(nonce,)).scalar_one()==1
    root=Path(os.getenv("DC06C05B03H_EVIDENCE_DIR",str(tmp_path)))
    root.mkdir(parents=True,exist_ok=True)
    (root/"lot06c05b03h-gateway-human-proof.json").write_text(json.dumps({
        "kind":"C05B03H_ED25519_GATEWAY_REAL_JWT_REAUTH_SQLCIPHER_LAB",
        "real_ed25519_possession_enrollment":True,
        "enrollment_owner_and_station_bound":True,
        "wrong_signature_and_replayed_enrollment_refused":True,
        "real_backend_password_reauthentication":True,
        "jwt_session_bound_one_use_human_grant":True,
        "revoked_gateway_blocks_receipt":True,
        "different_staff_jwt_session_rejected":True,
        "atomic_rollback_preserves_one_shot_grant":True,
        "one_receipt_audit_outbox_and_replay_denial":True,
        "private_key_exported_or_persisted":False,
        "real_imaging_sensor_attestation":False,
        "windows_key_protection_certified":False,
        "production_device_issuer_activated":False,
        "human_approval_production_enabled":False,
        "clinical_receipt_authorized":False,
        "product_ready":False,
        "clinical_go":False
    },indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("C05B03H_ED25519_GATEWAY_HUMAN_ONE_SHOT_SQLCIPHER_RECEIPT_PASS")

def test_h_cabinet_hard_disabled(bridge,monkeypatch):
    app,engine,claim,station_token,staff_email,owner_email,body,_=_make_fixture(bridge)
    _bind(app,engine,claim,bridge[4])
    owner=create_access_token({"sub":owner_email})
    with TestClient(app) as client:
        client.cookies.set("dc_workstation",station_token)
        monkeypatch.setenv("ENVIRONMENT","cabinet")
        response=client.post("/isolated/h/enroll/start",
                             json={"device":claim.device,"public_hex":"00"*32},
                             headers={"Authorization":"Bearer "+owner})
        assert response.status_code==503
    assert _counts(engine)==(0,0,0)
    print("C05B03H_CLINICAL_ENVIRONMENT_FAIL_CLOSED_PASS")
