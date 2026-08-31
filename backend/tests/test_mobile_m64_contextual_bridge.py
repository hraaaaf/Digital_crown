from datetime import datetime, timedelta
import secrets
from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers.mobile import (
    _allowed_bridge_destinations,
    _bridge_destination_from_token,
    _create_bridge_token,
)
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_mobile_license_cache(monkeypatch):
    """Avoid cross-test leakage from the 60s global licence cache.

    SQLite test rows reuse numeric ids after table cleanup, while the runtime
    cache intentionally survives requests. Clearing it around this module keeps
    M6.4 route tests deterministic without changing production behaviour.
    """
    from backend.main import _license_cache

    _license_cache.clear()
    monkeypatch.setattr(
        'backend.routers.mobile_pairing_secure.LicenseService.get_effective_license',
        AsyncMock(return_value={
            'active': True,
            'license_type': 'PAID',
            'max_devices': 10,
            'release_channel': 'stable',
        }),
    )
    yield
    _license_cache.clear()


def _user(db, *, email, role, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='M64 User',
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status='approved',
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def _pairing(db, owner, user, *, destination='agenda', manual_code='654321'):
    # Route-level calls pass through the global licence middleware. The pairing
    # tests exercise the bridge contract, so make the fixture's cabinet licence
    # explicitly valid instead of depending on unrelated conftest defaults.
    owner.is_licensed = True
    owner.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(owner)
    db.commit()

    token = _create_bridge_token(destination)
    record = models.ZKAPairingToken(
        token=token,
        manual_code=manual_code,
        employer_id=owner.id,
        user_id=user.id,
        public_id='abcdef1234567890',
        master_key='a' * 64,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _claim(client, credential):
    return client.post('/api/mobile/claim-token', json={
        'token': credential,
        'client_public_key_hex': _client_public_key(),
    })


def test_bridge_token_is_opaque_compact_and_server_decodable():
    token = _create_bridge_token('finance')
    assert token.startswith('f.')
    assert len(token) <= 36
    assert len(token.split('.', 1)[1]) >= 32
    assert _bridge_destination_from_token(token) == 'finance'
    assert _bridge_destination_from_token('legacy-token-without-envelope') == 'agenda'
    assert _bridge_destination_from_token('z.' + secrets.token_urlsafe(24)) == 'agenda'


def test_bridge_destinations_are_backend_permission_derived(db, dentiste):
    secretary = _user(
        db,
        email='m64-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={
            'agenda': True,
            'patients': True,
            'accounting': False,
            'payments': False,
        },
    )
    allowed = _allowed_bridge_destinations(secretary)
    assert allowed == ['agenda', 'assistant', 'security', 'dentists', 'lab']
    assert 'finance' not in allowed
    assert 'superadmin' not in allowed

    secretary.permissions = {
        'agenda': True,
        'patients': True,
        'accounting': True,
        'payments': False,
    }
    db.commit()
    assert 'finance' in _allowed_bridge_destinations(secretary)


def test_bridge_requires_agenda_for_dashboard_shell(db, dentiste):
    secretary = _user(
        db,
        email='m64-no-agenda@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': False, 'patients': True, 'accounting': True},
    )
    assert _allowed_bridge_destinations(secretary) == []


def test_contextual_destination_is_resolved_from_consumed_server_record(client, db, dentiste):
    secretary = _user(
        db,
        email='m64-finance@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True, 'accounting': True, 'payments': False},
    )
    record = _pairing(db, dentiste, secretary, destination='finance')
    claimed = _claim(client, record.token)
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']

    response = client.post(
        '/api/mobile/bridge-destination',
        json={'credential': record.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {'destination': 'finance', 'label': 'Finance', 'fallback': False}


def test_bridge_destination_rechecks_permissions_after_pairing(client, db, dentiste):
    secretary = _user(
        db,
        email='m64-revoke-finance@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True, 'accounting': True, 'payments': False},
    )
    record = _pairing(db, dentiste, secretary, destination='finance')
    claimed = _claim(client, record.token)
    assert claimed.status_code == 200, claimed.text

    secretary.permissions = {'agenda': True, 'patients': True, 'accounting': False, 'payments': False}
    db.commit()

    response = client.post(
        '/api/mobile/bridge-destination',
        json={'credential': record.token},
        headers={'Authorization': f"Bearer {claimed.json()['access_token']}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()['destination'] == 'agenda'
    assert response.json()['fallback'] is True


def test_manual_code_recovers_same_server_bound_destination(client, db, dentiste):
    secretary = _user(
        db,
        email='m64-manual@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True},
    )
    record = _pairing(db, dentiste, secretary, destination='lab', manual_code='123456')
    claimed = _claim(client, '123456')
    assert claimed.status_code == 200, claimed.text

    response = client.post(
        '/api/mobile/bridge-destination',
        json={'credential': '123456'},
        headers={'Authorization': f"Bearer {claimed.json()['access_token']}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()['destination'] == 'lab'
    assert response.json()['label'] == 'Labo'


def test_tampering_with_destination_prefix_invalidates_pairing(client, db, dentiste):
    record = _pairing(db, dentiste, dentiste, destination='finance')
    _, secret = record.token.split('.', 1)
    tampered = f'a.{secret}'
    response = _claim(client, tampered)
    assert response.status_code == 404
    db.refresh(record)
    assert record.used_at is None
