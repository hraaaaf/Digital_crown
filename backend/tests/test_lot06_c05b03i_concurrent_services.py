"""C05B-03I: actual PC02/PC08 services, independent file-backed SQLite sessions.
Synthetic identities, no HTTP, Tailnet, SQLCipher, device, patient data, or clinical ACK.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from time import monotonic
import os
import uuid

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionMessage,
)
from backend.services.patient_companion_agenda import create_appointment, issue_slots
from backend.services.patient_companion_messages import handle_message_send, handle_message_sync


@pytest.fixture()
def synthetic_cabinet(tmp_path):
    assert os.environ.get('ENVIRONMENT') == 'test'
    assert os.environ.get('DIGITALCROWN_ISOLATED_RUNTIME') == 'true'
    assert os.environ.get('C05B03H_NETWORK_POLICY_APPROVED') == 'false'
    engine = create_engine(
        'sqlite:///' + str(tmp_path / 'lot06-c05b03i-stress.sqlite'),
        poolclass=NullPool,
        connect_args={'timeout': 15, 'check_same_thread': False},
    )

    @event.listens_for(engine, 'connect')
    def _configure(connection, _record):
        connection.execute('PRAGMA busy_timeout=15000')
        connection.execute('PRAGMA foreign_keys=ON')

    with engine.connect() as conn:
        assert conn.exec_driver_sql('PRAGMA journal_mode=WAL').scalar().lower() == 'wal'
    # The schema is taken from the real ORM; NO production database is opened.
    models.Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        doctor = models.User(
            email='lot06-c05b03i-stress@example.invalid',
            hashed_password='test-only-disabled-login', role='DENTISTE',
            nom_complet='Practitioner Test', is_active=True, is_licensed=True,
        )
        db.add(doctor)
        db.flush()
        employer_id = doctor.id
        access_ids, patient_ids = [], []
        for label in ('A', 'B'):
            patient = models.Patient(
                numero_dossier='STRESS-' + label + '-' + uuid.uuid4().hex[:8],
                nom='Synthetic', prenom=label,
                date_naissance=datetime(2010, 1, 1), sexe='F',
                employer_id=employer_id,
            )
            identity = PatientCompanionIdentity(
                provider='local_bridge', subject='stress:' + label + ':' + uuid.uuid4().hex,
            )
            db.add_all([patient, identity])
            db.flush()
            access = PatientCompanionAccess(
                identity_id=identity.id, employer_id=employer_id,
                patient_id=patient.id, relationship_type='SELF',
            )
            db.add(access)
            db.flush()
            access_ids.append(access.id)
            patient_ids.append(patient.id)
        db.commit()
    try:
        yield engine, employer_id, tuple(access_ids), tuple(patient_ids)
    finally:
        engine.dispose()


def p95_ms(values):
    rows = sorted(values)
    return round(rows[max(0, (len(rows) * 95 + 99) // 100 - 1)], 2)


def test_actual_pc02_independent_sessions_race(synthetic_cabinet):
    engine, employer_id, access_ids, patient_ids = synthetic_cabinet
    latency = []
    for round_no in range(16):
        start = datetime(2030, 1, 2, 10) + timedelta(days=round_no)
        with Session(engine) as db:
            refs = []
            for access_id in access_ids:
                access = db.get(PatientCompanionAccess, access_id)
                issued = issue_slots(db, access=access, starts=[start],
                                     duration_minutes=30, practitioner_id=employer_id)
                assert len(issued) == 1
                refs.append(issued[0]['slot_ref'])
            db.commit()
        barrier = Barrier(2)

        def book(index):
            with Session(engine, expire_on_commit=False) as db:
                access = db.get(PatientCompanionAccess, access_ids[index])
                assert access.patient_id == patient_ids[index]
                barrier.wait(timeout=12)
                t0 = monotonic()
                result = create_appointment(db, access, {'slot_ref': refs[index]})
                if result.status == 'ACCEPTED':
                    db.commit()
                else:
                    db.rollback()
                return result.status, result.response.get('code'), (monotonic() - t0) * 1000

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(book, index) for index in (0, 1)]
            results = [future.result(timeout=24) for future in futures]
        assert sorted(row[0] for row in results) == ['ACCEPTED', 'REJECTED'], (round_no, results)
        refused = next(row for row in results if row[0] == 'REJECTED')
        assert refused[1] in ('SLOT_CONFLICT', 'SLOT_UNAVAILABLE', 'SLOT_NOT_FOUND')
        latency.extend(row[2] for row in results)
        with Session(engine) as db:
            rows = db.query(models.Appointment).filter(
                models.Appointment.employer_id == employer_id,
                models.Appointment.praticien_id == employer_id,
                models.Appointment.datetime_start == start,
            ).all()
            assert len(rows) == 1, (round_no, len(rows))
            assert rows[0].patient_id in patient_ids
    assert len(latency) == 32
    print('C05B03I_PC02_REAL_SERVICE_16_SQLITE_RACES_PASS',
          {'latency_samples': len(latency), 'observed_p95_ms': p95_ms(latency),
           'distinct_connections': True, 'http_tested': False})


def test_actual_pc08_parallel_messages_and_dentist_read(synthetic_cabinet):
    engine, employer_id, access_ids, patient_ids = synthetic_cabinet
    latency = []
    for round_no in range(16):
        barrier = Barrier(3)
        client_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        def send(index):
            with Session(engine, expire_on_commit=False) as db:
                access = db.get(PatientCompanionAccess, access_ids[index])
                barrier.wait(timeout=12)
                t0 = monotonic()
                result = handle_message_send(db, access, {
                    'client_message_id': client_ids[index],
                    'body': f'R{round_no} synthetic message for {index}',
                })
                if result.status == 'ACCEPTED':
                    db.commit()
                else:
                    db.rollback()
                return result.status, (monotonic() - t0) * 1000

        def dentist_read():
            with Session(engine) as db:
                barrier.wait(timeout=12)
                assert db.execute(select(func.count(models.Patient.id)).where(
                    models.Patient.employer_id == employer_id,
                )).scalar_one() == 2
                return True

        with ThreadPoolExecutor(max_workers=3) as pool:
            fa, fb, fc = pool.submit(send, 0), pool.submit(send, 1), pool.submit(dentist_read)
            results = [fa.result(timeout=24), fb.result(timeout=24)]
            assert fc.result(timeout=24)
        assert all(state == 'ACCEPTED' for state, _ in results), (round_no, results)
        latency.extend(ms for _, ms in results)
        with Session(engine) as db:
            for index in (0, 1):
                access = db.get(PatientCompanionAccess, access_ids[index])
                messages = handle_message_sync(db, access, {}).response['items']
                assert len(messages) == round_no + 1
                assert all(f'for {index}' in message['body'] for message in messages)
                assert db.query(PatientCompanionMessage).filter(
                    PatientCompanionMessage.access_id == access.id,
                    PatientCompanionMessage.client_message_id == client_ids[index],
                ).count() == 1
    assert len(latency) == 32
    print('C05B03I_PC08_REAL_SERVICE_PARALLEL_ISOLATION_PASS',
          {'latency_samples': len(latency), 'observed_p95_ms': p95_ms(latency),
           'distinct_connections': True, 'http_tested': False})
