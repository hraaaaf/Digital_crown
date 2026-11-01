"""C05B-03M security FUE: real TCP+SQLCipher with independent device and staff authority.

A separate simulated confirmation action is performed against actual User and
WorkstationMode records; never claim a genuine human UI click or enrollment.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import httpx
import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend import models
from backend.security import create_access_token
from backend.services.clinical_asset_storage import store_clinical_asset_bytes
from isolated_fue_lot06c.c05b03m_security_gate_lab import (
    BridgeRejected, TestOnlyMediaAuthority, identity, provision_test_device,
    record_staff_review_fixture, review, review_audit, sign_test_device_claim,
)
from isolated_fue_lot06c.test_c05b03k_hotfolder_to_sqlcipher_v15 import (
    _isolated_hotfolder, _collector_bytes,
)
from isolated_fue_lot06c.test_c05b03l_http_durable_ack_v15 import (
    _localhost_server, _prepare_preapproved_capture, _server_app,
)
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    _counts, _issue, bridge as synthetic_sqlcipher_bridge, receipts, audit, outbox,
)
from tools.imaging_gateway import HotFolder
from tools.imaging_gateway.bridge_background_lab import make_lab_collector
from tools.imaging_gateway.gateway import GatewayError
from tools.imaging_gateway.http_ack_lab_v15 import record_lab_http_ack


def _setup(bridge, tmp_path):
    engine, claim, device_token, station_token, media_root, _ = bridge
    _root, source, env = _isolated_hotfolder(tmp_path)
    collector = make_lab_collector(env)
    item, raw = _collector_bytes(collector)
    approved = _prepare_preapproved_capture(engine, claim, media_root, raw)
    private = Ed25519PrivateKey.generate()
    with Session(engine) as db:
        challenge = provision_test_device(db, approved, public_key=private.public_key())
        staff_email = db.get(models.User, approved.staff).email
    proof = sign_test_device_claim(approved, challenge, private)
    signing_key = Ed25519PrivateKey.generate()
    server_public = signing_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    app = _server_app(
        engine, approved, media_root, signing_key, security_gate=TestOnlyMediaAuthority(),
    )
    headers = {
        "Authorization": "Bearer " + create_access_token({"sub": staff_email}),
        "X-DC-Lab-Device": device_token,
        "X-DC-Lab-Device-Proof": proof,
        "X-DC-Lab-Patient": str(approved.patient),
        "Content-Type": "application/octet-stream",
    }
    return (engine, approved, device_token, station_token, media_root, source,
            collector, item, raw, private, challenge, headers, app, server_public)


def _post(http, claim, data, headers):
    return http.post("/isolated/lot06l/" + claim.capture, content=data, headers=headers)


def _confirm(engine, claim):
    with Session(engine) as db:
        record_staff_review_fixture(
            db, claim, staff_id=claim.staff, workstation_id=claim.station,
            explicit_confirm=True,
        )


def test_c05b03m_independent_device_key_human_confirmation_and_retry(
    synthetic_sqlcipher_bridge, tmp_path,
):
    (engine, claim, device_token, station_token, media_root, source,
     collector, item, raw, private, challenge, headers, app, server_public) = _setup(
        synthetic_sqlcipher_bridge, tmp_path,
    )
    assert _counts(engine) == (0, 0, 0)
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=15.0,
    ) as http:
        http.cookies.set("dc_workstation", station_token)
        # Preapproved E fixture alone is INSUFFICIENT: distinct staff action missing.
        no_review = _post(http, claim, raw, headers)
        assert no_review.status_code == 409, (no_review.status_code, no_review.text[:200])
        assert _counts(engine) == (0, 0, 0)
        _confirm(engine, claim)

        invalid_proofs = [
            {**headers, "X-DC-Lab-Device-Proof": ""},
            {**headers, "X-DC-Lab-Device-Proof": "0" * 128},
            {**headers, "X-DC-Lab-Device-Proof": sign_test_device_claim(
                replace(claim, patient=claim.patient + 1), challenge, private,
            )},
            {**headers, "X-DC-Lab-Device-Proof": sign_test_device_claim(
                claim, challenge, Ed25519PrivateKey.generate(),
            )},
        ]
        for bad in invalid_proofs:
            denied = _post(http, claim, raw, bad)
            assert denied.status_code == 409, (denied.status_code, denied.text[:150])
        assert _counts(engine) == (0, 0, 0)
        with Session(engine) as db:
            assert db.execute(select(review.c.consumed)).scalar_one() == 0
            assert db.execute(select(review_audit.c.event)).scalar_one() == (
                "SYNTHETIC_STAFF_CONFIRMED"
            )

        accepted = _post(http, claim, collector.read_verified(item["id"]), headers)
        assert accepted.status_code == 200, (accepted.status_code, accepted.text[:250])
        body = accepted.json()
        assert body["clinical_receipt_authorized"] is False
        assert _counts(engine) == (1, 1, 1)
        with Session(engine) as db:
            assert db.execute(select(review.c.consumed)).scalar_one() == 1

        # LOST ACK before local WAL write, then device/agent reboot:
        reboot = HotFolder(collector.config)
        assert reboot.items()[0]["state"] == "PENDING_CONFIRMATION"
        replay = _post(http, claim, reboot.read_verified(item["id"]), headers)
        assert replay.status_code == 200
        assert replay.json() == body
        assert _counts(engine) == (1, 1, 1)
        rid = record_lab_http_ack(
            reboot, item_id=item["id"], reply=body,
            server_public_key=server_public,
            expected_capture=claim.capture, expected_device=claim.device,
            expected_tenant=claim.tenant, expected_patient=claim.patient,
        )
        assert rid == body["receipt_id"]
        persisted = HotFolder(collector.config)
        assert persisted.items()[0]["state"] == "LAB_ACK_CONFIRMED"
        assert persisted.read_verified(item["id"]) == raw
        assert record_lab_http_ack(
            persisted, item_id=item["id"], reply=body,
            server_public_key=server_public,
            expected_capture=claim.capture, expected_device=claim.device,
            expected_tenant=claim.tenant, expected_patient=claim.patient,
        ) == rid

        # Revocation after receipt must deny even an idempotent upload replay.
        with engine.begin() as conn:
            conn.execute(update(identity).values(active=0))
        denied = _post(http, claim, raw, headers)
        assert denied.status_code == 409, (denied.status_code, denied.text[:150])
        assert _counts(engine) == (1, 1, 1)
    assert source.read_bytes() == raw
    print("C05B03M_ED25519_DEVICE_PLUS_SEPARATE_STAFF_SQLCIPHER_HTTP_RETRY_LAB_PASS")


def test_c05b03m_expiry_revocation_and_consumption_rollback(
    synthetic_sqlcipher_bridge, tmp_path,
):
    (engine, claim, device_token, station_token, media_root, _source,
     collector, item, raw, private, challenge, headers, app, server_public) = _setup(
        synthetic_sqlcipher_bridge, tmp_path,
    )
    # A staff action is never inferred from an existing synthetic E approval.
    with Session(engine) as db:
        with pytest.raises(BridgeRejected, match="EXPLICIT_STAFF_CONFIRMATION"):
            record_staff_review_fixture(
                db, claim, staff_id=claim.staff, workstation_id=claim.station,
                explicit_confirm=False,
            )
        db.rollback()
    _confirm(engine, claim)

    # The signing-key pin is independent of the bearer device_token.
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=15.0,
    ) as http:
        http.cookies.set("dc_workstation", station_token)
        with engine.begin() as conn:
            conn.execute(update(review).values(expires_at=1))
        assert _post(http, claim, raw, headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)
        with engine.begin() as conn:
            conn.execute(update(review).values(expires_at=4102444800))
            conn.execute(update(identity).values(generation=claim.generation + 1))
        assert _post(http, claim, raw, headers).status_code == 409
        with engine.begin() as conn:
            conn.execute(update(identity).values(generation=claim.generation))
            conn.execute(update(identity).values(
                public_key_hex=Ed25519PrivateKey.generate().public_key().public_bytes(
                    Encoding.Raw, PublicFormat.Raw,
                ).hex(),
            ))
        assert _post(http, claim, raw, headers).status_code == 409
        with engine.begin() as conn:
            conn.execute(update(identity).values(
                public_key_hex=private.public_key().public_bytes(
                    Encoding.Raw, PublicFormat.Raw,
                ).hex(),
            ))
        # Rehearse failure *after* cryptographically bound media exists:
        # the true verifier must not be bypassed just to hit this failpoint.
        with Session(engine) as db:
            store_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=claim.asset_id, content=raw, media_root=media_root,
            )
            db.commit()
        # Receipt failpoint must roll back one-time review consumption.
        gate = TestOnlyMediaAuthority()
        with pytest.raises(BridgeRejected, match="INJECTED_TRANSACTION_ROLLBACK"):
            _issue(
                engine, claim, device_token, station_token, media_root,
                fail_at="after_audit",
                locked_authorize=lambda db, c: gate.consume(
                    db, c, headers["X-DC-Lab-Device-Proof"],
                ),
            )
        with Session(engine) as db:
            assert db.execute(select(review.c.consumed)).scalar_one() == 0
        assert _counts(engine) == (0, 0, 0)

        # Revoked real staff invalidates the independent staff proof at _authority.
        with engine.begin() as conn:
            conn.execute(update(models.User.__table__).where(
                models.User.__table__.c.id == claim.staff,
            ).values(is_active=False))
        assert _post(http, claim, raw, headers).status_code == 401
        assert _counts(engine) == (0, 0, 0)
    print("C05B03M_EXPIRY_ROTATION_ROLLBACK_AND_REVOKED_STAFF_DENIED")


def test_c05b03m_no_sqlcipher_or_not_test_no_enrollment(
    synthetic_sqlcipher_bridge, monkeypatch,
):
    engine, claim, *_ = synthetic_sqlcipher_bridge
    with Session(engine) as db:
        monkeypatch.setenv("ENVIRONMENT", "cabinet")
        with pytest.raises(BridgeRejected, match="SQLCIPHER_TEST_ISOLATION_REQUIRED"):
            provision_test_device(
                db, claim, public_key=Ed25519PrivateKey.generate().public_key(),
            )
        db.rollback()
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("DC06C05B03M_TEST_ONLY", "0")
        with pytest.raises(BridgeRejected, match="SQLCIPHER_TEST_ISOLATION_REQUIRED"):
            provision_test_device(
                db, claim, public_key=Ed25519PrivateKey.generate().public_key(),
            )
        db.rollback()
    print("C05B03M_NON_TEST_DEVICE_ENROLLMENT_HARD_STOP_PASS")
