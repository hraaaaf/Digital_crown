from datetime import datetime, timedelta
import uuid
from unittest.mock import patch

from backend import models
from backend.routers.mobile import _create_mobile_jwt
from backend.security import get_password_hash, token_blacklist


def _pending_pairing(db, employer_id: int, suffix: str):
    record = models.ZKAPairingToken(
        token=f"{suffix}-{uuid.uuid4().hex[:12]}",
        employer_id=employer_id,
        public_id=uuid.uuid4().hex[:16],
        master_key="a" * 64,
        role="DENTISTE",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    return record


def _second_cabinet(db):
    user = models.User(
        email=f"mobile-other-{uuid.uuid4().hex[:8]}@test.local",
        hashed_password=get_password_hash("Pass123!"),
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _snapshot(client, token: str):
    return client.get(
        "/api/mobile/snapshot",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_old_mobile_jwt_is_rejected_after_cabinet_revocation(client, db, dentiste):
    old_token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    assert _snapshot(client, old_token).status_code == 200

    token_blacklist.revoke_mobile_access(dentiste.id, db)

    assert _snapshot(client, old_token).status_code == 401


def test_new_mobile_jwt_after_revocation_is_accepted(client, db, dentiste):
    old_token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    token_blacklist.revoke_mobile_access(dentiste.id, db)
    new_token = _create_mobile_jwt(dentiste.id, "DENTISTE")

    assert _snapshot(client, old_token).status_code == 401
    assert _snapshot(client, new_token).status_code == 200


def test_revocation_is_tenant_scoped(client, db, dentiste):
    other = _second_cabinet(db)
    own_token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    other_token = _create_mobile_jwt(other.id, "DENTISTE")

    token_blacklist.revoke_mobile_access(dentiste.id, db)

    assert _snapshot(client, own_token).status_code == 401
    assert _snapshot(client, other_token).status_code == 200


def test_revocation_invalidates_only_pending_pairing_codes(db, dentiste):
    other = _second_cabinet(db)
    own_pending = _pending_pairing(db, dentiste.id, "own")
    other_pending = _pending_pairing(db, other.id, "other")
    own_pending_id = own_pending.id
    other_pending_id = other_pending.id

    result = token_blacklist.revoke_mobile_access(dentiste.id, db)

    assert result["pairing_tokens_invalidated"] >= 1
    assert db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id == own_pending_id).first() is None
    assert db.query(models.ZKAPairingToken).filter(models.ZKAPairingToken.id == other_pending_id).first() is not None


def test_admin_revoke_endpoint_rejects_existing_mobile_token(client, db, dentiste, auth_headers):
    dentiste.role = models.UserRole.ADMIN
    dentiste.permissions = {**(dentiste.permissions or {}), "admin": True}
    db.commit()

    old_token = _create_mobile_jwt(dentiste.id, "DENTISTE")
    _pending_pairing(db, dentiste.id, "route")

    with patch("backend.routers.admin._legacy.zka_service.rotate_master_key", return_value="b" * 64):
        response = client.post("/api/admin/revoke-mobile", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["pairing_tokens_invalidated"] >= 1
    assert _snapshot(client, old_token).status_code == 401
