"""LOT06 C05B-03L — genuine localhost HTTP byte stream + SQLCipher + durable LAB ACK.

Test fixture pre-approves staff/device/capture; real backend JWT and workstation
guards run. No product route/installer/TLS/human ceremony/clinical authority.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import os
import socket
import threading
import time
from datetime import datetime
from contextlib import contextmanager

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import Depends, FastAPI, HTTPException, Request
import httpx
import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session
import uvicorn

from backend import models
from backend.routers import auth
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import store_clinical_asset_bytes
from backend.services.imaging_acquisition_preflight_v15 import resolve_acquisition_preflight
from backend.security import create_access_token
from isolated_fue_lot06c.test_c05b03k_hotfolder_to_sqlcipher_v15 import (
    _isolated_hotfolder, _collector_bytes,
)
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    BridgeRejected, _authority, _counts, _issue, approvals,
    bridge as synthetic_sqlcipher_bridge,
)
from tools.imaging_gateway import HotFolder
from tools.imaging_gateway.bridge_background_lab import make_lab_collector
from tools.imaging_gateway.gateway import GatewayError
from tools.imaging_gateway.http_ack_lab_v15 import (
    record_lab_http_ack, sign_lab_receipt,
)
from tools.imaging_gateway.media_validation import validated_mime


def _server_app(engine, claim, media_root, signing_key):
    app = FastAPI(title="C05B03L isolated localhost media-only receipt lab")

    # Async FastAPI dependency: construction and disposal occur on the same
    # Uvicorn event-loop thread. Sync-yield dependencies use AnyIO worker threads,
    # which may differ between enter/exit and invalidate SQLCipher DBAPI objects.
    async def lab_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[auth.get_db] = lab_db

    @app.post("/isolated/lot06l/{capture}")
    async def lab_receive(
        capture: str, request: Request,
        current_user: models.User = Depends(auth.get_current_user),
    ):
        if (os.getenv("ENVIRONMENT") != "test"
                or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
                or os.getenv("DC_V15_06_HTTP_ACK_LAB") != "1"
                or request.client is None
                or request.client.host not in ("127.0.0.1", "::1")):
            raise HTTPException(503, "ISOLATED_LOOPBACK_ONLY")
        if (capture != claim.capture
                or current_user.id != claim.staff
                or current_user.get_employer_id() != claim.tenant):
            raise HTTPException(403, "CAPTURE_STAFF_SCOPE_DENIED")
        token = request.headers.get("x-dc-lab-device", "")
        if request.headers.get("x-dc-lab-patient") != str(claim.patient):
            raise HTTPException(409, "EXPLICIT_PATIENT_APPROVAL_SCOPE_DENIED")
        station_token = request.cookies.get("dc_workstation", "")
        size = 0
        content = bytearray()
        async for chunk in request.stream():
            size += len(chunk)
            if size > 50 * 1024 * 1024:
                raise HTTPException(413, "MEDIA_TOO_LARGE")
            content.extend(chunk)
        raw = bytes(content)
        if (len(raw) != claim.byte_size
                or hashlib.sha256(raw).hexdigest() != claim.digest
                or not validated_mime(raw, "image/png")):
            raise HTTPException(409, "CAPTURE_MEDIA_BINDING_DENIED")
        with Session(engine) as db:
            try:
                db.connection().exec_driver_sql("BEGIN IMMEDIATE")
                # Existing REAL User/Patient/WorkstationMode + LAB device/approval.
                # Human/device approval is pre-staged by TEST, not this endpoint.
                _authority(db, claim, token, station_token)
                preflight = resolve_acquisition_preflight(
                    db, employer_id=claim.tenant, patient_id=claim.patient,
                )
                if (preflight.patient_id != claim.patient
                        or preflight.status != "STAFF_CONFIRMATION_REQUIRED"):
                    raise BridgeRejected("PATIENT_PREFLIGHT_DENIED")
                store_clinical_asset_bytes(
                    db, employer_id=claim.tenant, patient_id=claim.patient,
                    asset_id=claim.asset_id, content=raw, media_root=media_root,
                )
                db.commit()
            except BridgeRejected:
                db.rollback()
                raise HTTPException(409, "APPROVAL_OR_DEVICE_DENIED")
            except Exception:
                db.rollback()
                raise
        try:
            receipt = _issue(engine, claim, token, station_token, media_root)
        except BridgeRejected:
            raise HTTPException(409, "RECEIPT_AUTHORITY_DENIED")
        body = {
            "receipt_id": receipt, "capture": claim.capture, "tenant": claim.tenant,
            "patient": claim.patient, "device": claim.device, "asset_id": claim.asset_id,
            "digest": claim.digest, "size": claim.byte_size, "lab_only": True,
            "clinical_receipt_authorized": False,
        }
        return {**body, "receipt_mac": sign_lab_receipt(body, signing_key)}

    return app


@contextmanager
def _localhost_server(app):
    """Real TCP HTTP on 127.0.0.1 only, never bound to LAN/cabinet interfaces."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.listen(128)
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="error",
        access_log=False, lifespan="off",
    ))
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True,
        name="lot06-lab-loopback",
    )
    thread.start()
    try:
        for _ in range(200):
            if server.started:
                break
            if not thread.is_alive():
                raise AssertionError("LAB HTTP server exited before ready")
            time.sleep(0.025)
        else:
            raise AssertionError("LAB HTTP server timeout")
        yield "http://127.0.0.1:" + str(port)
    finally:
        server.should_exit = True
        thread.join(timeout=8)
        sock.close()
        assert not thread.is_alive(), "LAB TCP server not reaped"


def _prepare_preapproved_capture(engine, claim, media_root, raw):
    # Change only laboratory fixture approval, before any HTTP request;
    # server endpoint must NEVER mint or mutate its own approval.
    with Session(engine) as db:
        asset = create_clinical_asset(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
            mime_type="image/png", created_by=claim.staff,
            provenance_json={
                "ingestion_channel": "C05B03E_SYNTHETIC_ONLY",
                "capture_id": claim.capture, "device": claim.device,
            },
        )
        approved = replace(
            claim, asset_id=asset.id, digest=hashlib.sha256(raw).hexdigest(),
            byte_size=len(raw),
        )
        db.execute(update(approvals).where(
            approvals.c.tenant == claim.tenant,
            approvals.c.device == claim.device,
            approvals.c.capture == claim.capture,
        ).values(
            asset_id=approved.asset_id, digest=approved.digest,
            byte_size=approved.byte_size,
        ))
        db.commit()
    return approved


def test_c05b03l_real_localhost_http_bytes_sqlcipher_lost_ack_and_reboot(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, device_token, station_token, media_root, _ = synthetic_sqlcipher_bridge
    root, source, env = _isolated_hotfolder(tmp_path)
    collector = make_lab_collector(env)
    item, raw = _collector_bytes(collector)
    approved = _prepare_preapproved_capture(engine, claim, media_root, raw)
    with Session(engine) as db:
        staff_email = db.get(models.User, approved.staff).email
    jwt_token = create_access_token({"sub": staff_email})
    url_path = "/isolated/lot06l/" + approved.capture
    auth_header = {"Authorization": "Bearer " + jwt_token}
    headers = {
        **auth_header, "X-DC-Lab-Device": device_token,
        "X-DC-Lab-Patient": str(approved.patient),
        "Content-Type": "application/octet-stream",
    }
    signing_key = Ed25519PrivateKey.generate()
    pinned_public_key = signing_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    app = _server_app(engine, approved, media_root, signing_key)
    assert _counts(engine) == (0, 0, 0)
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, timeout=15.0, trust_env=False,
    ) as http:
        # Real TCP request with actual spool bytes, not a mocked _issue call.
        assert http.post(url_path, content=raw, headers={
            k: v for k, v in headers.items() if k != "Authorization"
        }).status_code == 401
        http.cookies.set("dc_workstation", "wrong")
        assert http.post(url_path, content=raw, headers=headers).status_code == 423
        http.cookies.set("dc_workstation", station_token)
        assert http.post(url_path, content=b"wrong", headers=headers).status_code == 409
        assert http.post(url_path, content=raw, headers={
            **headers, "X-DC-Lab-Patient": str(approved.patient + 1),
        }).status_code == 409
        assert http.post(url_path, content=raw, headers={
            **headers, "X-DC-Lab-Device": "unregistered-device-token",
        }).status_code == 409
        assert _counts(engine) == (0, 0, 0)
        # JWT+real WorkstationMode+LAB device and approval + bytes + SQLCipher.
        a = http.post(url_path, content=collector.read_verified(item["id"]), headers=headers)
        assert a.status_code == 200, (a.status_code, a.text[:300])
        reply = a.json()
        assert reply["clinical_receipt_authorized"] is False
        assert reply["digest"] == item["digest"]
        assert _counts(engine) == (1, 1, 1)
        # Response lost: client has not recorded ACK. Server already committed.
        assert collector.items()[0]["state"] == "PENDING_CONFIRMATION"
        restarted = HotFolder(collector.config)
        assert restarted.items()[0]["state"] == "PENDING_CONFIRMATION"
        b = http.post(url_path, content=restarted.read_verified(item["id"]), headers=headers)
        assert b.status_code == 200, (b.status_code, b.text[:300])
        assert b.json() == reply
        assert _counts(engine) == (1, 1, 1)

        with pytest.raises(GatewayError, match="SIGNATURE_MISMATCH"):
            record_lab_http_ack(
                restarted, item_id=item["id"],
                reply={**reply, "receipt_mac": "0" * 128},
                server_public_key=pinned_public_key, expected_capture=approved.capture,
                expected_device=approved.device, expected_tenant=approved.tenant,
                expected_patient=approved.patient,
            )
        with pytest.raises(GatewayError, match="SCOPE_CONFLICT"):
            record_lab_http_ack(
                restarted, item_id=item["id"], reply=reply,
                server_public_key=pinned_public_key, expected_capture=approved.capture,
                expected_device=approved.device, expected_tenant=approved.tenant,
                expected_patient=approved.patient + 1,
            )
        assert restarted.items()[0]["state"] == "PENDING_CONFIRMATION"
        rid = record_lab_http_ack(
            restarted, item_id=item["id"], reply=reply,
            server_public_key=pinned_public_key, expected_capture=approved.capture,
            expected_device=approved.device, expected_tenant=approved.tenant,
            expected_patient=approved.patient,
        )
        assert rid == reply["receipt_id"]
        assert _counts(engine) == (1, 1, 1)
        confirmed_restart = HotFolder(collector.config)
        assert confirmed_restart.items()[0]["state"] == "LAB_ACK_CONFIRMED"
        assert confirmed_restart.read_verified(item["id"]) == raw
        assert record_lab_http_ack(
            confirmed_restart, item_id=item["id"], reply=reply,
            server_public_key=pinned_public_key, expected_capture=approved.capture,
            expected_device=approved.device, expected_tenant=approved.tenant,
            expected_patient=approved.patient,
        ) == rid
        assert confirmed_restart.scan_once()["unstable"] == 1
        assert confirmed_restart.scan_once()["duplicate"] == 1
        assert len(confirmed_restart.items()) == 1
        assert _counts(engine) == (1, 1, 1)

        # Real backend station revocation invalidates the same HTTP path.
        with engine.begin() as conn:
            conn.execute(update(models.WorkstationMode.__table__).where(
                models.WorkstationMode.__table__.c.id == approved.station
            ).values(revoked_at=datetime.utcnow()))
        assert http.post(url_path, content=raw, headers=headers).status_code == 423
        assert _counts(engine) == (1, 1, 1)
    assert source.read_bytes() == raw
    print("C05B03L_REAL_TCP_HTTP_MEDIA_SQLCIPHER_DURABLE_SIGNED_LAB_ACK_PASS")


def test_c05b03l_lab_ack_requires_test_isolation_and_signature(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, token, station, media_root, _ = synthetic_sqlcipher_bridge
    root, _source, env = _isolated_hotfolder(tmp_path)
    collector = make_lab_collector(env)
    item, raw = _collector_bytes(collector)
    approved = _prepare_preapproved_capture(engine, claim, media_root, raw)
    fake = {
        "receipt_id": "LAB-ONLY-" + "a" * 32,
        "capture": approved.capture, "tenant": approved.tenant,
        "patient": approved.patient, "device": approved.device,
        "asset_id": approved.asset_id, "digest": approved.digest,
        "size": approved.byte_size, "lab_only": True,
        "clinical_receipt_authorized": False,
    }
    signed = {**fake, "receipt_mac": sign_lab_receipt(fake, Ed25519PrivateKey.generate())}
    call = dict(
        item_id=item["id"], reply=signed,
        server_public_key=Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw),
        expected_capture=approved.capture, expected_device=approved.device,
        expected_tenant=approved.tenant, expected_patient=approved.patient,
    )
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(GatewayError, match="LAB_HTTP_ACK_DISABLED"):
        record_lab_http_ack(collector, **call)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DC_V15_06_HTTP_ACK_LAB", "0")
    with pytest.raises(GatewayError, match="LAB_HTTP_ACK_DISABLED"):
        record_lab_http_ack(collector, **call)
    # A correctly signed synthetic shape alone does NOT prove server persistence.
    # Without real receipt authority these helpers remain LAB-only by construction.
    assert collector.items()[0]["state"] == "PENDING_CONFIRMATION"
    assert _counts(engine) == (0, 0, 0)
