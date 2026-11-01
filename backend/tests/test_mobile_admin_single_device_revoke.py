"""CPV2-01C: an administrator can revoke ONE orphaned offline phone only.

Disposable in-memory SQLite; all JWTs, phones, users, and patients are synthetic.
"""
from datetime import datetime
import uuid

from backend import models
from backend.tests.test_mobile_single_device_unlink import _claim
from backend.tests.conftest import make_user


def test_admin_can_revoke_only_phone_a_without_disconnecting_phone_b(client, db, dentiste, auth_headers):
    phone_a = _claim(client, db, dentiste)
    phone_b = _claim(client, db, dentiste)
    headers_a = {'Authorization': 'Bearer ' + phone_a['access_token']}
    headers_b = {'Authorization': 'Bearer ' + phone_b['access_token']}

    list_response = client.get('/api/admin/mobile-devices', headers=auth_headers)
    assert list_response.status_code == 200
    devices = list_response.json()['devices']
    assert {phone_a['device_id'], phone_b['device_id']} <= {d['device_id'] for d in devices}
    assert all('access_token' not in d and 'refresh_token' not in d
               and 'client_public_key_hex' not in d for d in devices)

    response = client.post('/api/admin/mobile-devices/' + phone_a['device_id'] + '/revoke',
                           headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json() == {'revoked': True}
    assert client.get('/api/mobile/snapshot', headers=headers_a).status_code == 401
    assert client.post('/api/mobile/refresh-token', json={
        'refresh_token': phone_a['refresh_token'],
    }).status_code == 401
    assert client.get('/api/mobile/snapshot', headers=headers_b).status_code == 200
    assert client.post('/api/mobile/refresh-token', json={
        'refresh_token': phone_b['refresh_token'],
    }).status_code == 200

    # Idempotent same-cabinet retry, no tenant-wide cutoff.
    assert client.post('/api/admin/mobile-devices/' + phone_a['device_id'] + '/revoke',
                       headers=auth_headers).status_code == 200
    listed = client.get('/api/admin/mobile-devices', headers=auth_headers).json()['devices']
    assert any(d['device_id'] == phone_a['device_id'] and d['revoked'] for d in listed)
    assert any(d['device_id'] == phone_b['device_id'] and not d['revoked'] for d in listed)


def test_admin_list_and_revoke_require_desktop_admin_auth(client, db, dentiste):
    device = _claim(client, db, dentiste)
    assert client.get('/api/admin/mobile-devices').status_code == 401
    assert client.post('/api/admin/mobile-devices/' + device['device_id'] + '/revoke').status_code == 401
    bearer = {'Authorization': 'Bearer ' + device['access_token']}
    assert client.get('/api/admin/mobile-devices', headers=bearer).status_code in (401, 403)
    assert client.post('/api/admin/mobile-devices/' + device['device_id'] + '/revoke',
                       headers=bearer).status_code in (401, 403)


def test_admin_must_not_revoke_or_disclose_other_cabinet_device(client, db, dentiste, auth_headers):
    # A legitimate but unrelated record must behave like an absent device.
    other_owner = make_user(db, email='unrelated-mobile-owner@synthetic.local')
    other_id = str(uuid.uuid4())
    foreign = models.MobilePairedDevice(
        device_id=other_id, user_id=other_owner.id, employer_id=other_owner.id,
        client_public_key_hex='04' + '1' * 128, refresh_jti='disposable-foreign',
        created_at=datetime.utcnow(), last_seen_at=datetime.utcnow(),
    )
    db.add(foreign)
    db.commit()
    ids = {x['device_id'] for x in client.get('/api/admin/mobile-devices', headers=auth_headers).json()['devices']}
    assert other_id not in ids
    denied = client.post('/api/admin/mobile-devices/' + other_id + '/revoke', headers=auth_headers)
    assert denied.status_code == 404
    db.refresh(foreign)
    assert foreign.revoked_at is None
