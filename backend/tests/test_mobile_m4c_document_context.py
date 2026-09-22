from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.security import get_password_hash
from backend.services.archive_service import get_archive_service


@pytest.fixture(autouse=True)
def _isolate_mobile_runtime_state(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit
    from backend.services import archive_service
    from backend.routers import documents

    # M4-C exercises a real archived binary. Keep the filesystem side of the
    # test as isolated as the SQLite fixture: every test gets one private media
    # root shared by the archive writer, desktop document router and mobile
    # context resolver. This prevents order-dependent leakage from earlier
    # tests and never touches the runner/user media directory.
    media_root = tmp_path / 'm4c-media'
    archive_root = media_root / 'archives'
    legacy_root = media_root / 'documents'
    archive_root.mkdir(parents=True, exist_ok=True)
    legacy_root.mkdir(parents=True, exist_ok=True)

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', lambda: tmp_path / 'm4c-rate-limit.json')
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', media_root)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', archive_root)
    monkeypatch.setattr(archive_service, 'LEGACY_DOCS_DIR', legacy_root)
    monkeypatch.setattr(documents, 'MEDIA_DIR', media_root)
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', media_root)
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
        nom_complet='M4C User',
        is_active=True,
        is_licensed=True,
        license_expires_at=datetime.utcnow() + timedelta(days=30),
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status='approved',
    )
    db.add(user); db.commit(); db.refresh(user); return user


def _patient(db, owner, *, dossier='M4C-0042'):
    patient = models.Patient(
        numero_dossier=dossier,
        nom='BENNANI', prenom='Sara', date_naissance=datetime(1992, 5, 18), sexe='F',
        employer_id=owner.id, telephone='0612345678', assurance='MUTUELLE',
    )
    db.add(patient); db.commit(); db.refresh(patient); return patient


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg); db.commit(); db.refresh(cfg); return cfg


def _archive(db, patient, owner, *, doc_type=models.DocumentType.ORDONNANCE, filename='Ordonnance_M4C.pdf'):
    service = get_archive_service(db)
    doc, _ = service.archive_document(
        patient_id=patient.id,
        file_content=b'%PDF-1.4\nM4C-DOCUMENT\n%%EOF',
        filename=filename,
        doc_type=doc_type,
        uploaded_by_id=owner.id,
        clinical_data={'items': [{'label': 'M4C'}]},
    )
    return doc


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


def _issue(client, headers, document_id, target_user_id=None):
    payload = {'resource_type': 'document', 'resource_id': document_id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    return client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=headers)


def test_document_bridge_full_protocol_media_and_qr_are_opaque(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.nom_complet = 'Dr M4C'; dentiste.is_licensed = True; dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste); db.commit(); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    document = _archive(db, patient, dentiste)

    captured_qr = {}
    def _capture(payload, **_kwargs):
        captured_qr['payload'] = payload
        return BytesIO(b'm4c-qr')
    monkeypatch.setattr(mobile_resource_bridge._admin_legacy.QRService, 'generate_qr_bytes', staticmethod(_capture))

    options = client.get(f'/api/mobile/resource-bridge-options?resource_type=document&resource_id={document.id}', headers=auth_headers)
    assert options.status_code == 200, options.text
    assert options.json()['resource_type'] == 'document'
    assert options.json()['resource_label'] == 'Document'
    assert options.json()['contains_patient_data'] is False
    assert options.json()['contains_resource_data'] is False

    issued = _issue(client, auth_headers, document.id)
    assert issued.status_code == 200, issued.text
    assert issued.json()['contains_patient_data'] is False
    assert issued.json()['contains_resource_data'] is False
    assert 'document_id' not in issued.json()
    assert 'file_path' not in issued.json()
