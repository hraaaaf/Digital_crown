from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.routers import mobile_patient_cockpit as cockpit


def _session():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    models.User.__table__.create(engine)
    models.Patient.__table__.create(engine)
    models.Appointment.__table__.create(engine)
    return sessionmaker(bind=engine)()


def _user(user_id: int, email: str):
    return models.User(
        id=user_id,
        email=email,
        hashed_password='test',
        role=models.UserRole.DENTISTE,
        is_active=True,
        employer_id=None,
        permissions={},
    )


def _patient(patient_id: int, employer_id: int, name: str):
    return models.Patient(
        id=patient_id,
        numero_dossier=f'P-{patient_id:04d}',
        nom=name,
        prenom='Patient',
        date_naissance=datetime(1990, 1, 1),
        sexe='M',
        employer_id=employer_id,
        telephone=f'+21260000{patient_id:04d}',
        antecedents_medicaux=None,
    )


def test_search_is_tenant_scoped(monkeypatch):
    db = _session()
    owner_a = _user(1, 'a@example.test')
    owner_b = _user(2, 'b@example.test')
    db.add_all([owner_a, owner_b, _patient(101, 1, 'Alpha'), _patient(202, 2, 'Beta')])
    db.commit()

    monkeypatch.setattr(cockpit, 'encrypt_payload', lambda payload: payload)
    result = cockpit.search_mobile_patient_cockpit(q='', db=db, mobile_user=owner_a)

    assert [patient['id'] for patient in result['patients']] == [101]


def test_cross_tenant_patient_detail_fails_closed():
    db = _session()
    db.add_all([_user(1, 'a@example.test'), _user(2, 'b@example.test'), _patient(202, 2, 'Beta')])
    db.commit()

    with pytest.raises(HTTPException) as failure:
        cockpit._patient_or_404(db, employer_id=1, patient_id=202)

    assert failure.value.status_code == 404


def test_finance_is_omitted_without_financial_permission(monkeypatch):
    db = _session()
    owner = _user(1, 'a@example.test')
    patient = _patient(101, 1, 'Alpha')
    db.add_all([owner, patient])
    db.commit()

    monkeypatch.setattr(cockpit, 'encrypt_payload', lambda payload: payload)
    monkeypatch.setattr(cockpit, 'has_permission', lambda _user, _permission: False)

    result = cockpit.get_mobile_patient_cockpit(patient_id=101, db=db, mobile_user=owner)
    assert result['patient']['id'] == 101
    assert result['finance'] is None


def test_finance_is_returned_only_when_permission_allows_it(monkeypatch):
    db = _session()
    owner = _user(1, 'a@example.test')
    patient = _patient(101, 1, 'Alpha')
    db.add_all([owner, patient])
    db.commit()

    monkeypatch.setattr(cockpit, 'encrypt_payload', lambda payload: payload)
    monkeypatch.setattr(cockpit, 'has_permission', lambda _user, _permission: True)
    monkeypatch.setattr(
        cockpit,
        'get_patient_financial_snapshot_p6',
        lambda _patient_id, _db, _user: {
            'has_billing_data': True,
            'remaining_due': 1250.0,
            'total_collected': 4100.0,
            'overdue_count': 1,
        },
    )

    result = cockpit.get_mobile_patient_cockpit(patient_id=101, db=db, mobile_user=owner)
    assert result['finance'] == {
        'has_billing_data': True,
        'remaining_due': 1250.0,
        'total_collected': 4100.0,
        'overdue_count': 1,
    }


class _FakeQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.value


class _FakeContextDb:
    def __init__(self):
        self.config = SimpleNamespace(public_id='CAB-TEST')
        self.executed = []
        self.added = []
        self.committed = False

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self.config)

    def add(self, record):
        record.id = 9001
        self.added.append(record)

    def flush(self):
        return None

    def execute(self, statement):
        self.executed.append(statement)
        return None

    def commit(self):
        self.committed = True


def _patch_context_dependencies(monkeypatch, mobile_payload):
    mobile_user = SimpleNamespace(id=7, get_employer_id=lambda: 55)
    patient = SimpleNamespace(id=101)
    monkeypatch.setattr(cockpit._legacy, '_decode_mobile_identity', lambda _authorization, _db: (mobile_user, 55, mobile_payload))
    monkeypatch.setattr(cockpit, 'has_permission', lambda _user, _permission: True)
    monkeypatch.setattr(cockpit, '_patient_or_404', lambda _db, _employer_id, _patient_id: patient)
    monkeypatch.setattr(cockpit, '_resource_entity', lambda _db, _user, _resource_type, _resource_id: patient)
    monkeypatch.setattr(cockpit, '_purge_expired', lambda _db, _employer_id, _now: None)
    monkeypatch.setattr(cockpit, '_unique_manual_code', lambda _db, _now: '123456')
    monkeypatch.setattr(cockpit, '_resource_token', lambda: 'opaque-resource-token')
    monkeypatch.setattr(cockpit, '_role_name', lambda _user: 'DENTISTE')
    monkeypatch.setattr(cockpit.os, 'getenv', lambda _name: 'test-key-material')
    monkeypatch.setattr(cockpit.secrets, 'token_urlsafe', lambda _size: 'opaque-context-key')
    monkeypatch.setattr(cockpit.models, 'ZKAPairingToken', lambda **kwargs: SimpleNamespace(**kwargs))
    return mobile_user


def test_patient_context_is_device_bound_and_public_response_is_opaque(monkeypatch):
    db = _FakeContextDb()
    _patch_context_dependencies(monkeypatch, {'device_id': 'device-abc'})

    result = cockpit.create_mobile_patient_cockpit_context(
        patient_id=101,
        body=cockpit.PatientCockpitContextRequest(resource_type='patient'),
        authorization='test-authorization',
        db=db,
    )

    assert result == {
        'context': {'type': 'patient', 'key': 'opaque-context-key', 'state': 'ready'},
        'resource_label': 'Dossier patient',
        'expires_in': 1800,
        'contains_patient_data': False,
        'contains_resource_data': False,
    }
    assert 'patient_id' not in result
    assert 'resource_id' not in result
    assert db.committed is True
    assert len(db.executed) == 1
    params = db.executed[0].compile().params
    assert params['employer_id'] == 55
    assert params['target_user_id'] == 7
    assert params['device_id'] == 'device-abc'
    assert params['resource_type'] == 'patient'
    assert params['resource_id'] == 101


def test_patient_context_rejects_session_without_device_binding(monkeypatch):
    db = _FakeContextDb()
    _patch_context_dependencies(monkeypatch, {})

    with pytest.raises(HTTPException) as failure:
        cockpit.create_mobile_patient_cockpit_context(
            patient_id=101,
            body=cockpit.PatientCockpitContextRequest(resource_type='patient'),
            authorization='test-authorization',
            db=db,
        )

    assert failure.value.status_code == 401
    assert db.committed is False
