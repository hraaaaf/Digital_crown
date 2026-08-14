"""P1-2 — Régressions de sécurité des credentials mobiles ZKA."""
from datetime import datetime, timedelta, timezone
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from jose import jwt

from backend import models
from backend.config import settings
from backend.routers.mobile import _create_mobile_jwt
from backend.security import ALGORITHM, SECRET_KEY, TokenBlacklist, token_blacklist


def _pairing_record(db, dentiste):
    record = models.ZKAPairingToken(
        token=str(uuid.uuid4()),
        employer_id=dentiste.id,
        public_id="0123456789abcdef",
        master_key="ab" * 32,
        role="DENTISTE",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _client_public_key_hex() -> str:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def test_mobile_jwt_is_bounded_to_configured_24h_and_has_jti():
    before = datetime.now(timezone.utc)
    token = _create_mobile_jwt(123, "DENTISTE")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    after = datetime.now(timezone.utc)

    assert payload["type"] == "mobile"
    assert payload["jti"]
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert before + timedelta(hours=settings.MOBILE_TOKEN_EXPIRE_HOURS) - timedelta(seconds=2) <= expires_at
    assert expires_at <= after + timedelta(hours=settings.MOBILE_TOKEN_EXPIRE_HOURS) + timedelta(seconds=2)
    assert settings.MOBILE_TOKEN_EXPIRE_HOURS == 24


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


def test_revocation_lookup_failure_is_fail_closed():
    class BrokenDB:
        def query(self, *_args, **_kwargs):
            raise RuntimeError("revocation store unavailable")

    blacklist = TokenBlacklist()
    assert blacklist.is_revoked("unknown-jti", BrokenDB()) is True


def test_invalid_ecdh_key_does_not_consume_pairing_token(client, db, dentiste):
    record = _pairing_record(db, dentiste)

    response = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": "deadbeef"},
    )
    assert response.status_code == 400

    db.expire_all()
    refreshed = db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id == record.id).first()
    assert refreshed.used_at is None


def test_missing_ecdh_key_does_not_consume_pairing_token(client, db, dentiste):
    record = _pairing_record(db, dentiste)

    response = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": None},
    )
    assert response.status_code == 400

    db.expire_all()
    refreshed = db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id == record.id).first()
    assert refreshed.used_at is None


def test_valid_pairing_consumes_once_and_replay_is_rejected(client, db, dentiste):
    record = _pairing_record(db, dentiste)
    client_public_key_hex = _client_public_key_hex()

    first = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": client_public_key_hex},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["publicId"] == record.public_id
    assert body["server_public_key_hex"]
    assert body["encrypted_master_key_hex"]

    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "mobile"
    assert payload["jti"]

    db.expire_all()
    refreshed = db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id == record.id).first()
    assert refreshed.used_at is not None

    replay = client.post(
        "/api/mobile/claim-token",
        json={"token": record.token, "client_public_key_hex": client_public_key_hex},
    )
    assert replay.status_code == 404
