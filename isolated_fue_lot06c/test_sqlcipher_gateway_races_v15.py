"""LOT06 H-02: FUE gateway challenges, expiry/rotation and six concurrent receipts.

Isolated native SQLCipher and real backend HTTP dependency only. The Windows
private-key store is not part of this Linux CI; DO NOT claim hardware assurance.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from threading import Barrier

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from backend import models
from backend.security import create_access_token, get_password_hash
from isolated_fue_lot06c.test_sqlcipher_http_jwt_capture_bridge_v15 import _make_fixture
from isolated_fue_lot06c.test_sqlcipher_gateway_human_proof_v15 import (
    _bind, _guard, _msg, PASSWORD,
)
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import _counts, bridge


def _setup(bridge, monkeypatch):
    _guard()
    app, engine, claim, station, staff_email, owner_email, _, tmp = _make_fixture(bridge)
    monkeypatch.setenv("DC06C05B03H_LEGACY_DEVICE_TOKEN", bridge[2])
    with Session(engine) as db:
        db.execute(update(models.User.__table__).where(
            models.User.__table__.c.id == claim.staff
        ).values(hashed_password=get_password_hash(PASSWORD)))
        db.commit()
    _bind(app, engine, claim, bridge[4])
    return app, engine, claim, station, (
        create_access_token({"sub": staff_email}),
        create_access_token({"sub": owner_email}),
    ), tmp


def _key():
    signer = Ed25519PrivateKey.generate()
    pub = signer.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    return signer, pub


def _post(client, suffix, jwt, payload=None):
    return client.post(
        "/isolated/h/" + suffix, json=payload or {},
        headers={"Authorization": "Bearer " + jwt},
    )


def _start_enroll(client, owner, claim, key):
    priv, pub = key
    response = _post(client, "enroll/start", owner, {"device": claim.device, "public_hex": pub})
    assert response.status_code == 200, (response.status_code, response.text[:200])
    nonce = response.json()["nonce"]
    binding = dict(nonce=nonce, tenant=claim.tenant, device=claim.device,
                   station=claim.station, generation=claim.generation, public_hex=pub)
    return {"nonce": nonce, "signature": priv.sign(_msg("ENROLL", binding)).hex()}


def _enroll(client, owner, claim, key):
    response = _post(client, "enroll/finish", owner, _start_enroll(client, owner, claim, key))
    assert response.status_code == 200, (response.status_code, response.text[:200])


def _signed_capture(client, staff, priv):
    request = _post(client, "capture/start", staff)
    assert request.status_code == 200, (request.status_code, request.text[:200])
    payload = request.json()
    nonce, binding = payload["nonce"], payload["binding"]
    return {"nonce": nonce, "signature": priv.sign(_msg("CAPTURE", binding)).hex()}


def _approve(client, staff, signed):
    response = _post(client, "approve", staff, {**signed, "password": PASSWORD})
    assert response.status_code == 200, (response.status_code, response.text[:200])


def test_h02_two_pending_enrollments_one_winner_and_expired_nonce(bridge, monkeypatch):
    app, engine, claim, station, (staff, owner), _ = _setup(bridge, monkeypatch)
    first_key = _key()
    second_key = _key()
    with TestClient(app) as client:
        client.cookies.set("dc_workstation", station)
        expired = _start_enroll(client, owner, claim, first_key)
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_enroll SET expires=0 WHERE nonce=?",
                               (expired["nonce"],))
        assert _post(client, "enroll/finish", owner, expired).status_code == 409
        first = _start_enroll(client, owner, claim, first_key)
        second = _start_enroll(client, owner, claim, second_key)
        assert first["nonce"] != second["nonce"]
        assert _post(client, "enroll/finish", owner, second).status_code == 200
        assert _post(client, "enroll/finish", owner, first).status_code == 409
        assert _post(client, "enroll/finish", owner, second).status_code == 409
        with engine.connect() as db:
            row = db.exec_driver_sql(
                "SELECT public_hex, generation FROM c05b03h_devices "
                "WHERE tenant=? AND device=?", (claim.tenant, claim.device),
            ).one()
            assert row[0] == second_key[1]
            assert row[1] == claim.generation
            assert db.exec_driver_sql(
                "SELECT COUNT(*) FROM c05b03h_devices"
            ).scalar_one() == 1
        assert _counts(engine) == (0, 0, 0)
    print("C05B03H02_PENDING_ENROLLMENT_RACE_AND_EXPIRATION_FAIL_CLOSED")


def test_h02_capture_grant_expiry_rotation_and_revocation(bridge, monkeypatch):
    app, engine, claim, station, (staff, owner), _ = _setup(bridge, monkeypatch)
    key = _key()
    with TestClient(app) as client:
        client.cookies.set("dc_workstation", station)
        _enroll(client, owner, claim, key)
        stale_capture = _signed_capture(client, staff, key[0])
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_capture SET expires=0 WHERE nonce=?",
                               (stale_capture["nonce"],))
        assert _post(client, "approve", staff, {**stale_capture, "password": PASSWORD}).status_code == 409

        stale_grant = _signed_capture(client, staff, key[0])
        _approve(client, staff, stale_grant)
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_grants SET expires=0 WHERE nonce=?",
                               (stale_grant["nonce"],))
        assert _post(client, "issue", staff, stale_grant).status_code == 409
        assert _counts(engine) == (0, 0, 0)

        fresh = _signed_capture(client, staff, key[0])
        _approve(client, staff, fresh)
        with engine.begin() as db:
            db.exec_driver_sql(
                "UPDATE c05b03h_devices SET generation=generation+1"
            )
        assert _post(client, "issue", staff, fresh).status_code == 409
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_devices SET generation=?", (claim.generation,))
            db.exec_driver_sql("UPDATE c05b03h_devices SET active=0")
        assert _post(client, "issue", staff, fresh).status_code == 409

        # A rotated public key no longer validates the pending old signature.
        attacker_key = _key()
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_devices SET active=1,public_hex=?",
                               (attacker_key[1],))
        assert _post(client, "issue", staff, fresh).status_code == 409
        with engine.begin() as db:
            db.exec_driver_sql("UPDATE c05b03h_devices SET public_hex=?", (key[1],))
        assert _counts(engine) == (0, 0, 0)
        good = _post(client, "issue", staff, fresh)
        assert good.status_code == 200, (good.status_code, good.text[:200])
        assert good.json()["clinical_receipt_authorized"] is False
        assert _counts(engine) == (1, 1, 1)
    print("C05B03H02_CAPTURE_GRANT_EXPIRY_REVOKE_ROTATE_FAIL_CLOSED")


def test_h02_six_concurrent_issuers_one_human_grant(bridge, monkeypatch, tmp_path):
    app, engine, claim, station, (staff, owner), _ = _setup(bridge, monkeypatch)
    key = _key()
    with TestClient(app) as client:
        client.cookies.set("dc_workstation", station)
        _enroll(client, owner, claim, key)
        signed = _signed_capture(client, staff, key[0])
        _approve(client, staff, signed)

    ready = Barrier(7)
    def worker(_idx):
        with TestClient(app, raise_server_exceptions=False) as client:
            client.cookies.set("dc_workstation", station)
            ready.wait(timeout=20)
            response = _post(client, "issue", staff, signed)
            return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=6) as pool:
        pending = [pool.submit(worker, i) for i in range(6)]
        ready.wait(timeout=20)
        results = [job.result(timeout=30) for job in pending]
    assert sorted(code for code, _ in results) == [200, 409, 409, 409, 409, 409], results
    successful = [result for code, result in results if code == 200]
    assert len(successful) == 1
    assert successful[0]["clinical_receipt_authorized"] is False
    assert successful[0]["receipt_id"].startswith("LAB-ONLY-")
    assert _counts(engine) == (1, 1, 1)
    with engine.connect() as con:
        for table in ("c05b03h_capture", "c05b03h_grants"):
            assert con.exec_driver_sql(
                "SELECT used FROM " + table + " WHERE nonce=?", (signed["nonce"],)
            ).scalar_one() == 1
    out = Path(os.getenv("DC06C05B03H02_EVIDENCE_DIR", str(tmp_path)))
    out.mkdir(parents=True, exist_ok=True)
    (out / "lot06c05b03h02-races.json").write_text(json.dumps({
        "kind": "C05B03H02_NATIVE_SQLCIPHER_REAL_JWT_HTTP_CONCURRENCY_LAB",
        "two_pending_enrollments_one_winner_verified_in_sibling_fue": True,
        "expired_enrollment_capture_grant_denied_in_sibling_fue": True,
        "revoked_or_generation_rotated_gateway_denied_in_sibling_fue": True,
        "six_concurrent_http_issuers_one_receipt": True,
        "five_replayed_authorizations_rejected": True,
        "single_sqlcipher_receipt_audit_outbox": True,
        "real_sensor_attestation": False,
        "hardware_windows_key_protected": False,
        "production_migration_applied": False,
        "actual_clinical_ui_approval": False,
        "product_ready": False,
        "clinical_go": False
    }, sort_keys=True, indent=2) + "\n", encoding="utf8")
    print("C05B03H02_SIX_CONCURRENT_HTTP_WRITERS_ONE_RECEIPT_PASS")
