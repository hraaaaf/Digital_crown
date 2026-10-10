from backend.core.key_material import mobile_pairing_key_hex
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
        master_key=mobile_pairing_key_hex(),
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



def _paired_mobile_token(db, user):
    device_id = str(uuid.uuid4())
    db.add(models.MobilePairedDevice(
        device_id=device_id,
        user_id=user.id,
        employer_id=user.get_employer_id(),
        client_public_key_hex='04' + ('11' * 64),
        refresh_jti=f'refresh-{uuid.uuid4().hex}',
    ))
    db.commit()
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return _create_mobile_jwt(user.id, role, user.get_employer_id(), device_id)


def _snapshot(client, token: str):
    return client.get(
        "/api/mobile/snapshot",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_old_mobile_jwt_is_rejected_after_cabinet_revocation(client, db, dentiste):
    old_token = _paired_mobile_token(db, dentiste)
    assert _snapshot(client, old_token).status_code == 200

    token_blacklist.revoke_mobile_access(dentiste.id, db)

    assert _snapshot(client, old_token).status_code == 401


def test_new_mobile_jwt_after_revocation_is_accepted(client, db, dentiste):
    old_token = _paired_mobile_token(db, dentiste)
    token_blacklist.revoke_mobile_access(dentiste.id, db)
    new_token = _paired_mobile_token(db, dentiste)

    assert _snapshot(client, old_token).status_code == 401
    assert _snapshot(client, new_token).status_code == 200


def test_revocation_is_tenant_scoped(client, db, dentiste):
    other = _second_cabinet(db)
    own_token = _paired_mobile_token(db, dentiste)
    other_token = _paired_mobile_token(db, other)

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

    old_token = _paired_mobile_token(db, dentiste)
    _pending_pairing(db, dentiste.id, "route")

    with patch("backend.routers.admin._legacy.zka_service.rotate_master_key", return_value="b" * 64):
        response = client.post("/api/admin/revoke-mobile", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["pairing_tokens_invalidated"] >= 1
    assert _snapshot(client, old_token).status_code == 401


def test_admin_revoke_audit_failure_does_not_undo_persisted_revocation(client, db, dentiste, auth_headers):
    dentiste.role = models.UserRole.ADMIN
    dentiste.permissions = {**(dentiste.permissions or {}), "admin": True}
    db.commit()
    old_token = _paired_mobile_token(db, dentiste)
    with patch("backend.routers.admin._legacy.audit_service.log", side_effect=RuntimeError("fictitious audit failure")):
        response = client.post("/api/admin/revoke-mobile", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["audit_recorded"] is False
    token_blacklist._mobile_cutoffs.clear()
    assert _snapshot(client, old_token).status_code == 401


def test_mobile_assistant_cannot_revoke_cabinet(client, db, dentiste):
    assistant = models.User(email="fictitious-assistant-revoke@test.local", hashed_password=get_password_hash("Pass123!"), role=models.UserRole.SECRETAIRE, employer_id=dentiste.id, is_active=True)
    db.add(assistant)
    db.commit()
    token = _paired_mobile_token(db, assistant)
    response = client.post("/api/admin/revoke-mobile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (401, 403)
    assert db.query(models.MobilePairedDevice).filter_by(user_id=assistant.id, revoked_at=None).count() == 1


def test_admin_revoke_never_calls_storage_rotation(client, db, dentiste, auth_headers):
    dentiste.role = models.UserRole.ADMIN
    dentiste.permissions = {**(dentiste.permissions or {}), "admin": True}
    db.commit()
    with patch("backend.routers.admin._legacy.zka_service.rotate_master_key", side_effect=AssertionError("Storage rotation forbidden")) as rotation:
        response = client.post("/api/admin/revoke-mobile", headers=auth_headers)
    assert response.status_code == 200
    rotation.assert_not_called()


def test_committed_revocation_reports_real_audit_commit_failure(client, db, dentiste, auth_headers):
    dentiste.role = models.UserRole.ADMIN
    dentiste.permissions = {**(dentiste.permissions or {}), "admin": True}
    db.commit()
    old_token = _paired_mobile_token(db, dentiste)
    commit = db.commit
    calls = 0
    def failing_audit_commit():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fictitious second commit failure")
        return commit()
    with patch.object(db, "commit", side_effect=failing_audit_commit):
        response = client.post("/api/admin/revoke-mobile", headers=auth_headers)
    assert calls == 2
    assert response.status_code == 200
    assert response.json()["audit_recorded"] is False
    token_blacklist._mobile_cutoffs.clear()
    assert _snapshot(client, old_token).status_code == 401
