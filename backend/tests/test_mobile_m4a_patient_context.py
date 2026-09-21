from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401 — register Core table before test DB create_all
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_mobile_runtime_state(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4a-rate-limit.json'))
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
    yield
    _license_cache.clear()
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False


def _user(db, *, email, role=models.UserRole.DENTISTE, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='M4A User',
        is_active=True,
        is_licensed=True,
        license_expires_at=datetime.utcnow() + timedelta(days=30),
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status='approved',
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, owner, *, dossier='DC-0042'):
    patient = models.Patient(
        numero_dossier=dossier,
        nom='BENNANI',
        prenom='Sara',
        date_naissance=datetime(1992, 5, 18),
        sexe='F',
        employer_id=owner.id,
        telephone='0612345678',
        assurance='MUTUELLE',
        antecedents_medicaux='Allergie pénicilline',
        motif_consultation='Contrôle',
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


def _auth(client, user):
    response = client.post('/api/auth/login', data={'username': user.email, 'password': 'TestPass123!'})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def _claim(client, credential):
    return client.post('/api/mobile/claim-token', json={
        'token': credential,
        'client_public_key_hex': _client_public_key(),
    })


def _issue_patient_bridge(client, headers, patient_id, target_user_id=None):
    payload = {'resource_type': 'patient', 'resource_id': patient_id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    return client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=headers)


def test_patient_bridge_full_protocol_is_opaque_and_opens_exact_patient(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.nom_complet = 'Dr M4A'
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)

    captured_qr = {}

    def _capture_qr_payload(payload, **_kwargs):
        captured_qr['payload'] = payload
        return BytesIO(b'm4a-opaque-qr-proof')

    monkeypatch.setattr(
        mobile_resource_bridge._admin_legacy.QRService,
        'generate_qr_bytes',
        staticmethod(_capture_qr_payload),
    )