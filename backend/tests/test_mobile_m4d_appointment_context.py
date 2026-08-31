from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

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
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4d-rate-limit.json'))
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
    user = models.User(email=email, hashed_password=get_password_hash('TestPass123!'), role=role, nom_complet='M4D User', is_active=True, is_licensed=True, license_expires_at=datetime.utcnow() + timedelta(days=30), employer_id=employer_id, permissions=permissions or {}, approval_status='approved')
    db.add(user); db.commit(); db.refresh(user); return user


def _patient(db, owner, *, dossier='M4D-0042'):
    patient = models.Patient(numero_dossier=dossier, nom='BENNANI', prenom='Sara', date_naissance=datetime(1992, 5, 18), sexe='F', employer_id=owner.id, telephone='0612345678')
    db.add(patient); db.commit(); db.refresh(patient); return patient


def _appointment(db, owner, patient=None):
    appt = models.Appointment(patient_id=patient.id if patient else None, patient_name='BENNANI Sara' if patient else 'Visiteur externe', datetime_start=datetime(2026, 8, 25, 10, 30), duration_minutes=60, motif='Contrôle implant 36', status=models.AppointmentStatus.CONFIRME, scheduling_type=models.SchedulingType.EXACT_TIME, notes='RDV M4-D exact', employer_id=owner.id)
    db.add(appt); db.commit(); db.refresh(appt); return appt


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg); db.commit(); db.refresh(cfg); return cfg


def _auth(client, user):
    response = client.post('/api/auth/login', data={'username': user.email, 'password': 'TestPass123!'})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(encoding=serialization.Encoding.X962, format=serialization.PublicFormat.UncompressedPoint).hex()


def _claim(client, credential):
    return client.post('/api/mobile/claim-token', json={'token': credential, 'client_public_key_hex': _client_public_key()})


def _issue(client, headers, appointment_id, target_user_id=None):
    payload = {'resource_type': 'appointment', 'resource_id': appointment_id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    return client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=headers)


def test_appointment_bridge_full_protocol_and_qr_are_opaque(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.nom_complet = 'Dr M4D'; dentiste.is_licensed = True; dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste); db.commit(); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    appointment = _appointment(db, dentiste, patient)

    captured_qr = {}
    def _capture(payload, **_kwargs):
        captured_qr['payload'] = payload
        return BytesIO(b'm4d-qr')
    monkeypatch.setattr(mobile_resource_bridge._admin_legacy.QRService, 'generate_qr_bytes', staticmethod(_capture))

    options = client.get(f'/api/mobile/resource-bridge-options?resource_type=appointment&resource_id={appointment.id}', headers=auth_headers)
    assert options.status_code == 200, options.text
    assert options.json()['resource_type'] == 'appointment'
    assert options.json()['resource_label'] == 'Rendez-vous'
    assert options.json()['contains_patient_data'] is False
    assert options.json()['contains_resource_data'] is False

    issued = _issue(client, auth_headers, appointment.id)
    assert issued.status_code == 200, issued.text
    assert issued.json()['contains_patient_data'] is False
    assert issued.json()['contains_resource_data'] is False
    assert 'appointment_id' not in issued.json()
    assert 'patient_id' not in issued.json()

    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    parsed = urlsplit(captured_qr['payload'])
    query = parse_qs(parsed.query, strict_parsing=True)
    assert parsed.path == '/mobile/onboarding'
    assert set(query) == {'token'}
    assert query['token'] == [pairing.token]
    lowered = captured_qr['payload'].lower()
    for forbidden in ('appointment_id=', 'resource_id=', 'patient_id=', 'bennani', 'implant', '10:30'):
        assert forbidden not in lowered

    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    mobile_headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=mobile_headers)
    assert destination.status_code == 200, destination.text
    resolved = destination.json()
    assert resolved['destination'] == 'context'
    assert resolved['fallback'] is False
    assert resolved['context']['type'] == 'appointment'
    assert resolved['context']['state'] == 'ready'

    context = client.post('/api/mobile/resource-context', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
    assert context.status_code == 200, context.text
    data = context.json()
    assert data['type'] == 'appointment'
    assert data['appointment']['patient_name'] == 'BENNANI Sara'
    assert data['appointment']['datetime_start'].startswith('2026-08-25T10:30')
    assert data['appointment']['duration_minutes'] == 60
    assert data['appointment']['motif'] == 'Contrôle implant 36'
    assert data['appointment']['status'] == models.AppointmentStatus.CONFIRME.value
    assert data['appointment']['scheduling_type'] == models.SchedulingType.EXACT_TIME.value
    assert 'id' not in data['appointment']
    assert 'patient_id' not in data['appointment']


def test_appointment_target_requires_agenda_and_revocation_fails_closed(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    appointment = _appointment(db, dentiste, patient)
    allowed = _user(db, email='m4d-agenda@cabinet.ma', employer_id=dentiste.id, permissions={'agenda': True, 'patients': False})
    denied = _user(db, email='m4d-noagenda@cabinet.ma', employer_id=dentiste.id, permissions={'agenda': False, 'patients': True})
    owner_headers = _auth(client, dentiste)

    denied_issue = _issue(client, owner_headers, appointment.id, denied.id)
    assert denied_issue.status_code == 403
    issued = _issue(client, owner_headers, appointment.id, allowed.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}

    allowed.permissions = {'agenda': False, 'patients': False}; db.commit()
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200
    assert destination.json()['context']['state'] == 'unavailable'
    refused = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert refused.status_code == 403


def test_appointment_deleted_and_cross_tenant_are_denied(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    other = _user(db, email='m4d-other@cabinet.ma')
    other_patient = _patient(db, other, dossier='OTHER-M4D')
    other_appt = _appointment(db, other, other_patient)
    denied = _issue(client, auth_headers, other_appt.id)
    assert denied.status_code in (403, 404)

    patient = _patient(db, dentiste, dossier='OWN-M4D')
    appointment = _appointment(db, dentiste, patient)
    issued = _issue(client, auth_headers, appointment.id); assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200
    db.delete(appointment); db.commit()
    missing = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert missing.status_code == 404
