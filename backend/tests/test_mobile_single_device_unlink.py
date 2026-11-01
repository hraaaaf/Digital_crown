"""CPV2-01C: unlink ONE paired mobile device, preserve other phones.

Uses the real FastAPI mobile routes with disposable SQLite fixtures only.
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend.tests.test_mobile_credential_hardening import _pairing_record


def _claim(client, db, owner):
    record = _pairing_record(db, owner)
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()
    response = client.post('/api/mobile/claim-token', json={
        'token': record.token,
        'client_public_key_hex': public,
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_unlink_current_device_does_not_revoke_other_phone(client, db, dentiste):
    phone_a = _claim(client, db, dentiste)
    phone_b = _claim(client, db, dentiste)
    assert phone_a['device_id'] != phone_b['device_id']
    a = {'Authorization': 'Bearer ' + phone_a['access_token']}
    b = {'Authorization': 'Bearer ' + phone_b['access_token']}

    assert client.get('/api/mobile/snapshot', headers=a).status_code == 200
    assert client.get('/api/mobile/snapshot', headers=b).status_code == 200
    denied = client.post('/api/mobile/revoke-device')
    assert denied.status_code in (401, 422)

    result = client.post('/api/mobile/revoke-device', headers=a)
    assert result.status_code == 200, result.text
    assert result.json() == {'revoked': True}
    assert client.get('/api/mobile/snapshot', headers=a).status_code == 401
    assert client.post('/api/mobile/refresh-token', json={
        'refresh_token': phone_a['refresh_token'],
    }).status_code == 401
    assert client.post('/api/mobile/revoke-device', headers=a).status_code == 401

    # No cabinet-wide kill switch: device B remains paired and refreshable.
    assert client.get('/api/mobile/snapshot', headers=b).status_code == 200
    assert client.post('/api/mobile/refresh-token', json={
        'refresh_token': phone_b['refresh_token'],
    }).status_code == 200
