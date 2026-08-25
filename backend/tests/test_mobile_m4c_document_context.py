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
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4c-rate-limit.json'))
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', media_root)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', archive_root)
    monkeypatch.setattr(archive_service, 'LEGACY_DOCS_DIR', legacy_root)
    monkeypatch.setattr(documents, 'MEDIA_DIR', media_root)
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', media_root)
    yield
    _license_cache.clear()


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

    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    parsed = urlsplit(captured_qr['payload'])
    query = parse_qs(parsed.query, strict_parsing=True)
    assert parsed.path == '/mobile/onboarding'
    assert set(query) == {'token'}
    assert query['token'] == [pairing.token]
    lowered = captured_qr['payload'].lower()
    for forbidden in ('document_id=', 'resource_id=', 'patient_id=', 'file_path=', 'ordonnance_m4c.pdf', 'bennani'):
        assert forbidden not in lowered

    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    mobile_headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=mobile_headers)
    assert destination.status_code == 200, destination.text
    resolved = destination.json()
    assert resolved['destination'] == 'context'
    assert resolved['fallback'] is False
    assert resolved['context']['type'] == 'document'
    assert resolved['context']['state'] == 'ready'

    context = client.post('/api/mobile/resource-context', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
    assert context.status_code == 200, context.text
    data = context.json()
    assert data['type'] == 'document'
    assert data['document']['patient_name'] == 'BENNANI Sara'
    assert data['document']['document_type'] == models.DocumentType.ORDONNANCE.value
    assert data['document']['filename'] == 'Ordonnance_M4C.pdf'
    assert 'id' not in data['document']
    assert 'file_path' not in data['document']

    media = client.post('/api/mobile/resource-context-media', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
    assert media.status_code == 200, media.text
    assert media.content.startswith(b'%PDF-1.4\nM4C-DOCUMENT')
    assert media.headers['cache-control'].startswith('private, no-store')


def test_document_target_permission_is_derived_from_real_document_type(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    ordonnance = _archive(db, patient, dentiste, doc_type=models.DocumentType.ORDONNANCE, filename='Rx.pdf')
    devis = _archive(db, patient, dentiste, doc_type=models.DocumentType.DEVIS, filename='Devis.pdf')
    rx_user = _user(db, email='m4c-rx@cabinet.ma', employer_id=dentiste.id, permissions={'prescriptions': True, 'patients': False, 'accounting': False})
    finance_user = _user(db, email='m4c-finance@cabinet.ma', employer_id=dentiste.id, permissions={'accounting': True, 'patients': False, 'prescriptions': False})
    owner_headers = _auth(client, dentiste)

    rx_ok = _issue(client, owner_headers, ordonnance.id, rx_user.id)
    assert rx_ok.status_code == 200, rx_ok.text
    rx_denied = _issue(client, owner_headers, devis.id, rx_user.id)
    assert rx_denied.status_code == 403

    finance_ok = _issue(client, owner_headers, devis.id, finance_user.id)
    assert finance_ok.status_code == 200, finance_ok.text
    finance_denied = _issue(client, owner_headers, ordonnance.id, finance_user.id)
    assert finance_denied.status_code == 403


def test_document_permission_revocation_and_trash_fail_closed(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    document = _archive(db, patient, dentiste)
    operator = _user(db, email='m4c-revoke@cabinet.ma', employer_id=dentiste.id, permissions={'prescriptions': True, 'patients': False})
    issued = _issue(client, _auth(client, dentiste), document.id, operator.id)
    assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}

    operator.permissions = {'prescriptions': False, 'patients': False}; db.commit()
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200
    assert destination.json()['context']['state'] == 'unavailable'
    denied = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert denied.status_code == 403

    operator.permissions = {'prescriptions': True, 'patients': False}; db.commit()
    document.status = models.DocumentStatus.SUPPRIME; db.commit()
    missing = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert missing.status_code == 404


def test_document_cross_tenant_and_missing_file_are_denied(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    other = _user(db, email='m4c-other@cabinet.ma')
    other_patient = _patient(db, other, dossier='OTHER-M4C')
    other_doc = _archive(db, other_patient, other, filename='Other.pdf')
    denied = _issue(client, auth_headers, other_doc.id)
    assert denied.status_code in (403, 404)

    patient = _patient(db, dentiste, dossier='OWN-M4C')
    document = _archive(db, patient, dentiste, filename='Missing.pdf')
    issued = _issue(client, auth_headers, document.id); assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200

    candidate = mobile_resource_bridge._document_file(document)
    candidate.unlink(missing_ok=True)
    media = client.post('/api/mobile/resource-context-media', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert media.status_code == 404


def test_document_mutations_use_typed_permission_and_legacy_trash_stays_closed(client, db, dentiste):
    patient = _patient(db, dentiste)
    devis = _archive(db, patient, dentiste, doc_type=models.DocumentType.DEVIS, filename='Mutation-Devis.pdf')
    patients_only = _user(db, email='m4c-patients-only@cabinet.ma', employer_id=dentiste.id, permissions={'patients': True, 'accounting': False})
    accounting_only = _user(db, email='m4c-accounting-only@cabinet.ma', employer_id=dentiste.id, permissions={'patients': False, 'accounting': True})

    denied = client.post(f'/api/documents/{devis.id}/trash', headers=_auth(client, patients_only))
    assert denied.status_code == 403
    trashed = client.post(f'/api/documents/{devis.id}/trash', headers=_auth(client, accounting_only))
    assert trashed.status_code == 200, trashed.text

    restore_denied = client.post(f'/api/documents/{devis.id}/restore', headers=_auth(client, patients_only))
    assert restore_denied.status_code == 403
    restored = client.post(f'/api/documents/{devis.id}/restore', headers=_auth(client, accounting_only))
    assert restored.status_code == 200, restored.text

    legacy = client.post(f'/api/documents/legacy:{patient.id}:ancien.pdf/trash', headers=_auth(client, patients_only))
    assert legacy.status_code == 400

    delete_denied = client.delete(f'/api/documents/{devis.id}?confirm=true', headers=_auth(client, patients_only))
    assert delete_denied.status_code == 403
