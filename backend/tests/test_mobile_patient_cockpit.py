from datetime import datetime

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
