from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from PIL import Image

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.security import get_password_hash
from backend.services import archive_service


@pytest.fixture(autouse=True)
def _isolate_mobile_photo_runtime(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm6a-rate-limit.json'))
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', tmp_path / 'archives')
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', tmp_path)
    yield
    _license_cache.clear()


def _user(db, *, email, role=models.UserRole.DENTISTE, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='M6A User',
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


def _patient(db, owner, *, dossier='M6A-001'):
    patient = models.Patient(
        numero_dossier=dossier,
        nom='BENNANI',
        prenom='Sara',
        date_naissance=datetime(1992, 5, 18),
        sexe='F',
        employer_id=owner.id,
        telephone='0612345678',
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg)
    db.commit()
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


def _mobile_patient_context(client, db, owner, patient, owner_headers, *, target_user_id=None):
    payload = {'resource_type': 'patient', 'resource_id': patient.id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    issued = client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=owner_headers)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token,
        'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']
    destination = client.post(
        '/api/mobile/resource-bridge-destination',
        json={'credential': pairing.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert destination.status_code == 200, destination.text
    return access, destination.json()['context']['key']


def _jpeg_bytes(*, with_exif=False):
    image = Image.new('RGB', (96, 64), color=(205, 225, 240))
    output = BytesIO()
    if with_exif:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = 'metadata-to-strip'
        image.save(output, format='JPEG', quality=95, exif=exif)
    else:
        image.save(output, format='JPEG', quality=95)
    return output.getvalue()


def _upload(client, access, context_key, content, *, filename='chairside.jpg', content_type='image/jpeg'):
    return client.post(
        '/api/mobile/resource-context-photo',
        data={'context_key': context_key},
        files={'file': (filename, content, content_type)},
        headers={'Authorization': f'Bearer {access}'},
    )


def test_mobile_clinical_photo_archives_exact_patient_and_strips_metadata(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    response = _upload(client, access, context_key, _jpeg_bytes(with_exif=True), filename='../../evil.php.jpg')
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['success'] is True
    assert payload['document']['document_type'] == 'PHOTO_CLINIQUE'
    assert 'patient_id' not in payload
    assert 'file_path' not in payload['document']

    document = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == payload['document']['id']).one()
    assert document.patient_id == patient.id
    assert document.document_type == models.DocumentType.PHOTO_CLINIQUE
    assert document.uploaded_by_id == dentiste.id
    assert document.original_filename.startswith('photo-clinique-')
    assert document.original_filename.endswith('.jpg')
    assert '..' not in document.original_filename
    assert 'evil' not in document.original_filename

    relative = document.file_path.replace('static/archives/', '', 1)
    stored = Path(archive_service.ARCHIVE_BASE_DIR) / relative
    assert stored.is_file()
    assert archive_service.ARCHIVE_BASE_DIR.resolve() in stored.resolve().parents
    with Image.open(stored) as normalized:
        assert normalized.format == 'JPEG'
        assert normalized.getexif().get(274) is None
        assert normalized.getexif().get(270) is None


def test_mobile_clinical_photo_rejects_invalid_and_oversized_files(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    invalid = _upload(client, access, context_key, b'not-an-image', filename='fake.jpg')
    assert invalid.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    oversized = _upload(client, access, context_key, b'x' * (12 * 1024 * 1024 + 1), filename='large.jpg')
    assert oversized.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_clinical_photo_revalidates_permission_at_upload_time(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m6a-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'patients': True, 'agenda': True},
    )
    patient = _patient(db, dentiste)
    owner_headers = _auth(client, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, owner_headers, target_user_id=secretary.id)

    secretary.permissions = {'patients': False, 'agenda': True}
    db.commit()
    denied = _upload(client, access, context_key, _jpeg_bytes())
    assert denied.status_code == 403
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_clinical_photo_rejects_deleted_patient_and_non_patient_context(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    patient.deleted_at = datetime.utcnow()
    db.commit()
    deleted = _upload(client, access, context_key, _jpeg_bytes())
    assert deleted.status_code == 404
    assert db.query(models.DocumentArchive).count() == 0

    patient.deleted_at = None
    db.commit()
    appointment = models.Appointment(
        patient_id=patient.id,
        patient_name='BENNANI Sara',
        datetime_start=datetime.utcnow() + timedelta(hours=1),
        duration_minutes=30,
        employer_id=dentiste.id,
    )
    db.add(appointment)
    db.commit()
    issued = client.post('/api/mobile/resource-bridge-pairing', json={
        'resource_type': 'appointment',
        'resource_id': appointment.id,
    }, headers=auth_headers)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token,
        'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200
    appointment_access = claimed.json()['access_token']
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers={'Authorization': f'Bearer {appointment_access}'})
    assert destination.status_code == 200
    wrong = _upload(client, appointment_access, destination.json()['context']['key'], _jpeg_bytes())
    assert wrong.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0
