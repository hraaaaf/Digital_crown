from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from PIL import Image

from backend import models
from backend.routers import mobile_pairing_secure, mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.services import archive_service
from backend.tests.test_mobile_m6a_clinical_photo import (
    _auth,
    _cabinet,
    _client_public_key,
    _jpeg_bytes,
    _mobile_patient_context,
    _patient,
    _user,
)


@pytest.fixture(autouse=True)
def _isolate_mobile_scan_runtime(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    async def _signed_entitlement(*_args, **_kwargs):
        return {
            'active': True,
            'license_type': 'PAID',
            'max_devices': 10,
            'release_channel': 'stable',
        }

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm6b-rate-limit.json'))
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', tmp_path / 'archives')
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(
        mobile_pairing_secure.LicenseService,
        'get_effective_license',
        _signed_entitlement,
    )
    yield
    _license_cache.clear()


def _scan(client, access, context_key, pages):
    files = [
        ('pages', (filename, content, content_type))
        for filename, content, content_type in pages
    ]
    return client.post(
        '/api/mobile/resource-context-document-scan',
        data={'context_key': context_key},
        files=files,
        headers={'Authorization': f'Bearer {access}'},
    )


def _setup(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste, dossier='M6B-001')
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)
    return patient, access, context_key


def test_mobile_document_scan_archives_one_exact_patient_pdf(client, db, dentiste, auth_headers, monkeypatch):
    patient, access, context_key = _setup(client, db, dentiste, auth_headers, monkeypatch)
    response = _scan(client, access, context_key, [
        ('../../page-1.php.jpg', _jpeg_bytes(with_exif=True), 'image/jpeg'),
        ('page-2.jpg', _jpeg_bytes(), 'image/jpeg'),
    ])
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['success'] is True
    assert payload['pages'] == 2
    assert payload['document']['document_type'] == 'AUTRE'
    assert 'patient_id' not in payload
    assert 'file_path' not in payload['document']

    documents = db.query(models.DocumentArchive).all()
    assert len(documents) == 1
    document = documents[0]
    assert document.patient_id == patient.id
    assert document.document_type == models.DocumentType.AUTRE
    assert document.uploaded_by_id == dentiste.id
    assert document.title == 'Document scanné'
    assert document.original_filename.startswith('document-scanne-')
    assert document.original_filename.endswith('.pdf')
    assert '..' not in document.original_filename
    assert 'page-1' not in document.original_filename

    relative = document.file_path.replace('static/archives/', '', 1)
    stored = Path(archive_service.ARCHIVE_BASE_DIR) / relative
    assert stored.is_file()
    assert archive_service.ARCHIVE_BASE_DIR.resolve() in stored.resolve().parents
    pdf = fitz.open(stream=stored.read_bytes(), filetype='pdf')
    try:
        assert pdf.page_count == 2
    finally:
        pdf.close()


def test_mobile_document_scan_rejects_bad_content_mime_and_limits(client, db, dentiste, auth_headers, monkeypatch):
    _patient_row, access, context_key = _setup(client, db, dentiste, auth_headers, monkeypatch)

    invalid = _scan(client, access, context_key, [('fake.jpg', b'not-an-image', 'image/jpeg')])
    assert invalid.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    wrong_mime = _scan(client, access, context_key, [('page.pdf', _jpeg_bytes(), 'application/pdf')])
    assert wrong_mime.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    too_many = _scan(client, access, context_key, [
        (f'page-{index}.jpg', _jpeg_bytes(), 'image/jpeg') for index in range(9)
    ])
    assert too_many.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0

    page = _jpeg_bytes()
    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_TOTAL_BYTES', len(page) + 8)
    aggregate = _scan(client, access, context_key, [
        ('one.jpg', page, 'image/jpeg'),
        ('two.jpg', page, 'image/jpeg'),
    ])
    assert aggregate.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0

    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_TOTAL_BYTES', 48 * 1024 * 1024)
    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_PIXELS', 100)
    pixels = _scan(client, access, context_key, [('pixels.jpg', page, 'image/jpeg')])
    assert pixels.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_document_scan_revalidates_permission_and_deleted_patient(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m6b-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'patients': True, 'agenda': True},
    )
    patient = _patient(db, dentiste, dossier='M6B-REVOKE')
    owner_headers = _auth(client, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, owner_headers, target_user_id=secretary.id)

    secretary.permissions = {'patients': False, 'agenda': True}
    db.commit()
    denied = _scan(client, access, context_key, [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert denied.status_code == 403
    assert db.query(models.DocumentArchive).count() == 0

    secretary.permissions = {'patients': True, 'agenda': True}
    patient.deleted_at = datetime.utcnow()
    db.commit()
    deleted = _scan(client, access, context_key, [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert deleted.status_code == 404
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_document_scan_rejects_cross_tenant_and_non_patient_context(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)

    other_owner = _user(db, email='m6b-other@cabinet.ma')
    other_patient = _patient(db, other_owner, dossier='M6B-OTHER')
    cross = client.post('/api/mobile/resource-bridge-pairing', json={
        'resource_type': 'patient', 'resource_id': other_patient.id,
    }, headers=auth_headers)
    assert cross.status_code == 404

    patient = _patient(db, dentiste, dossier='M6B-LOCAL')
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
        'resource_type': 'appointment', 'resource_id': appointment.id,
    }, headers=auth_headers)
    assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token, 'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200
    appointment_access = claimed.json()['access_token']
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers={'Authorization': f'Bearer {appointment_access}'})
    assert destination.status_code == 200
    wrong = _scan(client, appointment_access, destination.json()['context']['key'], [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert wrong.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0
