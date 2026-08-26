from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
import pytest
from starlette.requests import Request

from backend import models
from backend.models_mobile_passkey import MobilePasskeyCredential
from backend.routers import mobile as mobile_router
from backend.routers import mobile_legacy
from backend.routers import mobile_passkey
from backend.services.mobile_biometric import (
    WEBAUTHN_ORIGIN,
    consume_challenge,
    issue_biometric_access_token,
    issue_challenge,
)


def _user(db, email: str, *, employer_id: int | None = None):
    user = models.User(
        email=email,
        hashed_password="test-only-hash",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Test",
        is_active=True,
        is_licensed=True,
        is_suspended=False,
        is_archived=False,
        employer_id=employer_id,
        approval_status="approved",
        permissions={"patients": True, "agenda": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _device(db, *, device_id: str, user_id: int, employer_id: int):
    row = models.MobilePairedDevice(
        device_id=device_id,
        user_id=user_id,
        employer_id=employer_id,
        client_public_key_hex="04" + "11" * 64,
        refresh_jti=f"refresh-{device_id}",
    )
    db.add(row)
    db.commit()
    return row


def _credential(db, *, user_id: int, employer_id: int, device_id: str, enabled: bool):
    row = MobilePasskeyCredential(
        credential_id="cred-" + device_id,
        user_id=user_id,
        employer_id=employer_id,
        device_id=device_id,
        credential_public_key="A" * 64,
        sign_count=0,
        transports=["internal"],
        credential_device_type="single_device",
        credential_backed_up=False,
        enabled_at=datetime.utcnow() if enabled else None,
    )
    db.add(row)
    db.commit()
    return row


def _origin_request(origin: str = WEBAUTHN_ORIGIN):
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/mobile/passkey/registration/options",
        "headers": [(b"origin", origin.encode("ascii"))],
        "scheme": "https",
        "server": ("digitalcrown.local", 8005),
        "client": ("127.0.0.1", 12345),
        "query_string": b"",
    })


def _durable_token(user, tenant_id: int, device_id: str) -> str:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return mobile_router._create_mobile_jwt(user.id, role, tenant_id, device_id)


def test_enabled_passkey_blocks_durable_mobile_token_but_accepts_uv(db):
    owner = _user(db, "m6i-owner@example.test")
    device = _device(
        db,
        device_id="11111111-1111-4111-8111-111111111111",
        user_id=owner.id,
        employer_id=owner.id,
    )
    _credential(db, user_id=owner.id, employer_id=owner.id, device_id=device.device_id, enabled=True)

    durable = _durable_token(owner, owner.id, device.device_id)
    with pytest.raises(HTTPException) as locked:
        mobile_legacy._decode_mobile_identity(f"Bearer {durable}", db)
    assert locked.value.status_code == 423
    assert locked.value.detail["code"] == "MOBILE_BIOMETRIC_LOCKED"

    uv, ttl = issue_biometric_access_token(user=owner, employer_id=owner.id, device_id=device.device_id)
    assert ttl == 300
    user, tenant_id, payload = mobile_legacy._decode_mobile_identity(f"Bearer {uv}", db)
    assert user.id == owner.id
    assert tenant_id == owner.id
    assert payload["biometric_uv"] is True


def test_pending_passkey_does_not_gate_normal_mobile_routes(db):
    owner = _user(db, "m6i-pending@example.test")
    device = _device(
        db,
        device_id="22222222-2222-4222-8222-222222222222",
        user_id=owner.id,
        employer_id=owner.id,
    )
    _credential(db, user_id=owner.id, employer_id=owner.id, device_id=device.device_id, enabled=False)
    durable = _durable_token(owner, owner.id, device.device_id)
    user, tenant_id, _payload = mobile_legacy._decode_mobile_identity(f"Bearer {durable}", db)
    assert user.id == owner.id
    assert tenant_id == owner.id


def test_enable_requires_uv_and_activates_only_the_bound_pending_credential(db):
    owner = _user(db, "m6i-enable@example.test")
    device = _device(
        db,
        device_id="26262626-2626-4262-8262-262626262626",
        user_id=owner.id,
        employer_id=owner.id,
    )
    pending = _credential(db, user_id=owner.id, employer_id=owner.id, device_id=device.device_id, enabled=False)
    body = mobile_passkey.EnablePasskeyRequest(credential_id=pending.credential_id)

    durable = _durable_token(owner, owner.id, device.device_id)
    with pytest.raises(HTTPException) as locked:
        mobile_passkey.enable_passkey(body, authorization=f"Bearer {durable}", db=db)
    assert locked.value.status_code == 423
    assert pending.enabled_at is None

    uv, _ttl = issue_biometric_access_token(user=owner, employer_id=owner.id, device_id=device.device_id)
    result = mobile_passkey.enable_passkey(body, authorization=f"Bearer {uv}", db=db)
    db.refresh(pending)
    assert result["state"] == "enabled"
    assert result["credential_id"] == pending.credential_id
    assert pending.enabled_at is not None


def test_registration_cannot_replace_enabled_or_duplicate_pending_passkey(db):
    owner = _user(db, "m6i-replace@example.test")
    device = _device(
        db,
        device_id="33333333-3333-4333-8333-333333333333",
        user_id=owner.id,
        employer_id=owner.id,
    )
    token = _durable_token(owner, owner.id, device.device_id)
    auth = f"Bearer {token}"

    enabled = _credential(db, user_id=owner.id, employer_id=owner.id, device_id=device.device_id, enabled=True)
    with pytest.raises(HTTPException) as replace:
        mobile_passkey.registration_options(_origin_request(), authorization=auth, db=db)
    assert replace.value.status_code == 423
    assert replace.value.detail["code"] == "PASSKEY_REPLACEMENT_REQUIRES_DISABLE"

    db.delete(enabled)
    db.commit()
    _credential(db, user_id=owner.id, employer_id=owner.id, device_id=device.device_id, enabled=False)
    with pytest.raises(HTTPException) as duplicate:
        mobile_passkey.registration_options(_origin_request(), authorization=auth, db=db)
    assert duplicate.value.status_code == 409
    assert duplicate.value.detail["code"] == "PASSKEY_ENROLLMENT_PENDING"


def test_webauthn_challenge_is_one_shot_and_device_scoped(db):
    owner = _user(db, "m6i-challenge@example.test")
    device = _device(
        db,
        device_id="44444444-4444-4444-8444-444444444444",
        user_id=owner.id,
        employer_id=owner.id,
    )
    other_device = _device(
        db,
        device_id="45454545-4545-4454-8454-454545454545",
        user_id=owner.id,
        employer_id=owner.id,
    )
    challenge = b"c" * 32
    challenge_id = issue_challenge(
        db,
        purpose="authenticate",
        user_id=owner.id,
        employer_id=owner.id,
        device_id=device.device_id,
        challenge=challenge,
    )

    with pytest.raises(HTTPException) as wrong_device:
        consume_challenge(
            db,
            challenge_id=challenge_id,
            purpose="authenticate",
            user_id=owner.id,
            employer_id=owner.id,
            device_id=other_device.device_id,
        )
    assert wrong_device.value.status_code == 410

    assert consume_challenge(
        db,
        challenge_id=challenge_id,
        purpose="authenticate",
        user_id=owner.id,
        employer_id=owner.id,
        device_id=device.device_id,
    ) == challenge
    with pytest.raises(HTTPException) as replay:
        consume_challenge(
            db,
            challenge_id=challenge_id,
            purpose="authenticate",
            user_id=owner.id,
            employer_id=owner.id,
            device_id=device.device_id,
        )
    assert replay.value.status_code == 410


def test_registration_rejects_ip_origin_before_any_webauthn_work(db):
    owner = _user(db, "m6i-origin@example.test")
    device = _device(
        db,
        device_id="55555555-5555-4555-8555-555555555555",
        user_id=owner.id,
        employer_id=owner.id,
    )
    auth = f"Bearer {_durable_token(owner, owner.id, device.device_id)}"
    with pytest.raises(HTTPException) as exc:
        mobile_passkey.registration_options(
            _origin_request("https://192.168.1.50:5173"),
            authorization=auth,
            db=db,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "WEBAUTHN_STABLE_ORIGIN_REQUIRED"


def test_m6i_runtime_contract_files_are_pinned_and_stable_origin_is_certified():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    setup_https = Path("scripts/setup-https.ps1").read_text(encoding="utf-8")
    config = Path("backend/config.py").read_text(encoding="utf-8")
    router_init = Path("backend/routers/__init__.py").read_text(encoding="utf-8")

    assert "webauthn==3.0.0" in requirements
    assert "zeroconf==0.150.0" in requirements
    assert "digitalcrown.local $lanIP" in setup_https
    assert "https://digitalcrown.local:5173" in config
    assert "install_mobile_biometric_identity_gate" in router_init
