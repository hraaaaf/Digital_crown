from datetime import datetime, timedelta
from pathlib import Path
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from jose import jwt

from backend import models
import backend.routers.admin_legacy as admin_legacy
from backend.routers.admin_legacy import _resolve_mobile_pairing_user
from backend.routers.mobile import _create_mobile_jwt
from backend.routers.mobile_legacy import get_mobile_employer_id, get_mobile_role
from backend.security import ALGORITHM, SECRET_KEY, get_password_hash, token_blacklist
from backend.utils import rate_limit


@pytest.fixture(autouse=True)
def _reset_pairing_rate_limit():
    path = Path(rate_limit._store_path)
    path.unlink(missing_ok=True)
    yield
    path.unlink(missing_ok=True)


def _user(db, *, email, role, employer_id=None, permissions=None, active=True, approval='approved'):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='Mobile User',
        is_active=active,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status=approval,
    )
    db.add(user); db.commit(); db.refresh(user)
    return user


def _pairing(db, owner, user, *, token=None, manual_code='654321'):
    row = models.ZKAPairingToken(
        token=token or uuid.uuid4().hex,
        manual_code=manual_code,
        employer_id=owner.id,
        user_id=user.id if user else None,
        public_id='abcdef1234567890',
        master_key='a' * 64,
        role='DENTISTE',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(row); db.commit(); db.refresh(row)
    return row


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def _claim(client, record, token=None):
    return client.post('/api/mobile/claim-token', json={
        'token': token or record.token,
        'client_public_key_hex': _client_public_key(),
    })


def test_admin_pairing_target_is_same_tenant_active_user(db, dentiste):
    secretary = _user(
        db, email='secretary-target@cabinet.ma', role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id, permissions={'agenda': True, 'patients': True},
    )
    employer_id, target = _resolve_mobile_pairing_user(db, dentiste, secretary.id)
    assert employer_id == dentiste.id
    assert target.id == secretary.id


def test_admin_pairing_target_rejects_cross_tenant(db, dentiste):
    other_owner = _user(db, email='other-owner@cabinet.ma', role=models.UserRole.DENTISTE)
    outsider = _user(db, email='other-secretary@cabinet.ma', role=models.UserRole.SECRETAIRE, employer_id=other_owner.id)
    with pytest.raises(HTTPException) as exc:
        _resolve_mobile_pairing_user(db, dentiste, outsider.id)
    assert exc.value.status_code == 404


def test_admin_pairing_target_rejects_inactive_or_pending(db, dentiste):
    inactive = _user(db, email='inactive-mobile@cabinet.ma', role=models.UserRole.SECRETAIRE, employer_id=dentiste.id, active=False)
    with pytest.raises(HTTPException) as exc:
        _resolve_mobile_pairing_user(db, dentiste, inactive.id)
    assert exc.value.status_code == 403

    pending = _user(db, email='pending-mobile@cabinet.ma', role=models.UserRole.SECRETAIRE, employer_id=dentiste.id, approval='pending')
    with pytest.raises(HTTPException) as exc:
        _resolve_mobile_pairing_user(db, dentiste, pending.id)
    assert exc.value.status_code == 403


def test_pairing_binds_real_user_tenant_role_and_device(client, db, dentiste):
    secretary = _user(
        db, email='secretary-mobile@cabinet.ma', role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id, permissions={'agenda': True, 'patients': True, 'accounting': False, 'payments': False},
    )
    response = _claim(client, _pairing(db, dentiste, secretary))
    assert response.status_code == 200, response.text
    body = response.json()
    payload = jwt.decode(body['access_token'], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload['sub'] == str(secretary.id)
    assert payload['tenant_id'] == dentiste.id
    assert payload['role'] == 'SECRETAIRE'
    assert payload['device_id'] == body['device_id']
    device = db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.device_id == body['device_id']).one()
    assert device.user_id == secretary.id and device.employer_id == dentiste.id


def test_manual_code_is_separate_and_claimable(client, db, dentiste):
    record = _pairing(db, dentiste, dentiste, manual_code='123456')
    assert record.token != record.manual_code
    assert _claim(client, record, token='123456').status_code == 200


def test_legacy_pairing_without_user_id_fails_closed(client, db, dentiste):
    record = _pairing(db, dentiste, None)
    response = _claim(client, record)
    assert response.status_code == 409
    db.refresh(record)
    assert record.used_at is None


def test_role_and_tenant_are_reloaded_from_db(db, dentiste):
    secretary = _user(db, email='role-mobile@cabinet.ma', role=models.UserRole.SECRETAIRE, employer_id=dentiste.id)
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()), user_id=secretary.id, employer_id=dentiste.id,
        client_public_key_hex=_client_public_key(), refresh_jti='refresh-test',
    )
    db.add(device); db.commit()
    token = _create_mobile_jwt(secretary.id, 'DENTISTE', dentiste.id, device.device_id)
    auth = f'Bearer {token}'
    assert get_mobile_employer_id(auth, db) == dentiste.id
    assert get_mobile_role(auth, db) == 'SECRETAIRE'


def test_revoked_device_rejects_access_token(db, dentiste):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()), user_id=dentiste.id, employer_id=dentiste.id,
        client_public_key_hex=_client_public_key(), refresh_jti='refresh-test', revoked_at=datetime.utcnow(),
    )
    db.add(device); db.commit()
    token = _create_mobile_jwt(dentiste.id, 'DENTISTE', dentiste.id, device.device_id)
    with pytest.raises(HTTPException) as exc:
        get_mobile_employer_id(f'Bearer {token}', db)
    assert exc.value.status_code == 401


def test_refresh_replay_revokes_device_and_new_chain(client, db, dentiste):
    claim = _claim(client, _pairing(db, dentiste, dentiste))
    assert claim.status_code == 200, claim.text
    body = claim.json()
    old_refresh = body['refresh_token']
    refreshed = client.post('/api/mobile/refresh-token', json={'refresh_token': old_refresh})
    assert refreshed.status_code == 200, refreshed.text
    new_refresh = refreshed.json()['refresh_token']
    assert client.post('/api/mobile/refresh-token', json={'refresh_token': old_refresh}).status_code == 401
    db.expire_all()
    device = db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.device_id == body['device_id']).one()
    assert device.revoked_at is not None
    assert client.post('/api/mobile/refresh-token', json={'refresh_token': new_refresh}).status_code == 401



def test_finance_export_is_backend_permission_guarded(client, db, dentiste):
    secretary = _user(
        db, email='finance-denied-mobile@cabinet.ma', role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id, permissions={'agenda': True, 'patients': True, 'accounting': False, 'payments': False},
    )
    body = _claim(client, _pairing(db, dentiste, secretary)).json()
    response = client.get(
        '/api/mobile/accounting/export-pdf?year=2026&month=8',
        headers={'Authorization': f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 403


def test_snapshot_does_not_query_finance_when_permission_denied(client, db, dentiste, monkeypatch):
    secretary = _user(
        db, email='snapshot-no-finance@cabinet.ma', role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id, permissions={'agenda': True, 'patients': True, 'accounting': False, 'payments': False},
    )
    body = _claim(client, _pairing(db, dentiste, secretary)).json()
    from backend.services.accounting_service import accounting_service
    def forbidden(*args, **kwargs):
        raise AssertionError('finance backend must not be queried')
    monkeypatch.setattr(accounting_service, 'get_finance_kpis', forbidden)
    response = client.get(
        '/api/mobile/snapshot',
        headers={'Authorization': f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 200, response.text

def test_cabinet_revocation_invalidates_device_and_refresh(client, db, dentiste):
    body = _claim(client, _pairing(db, dentiste, dentiste)).json()
    token_blacklist.revoke_mobile_access(dentiste.id, db)
    assert client.post('/api/mobile/refresh-token', json={'refresh_token': body['refresh_token']}).status_code == 401
    db.expire_all()
    device = db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.device_id == body['device_id']).one()
    assert device.revoked_at is not None

def test_mobile_mutation_uses_numeric_subject_as_user_id(client, db, dentiste):
    body = _claim(client, _pairing(db, dentiste, dentiste)).json()
    response = client.post(
        '/api/mobile/register-device',
        json={'fcm_token': f'm6-license-{uuid.uuid4()}', 'platform': 'ios'},
        headers={'Authorization': f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 200, response.text


def test_permissions_policy_allows_same_origin_camera_only(client):
    response = client.get('/health')
    policy = response.headers.get('permissions-policy', '')
    assert 'camera=(self)' in policy
    assert 'microphone=()' in policy
    assert 'geolocation=()' in policy

def test_admin_revoke_mobile_invalidates_claimed_device_and_refresh(client, db, dentiste, monkeypatch):
    body = _claim(client, _pairing(db, dentiste, dentiste)).json()
    monkeypatch.setattr(admin_legacy, 'current_backend_env_path', lambda: Path('/tmp/digital-crown-test.env'))
    monkeypatch.setattr(admin_legacy.zka_service, 'rotate_master_key', lambda *_args, **_kwargs: 'b' * 64)
    monkeypatch.setattr(admin_legacy.sync_manager, '_perform_sync', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin_legacy.audit_service, 'log', lambda **_kwargs: None)

    result = admin_legacy.revoke_mobile_access(db=db, current_user=dentiste)
    assert result['status'] == 'success'
    assert result['devices_revoked'] == 1
    assert client.post('/api/mobile/refresh-token', json={'refresh_token': body['refresh_token']}).status_code == 401
    db.expire_all()
    device = db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.device_id == body['device_id']).one()
    assert device.revoked_at is not None
