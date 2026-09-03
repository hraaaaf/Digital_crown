from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_mobile_runtime_state(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4b-rate-limit.json'))
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


def _user(db, *, email, role=models.UserRole.DENTISTE, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='M4B User',
        is_active=True,
        is_licensed=True,
        license_expires_at=datetime.utcnow() + timedelta(days=30),
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status='approved',
    )
    db.add(user); db.commit(); db.refresh(user); return user


def _patient(db, owner, *, dossier='M4B-0042'):
    patient = models.Patient(
        numero_dossier=dossier,
        nom='BENNANI', prenom='Sara', date_naissance=datetime(1992, 5, 18), sexe='F',
        employer_id=owner.id, telephone='0612345678', assurance='MUTUELLE',
    )
    db.add(patient); db.commit(); db.refresh(patient); return patient


def _analysis(db, patient, *, image_path):
    analysis = models.PanoramicAnalysis(
        patient_id=patient.id,
        image_path=image_path,
        detections_data={'detections': [{'fdi': 11}, {'fdi': 21}]},
        report_narrative='Bilan panoramique enregistré.',
    )
    db.add(analysis); db.commit(); db.refresh(analysis); return analysis


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg); db.commit(); db.refresh(cfg); return cfg


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
    return client.post('/api/mobile/claim-token', json={'token': credential, 'client_public_key_hex': _client_public_key()})


def _issue(client, headers, analysis_id, target_user_id=None):
    payload = {'resource_type': 'panoramic', 'resource_id': analysis_id}
    if target_user_id is not None: payload['target_user_id'] = target_user_id
    return client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=headers)


def _media_file():
    root = Path(mobile_resource_bridge.__file__).resolve().parents[1] / 'static' / 'uploads' / 'panoramic'
    root.mkdir(parents=True, exist_ok=True)
    path = root / f'm4b-{uuid.uuid4().hex}.jpg'
    path.write_bytes(b'\xff\xd8\xff\xe0M4B-PANORAMIC\xff\xd9')
    return path


def test_panoramic_bridge_full_protocol_and_media_are_opaque(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.nom_complet = 'Dr M4B'; dentiste.is_licensed = True; dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste); db.commit(); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    media = _media_file()
    try:
        analysis = _analysis(db, patient, image_path=f'api/static/uploads/panoramic/{media.name}')
        captured_qr = {}
        def _capture(payload, **_kwargs): captured_qr['payload'] = payload; return BytesIO(b'm4b-qr')
        monkeypatch.setattr(mobile_resource_bridge._admin_legacy.QRService, 'generate_qr_bytes', staticmethod(_capture))

        options = client.get(f'/api/mobile/resource-bridge-options?resource_type=panoramic&resource_id={analysis.id}', headers=auth_headers)
        assert options.status_code == 200, options.text
        assert options.json()['resource_type'] == 'panoramic'
        assert options.json()['resource_label'] == 'Radio panoramique'
        assert options.json()['contains_resource_data'] is False

        issued = _issue(client, auth_headers, analysis.id)
        assert issued.status_code == 200, issued.text
        assert issued.json()['contains_patient_data'] is False
        assert issued.json()['contains_resource_data'] is False
        assert 'analysis_id' not in issued.json()
        assert 'image_path' not in issued.json()

        pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
        parsed = urlsplit(captured_qr['payload']); query = parse_qs(parsed.query, strict_parsing=True)
        assert parsed.path == '/mobile/onboarding'; assert set(query) == {'token'}; assert query['token'] == [pairing.token]
        for forbidden_key in ('analysis_id=', 'resource_id=', 'patient_id=', 'image_path='):
            assert forbidden_key not in captured_qr['payload']
        assert patient.nom not in captured_qr['payload']; assert media.name not in captured_qr['payload']

        claimed = _claim(client, pairing.token); assert claimed.status_code == 200, claimed.text
        access = claimed.json()['access_token']; mobile_headers = {'Authorization': f'Bearer {access}'}
        destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=mobile_headers)
        assert destination.status_code == 200, destination.text
        resolved = destination.json(); assert resolved['destination'] == 'context'; assert resolved['fallback'] is False
        assert resolved['context']['type'] == 'panoramic'; assert resolved['context']['state'] == 'ready'

        context = client.post('/api/mobile/resource-context', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
        assert context.status_code == 200, context.text
        data = context.json(); assert data['type'] == 'panoramic'; assert data['panoramic']['patient_name'] == 'BENNANI Sara'
        assert data['panoramic']['landmarks_count'] == 2; assert data['panoramic']['report_saved'] is True
        assert 'id' not in data['panoramic']; assert 'image_path' not in data['panoramic']

        media_response = client.post('/api/mobile/resource-context-media', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
        assert media_response.status_code == 200, media_response.text
        assert media_response.content.startswith(b'\xff\xd8\xff\xe0M4B-PANORAMIC')
        assert media_response.headers['cache-control'].startswith('private, no-store')
    finally:
        media.unlink(missing_ok=True)


def test_panoramic_target_permission_is_independent_from_patients_and_agenda(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste); media = _media_file()
    try:
        analysis = _analysis(db, patient, image_path=f'api/static/uploads/panoramic/{media.name}')
        operator = _user(db, email='m4b-pano@cabinet.ma', employer_id=dentiste.id, permissions={'panoramic': True, 'patients': False, 'agenda': False})
        owner_headers = _auth(client, dentiste)
        issued = _issue(client, owner_headers, analysis.id, operator.id)
        assert issued.status_code == 200, issued.text
        assert issued.json()['target_user_id'] == operator.id
    finally:
        media.unlink(missing_ok=True)


def test_panoramic_permission_revocation_fails_closed(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste); media = _media_file()
    try:
        analysis = _analysis(db, patient, image_path=f'api/static/uploads/panoramic/{media.name}')
        operator = _user(db, email='m4b-revoke@cabinet.ma', employer_id=dentiste.id, permissions={'panoramic': True})
        issued = _issue(client, _auth(client, dentiste), analysis.id, operator.id); assert issued.status_code == 200
        pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
        claimed = _claim(client, pairing.token); assert claimed.status_code == 200
        headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
        operator.permissions = {'panoramic': False}; db.commit()
        destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
        assert destination.status_code == 200; assert destination.json()['context']['state'] == 'unavailable'; assert destination.json()['destination'] != 'agenda'
        denied = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
        assert denied.status_code == 403
    finally:
        media.unlink(missing_ok=True)


def test_deleted_or_cross_tenant_panoramic_is_not_resolved(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    other = _user(db, email='m4b-other@cabinet.ma'); other_patient = _patient(db, other, dossier='OTHER-M4B')
    other_analysis = _analysis(db, other_patient, image_path='api/static/uploads/panoramic/other.jpg')
    denied = _issue(client, auth_headers, other_analysis.id)
    assert denied.status_code in (403, 404)

    patient = _patient(db, dentiste, dossier='OWN-M4B'); media = _media_file()
    try:
        analysis = _analysis(db, patient, image_path=f'api/static/uploads/panoramic/{media.name}')
        issued = _issue(client, auth_headers, analysis.id); assert issued.status_code == 200
        pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first(); claimed = _claim(client, pairing.token); assert claimed.status_code == 200
        headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
        db.delete(analysis); db.commit()
        destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
        assert destination.status_code == 200; assert destination.json()['context']['state'] == 'unavailable'
        missing = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
        assert missing.status_code == 404
    finally:
        media.unlink(missing_ok=True)
