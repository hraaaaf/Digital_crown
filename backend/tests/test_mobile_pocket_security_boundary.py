from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers.mobile import _create_bridge_token
from backend.security import get_password_hash
from backend.utils import rate_limit


@pytest.fixture(autouse=True)
def _reset_pairing_rate_limit():
    path = Path(rate_limit._store_path())
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
        path.unlink(missing_ok=True)
    yield
    with rate_limit._lock:
        rate_limit._attempts.clear()
        rate_limit._loaded = False
        path.unlink(missing_ok=True)


def _user(db, *, email, role, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='Pocket Boundary User',
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


def _claim_mobile(client, db, owner, user):
    owner.is_licensed = True
    owner.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(owner)
    db.commit()

    record = models.ZKAPairingToken(
        token=_create_bridge_token('agenda'),
        manual_code='765432',
        employer_id=owner.id,
        user_id=user.id,
        public_id='abcdef1234567890',
        master_key='a' * 64,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()

    response = client.post('/api/mobile/claim-token', json={
        'token': record.token,
        'client_public_key_hex': _client_public_key(),
    })
    assert response.status_code == 200, response.text
    return response.json()['access_token']


def test_mobile_jwt_cannot_authenticate_generic_desktop_or_financial_apis(client, db, dentiste):
    secretary = _user(
        db,
        email='pocket-finance-boundary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={
            'agenda': True,
            'patients': True,
            'accounting': True,
            'payments': True,
            'clinical': False,
        },
    )
    access = _claim_mobile(client, db, dentiste, secretary)
    headers = {'Authorization': f'Bearer {access}'}

    assert client.get('/api/auth/me', headers=headers).status_code == 401
    assert client.get('/api/patients/', headers=headers).status_code == 401
    assert client.post(
        '/api/accounting/payments',
        headers=headers,
        json={'patient_id': 999, 'amount': 10, 'payment_method': 'ESPECES'},
    ).status_code == 401

    # The same paired token remains valid on its explicitly scoped mobile API.
    assert client.get('/api/mobile/patients', headers=headers).status_code == 200


def test_secretary_patient_access_does_not_grant_clinical_context(client, db, dentiste):
    secretary = _user(
        db,
        email='pocket-secretary-clinical-boundary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={
            'agenda': True,
            'patients': True,
            'accounting': False,
            'payments': False,
            'clinical': False,
        },
    )
    patient = models.Patient(
        nom='BOUNDARY',
        prenom='Patient',
        date_naissance=datetime(1990, 1, 1),
        sexe='F',
        employer_id=dentiste.id,
        telephone='+212600000000',
        antecedents_medicaux='Allergie pénicilline',
        motif_consultation='Douleur aiguë',
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    access = _claim_mobile(client, db, dentiste, secretary)
    headers = {'Authorization': f'Bearer {access}'}

    # Operational patient access remains available.
    assert client.get(f'/api/mobile/patient-cockpit/{patient.id}', headers=headers).status_code == 200

    # Clinical context creation is server-denied even though patients=True.
    response = client.post(
        f'/api/mobile/patient-cockpit/{patient.id}/context',
        headers=headers,
        json={'resource_type': 'patient'},
    )
    assert response.status_code == 403
    assert 'clinique' in response.json()['detail'].lower()


def test_pocket_v1_facades_preserve_mobile_scope_and_role_guards(client, db, dentiste):
    secretary = _user(
        db,
        email='pocket-v1-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'agenda': True, 'patients': True, 'accounting': False, 'payments': False},
    )
    access = _claim_mobile(client, db, dentiste, secretary)
    headers = {'Authorization': f'Bearer {access}'}

    # Stock is operational for the secretary through the explicit Pocket facade.
    assert client.get('/api/mobile/stock/items', headers=headers).status_code == 200

    # Practitioner-only secondary modules fail closed even by direct deep-link/API call.
    assert client.get('/api/mobile/lab-jobs', headers=headers).status_code == 403
    assert client.get('/api/mobile/partner-catalog/meta', headers=headers).status_code == 403
    assert client.get('/api/mobile/partner-orders/meta', headers=headers).status_code == 403

    # The paired JWT never becomes a generic desktop/API session.
    assert client.get('/api/stock/items', headers=headers).status_code == 401
    assert client.get('/api/lab-jobs/', headers=headers).status_code == 401
    assert client.get('/api/partner-catalog/meta', headers=headers).status_code == 401
