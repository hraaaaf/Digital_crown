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
    yield
    _license_cache.clear()


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

    options = client.get(
        f'/api/mobile/resource-bridge-options?resource_type=patient&resource_id={patient.id}',
        headers=auth_headers,
    )
    assert options.status_code == 200, options.text
    assert options.json()['contains_patient_data'] is False
    assert options.json()['resource_label'] == 'Dossier patient'
    assert [target['id'] for target in options.json()['targets']] == [dentiste.id]

    issued = _issue_patient_bridge(client, auth_headers, patient.id)
    assert issued.status_code == 200, issued.text
    body = issued.json()
    assert body['contains_patient_data'] is False
    assert body['resource_type'] == 'patient'
    assert body['resource_label'] == 'Dossier patient'
    assert 'patient_id' not in body
    assert 'patient_name' not in body

    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    assert pairing is not None
    assert pairing.token.startswith('c.')
    assert patient.nom not in pairing.token

    qr_payload = captured_qr.get('payload')
    assert qr_payload, 'Le payload envoyé au générateur QR doit être observable.'
    parsed_qr = urlsplit(qr_payload)
    qr_query = parse_qs(parsed_qr.query, strict_parsing=True)
    assert parsed_qr.path == '/mobile/onboarding'
    assert set(qr_query) == {'token'}
    assert qr_query['token'] == [pairing.token]
    assert 'patient_id' not in qr_payload
    assert patient.nom not in qr_payload
    assert patient.numero_dossier not in qr_payload

    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']

    destination = client.post(
        '/api/mobile/resource-bridge-destination',
        json={'credential': pairing.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert destination.status_code == 200, destination.text
    resolved = destination.json()
    assert resolved['destination'] == 'context'
    assert resolved['fallback'] is False
    assert resolved['context']['type'] == 'patient'
    assert resolved['context']['state'] == 'ready'
    assert patient.nom not in resolved['context']['key']

    mobile = client.post(
        '/api/mobile/resource-context',
        json={'context_key': resolved['context']['key']},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert mobile.status_code == 200, mobile.text
    data = mobile.json()
    assert data['type'] == 'patient'
    assert data['patient']['id'] == patient.id
    assert data['patient']['nom'] == 'BENNANI'
    assert data['patient']['prenom'] == 'Sara'
    assert data['patient']['numero_dossier'] == 'DC-0042'
    assert data['patient']['has_medical_alert'] is True
    assert 'antecedents_medicaux' not in data['patient']


def test_patient_bridge_rejects_cross_tenant_resource(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    _cabinet(db, dentiste)
    other_owner = _user(db, email='m4a-other-owner@cabinet.ma')
    other_patient = _patient(db, other_owner, dossier='OTHER-1')

    response = _issue_patient_bridge(client, auth_headers, other_patient.id)
    assert response.status_code == 404
    assert db.query(models.ZKAPairingToken).count() == 0


def test_non_admin_can_only_target_self(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m4a-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True, 'admin': False},
    )
    colleague = _user(
        db,
        email='m4a-colleague@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True, 'admin': False},
    )
    patient = _patient(db, dentiste)
    headers = _auth(client, secretary)

    options = client.get(
        f'/api/mobile/resource-bridge-options?resource_type=patient&resource_id={patient.id}',
        headers=headers,
    )
    assert options.status_code == 200, options.text
    assert [target['id'] for target in options.json()['targets']] == [secretary.id]

    denied = _issue_patient_bridge(client, headers, patient.id, colleague.id)
    assert denied.status_code == 403

    own = _issue_patient_bridge(client, headers, patient.id)
    assert own.status_code == 200, own.text
    assert own.json()['target_user_id'] == secretary.id


def test_permission_revocation_returns_context_error_never_agenda(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m4a-revoke@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True},
    )
    patient = _patient(db, dentiste)
    owner_headers = _auth(client, dentiste)
    issued = _issue_patient_bridge(client, owner_headers, patient.id, secretary.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']

    secretary.permissions = {'agenda': True, 'patients': False}
    db.commit()

    destination = client.post(
        '/api/mobile/resource-bridge-destination',
        json={'credential': pairing.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert destination.status_code == 200, destination.text
    assert destination.json()['destination'] == 'context'
    assert destination.json()['context']['state'] == 'unavailable'
    assert destination.json()['destination'] != 'agenda'

    resource = client.post(
        '/api/mobile/resource-context',
        json={'context_key': destination.json()['context']['key']},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert resource.status_code == 403


def test_soft_deleted_patient_returns_context_error_never_agenda(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    issued = _issue_patient_bridge(client, auth_headers, patient.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']

    patient.deleted_at = datetime.utcnow()
    db.commit()

    destination = client.post(
        '/api/mobile/resource-bridge-destination',
        json={'credential': pairing.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert destination.status_code == 200, destination.text
    assert destination.json()['destination'] == 'context'
    assert destination.json()['context']['state'] == 'unavailable'
    assert destination.json()['destination'] != 'agenda'

    resource = client.post(
        '/api/mobile/resource-context',
        json={'context_key': destination.json()['context']['key']},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert resource.status_code == 404
