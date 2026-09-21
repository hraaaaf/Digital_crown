from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from PIL import Image

from backend import models
from backend.routers import mobile_resource_bridge
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

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm6b-rate-limit.json'))
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', tmp_path / 'archives')
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', tmp_path)
    yield
    _license_cache.clear()
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False


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