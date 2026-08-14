from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from backend import models
from backend.routers.mobile import _create_mobile_jwt
from backend.security import ALGORITHM, SECRET_KEY, token_blacklist


def _pairing_record(db, dentiste):
    record = models.ZKAPairingToken(
        token=str(uuid.uuid4()),
        employer_id=dentiste.id,
        public_id="abcdef1234567890",
        master_key="a" * 64,
        role="DENTISTE",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_mobile_jwt_expires_within_24_hours(dentiste):
    before = datetime.now(timezone.utc)
    token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    after = datetime.now(timezone.utc)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert before + timedelta(hours=24) - timedelta(seconds=2) <= expiry
    assert expiry <= after + timedelta(hours=24) + timedelta(seconds=2)
    assert payload.get("jti")


def test_mobile_token_without_jti_is_rejected(client, dentiste):
    token = jwt.encode(
        {
            "sub": str(dentiste.id),
            "type": "mobile",
            "role": "DENTISTE",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = client.get(
        "/api/mobile/snapshot",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_revoked_mobile_token_is_rejected(client, db, dentiste):
    token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    token_blacklist.revoke(token, db)
    response = client.get(
        "/api/mobile/snapshot",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_pairing_missing_ecdh_key_does_not_consume_token(client, db, dentiste):
    record = _pairing_record(db, dentiste)
    response = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token},
    )
    assert response.status_code == 400
    db.refresh(record)
    assert record.used_at is None


def test_pairing_invalid_ecdh_key_does_not_consume_token(client, db, dentiste):
    record = _pairing_record(db, dentiste)
    response = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": "00"},
    )
    assert response.status_code == 400
    db.refresh(record)
    assert record.used_at is None


def test_pairing_success_consumes_token_once(client, db, dentiste):
    record = _pairing_record(db, dentiste)
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_hex = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()

    first = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": public_hex},
    )
    assert first.status_code == 200
    body = first.json()
    assert body.get("access_token")
    assert body.get("encrypted_master_key_hex")
    assert "masterKey" not in body
    assert "master_key" not in body

    db.refresh(record)
    assert record.used_at is not None

    second = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": public_hex},
    )
    assert second.status_code == 404
