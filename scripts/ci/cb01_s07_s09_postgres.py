"""Isolated PostgreSQL S07/S09 primitives, NOT clinical UI or executable Crown Bot."""
from __future__ import annotations
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import check_output
from threading import Event

from sqlalchemy import (BigInteger, Column, DateTime, Integer, MetaData, String,
                        Table, create_engine, inspect, select, update)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
# Load the exact checked-out PRODUCTION modules by file path. Importing the
# backend package itself bootstraps unrelated app schemas/third-party ML deps,
# which are intentionally absent from this narrow DB-only CI job.
from importlib.util import module_from_spec, spec_from_file_location
repo_root = Path(__file__).resolve().parents[2]

def _load_source_module(relative_path, module_name):
    path = repo_root / relative_path
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('REFUSED: production source module missing')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

revision = _load_source_module(
    'backend/core/appointment_revision_ddl.py', 'cb01_prod_revision')
interval = _load_source_module(
    'backend/services/agenda_interval_overlap.py', 'cb01_prod_interval')
transaction = _load_source_module(
    'backend/services/agenda_transaction_lock.py', 'cb01_prod_lock')
install_appointment_overlap_index = revision.install_appointment_overlap_index
install_appointment_revision_guard = revision.install_appointment_revision_guard
exact_half_open_overlap = interval.exact_half_open_overlap
indexed_end_after = interval.indexed_end_after
lock_cabinet_booking = transaction.lock_cabinet_booking

if os.environ.get('DIGITALCROWN_ISOLATED_RUNTIME') != '1':
    raise RuntimeError('REFUSED: isolated runtime required')
if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise RuntimeError('REFUSED: CI-only PostgreSQL lab')
head = os.environ.get('CB01_SOURCE_HEAD', '')
if len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
    raise RuntimeError('REFUSED: exact source SHA missing')
if check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != head:
    raise RuntimeError('REFUSED: source HEAD mismatch')
url = make_url(os.environ.get('CB01_PG_LAB_URL', ''))
if (url.drivername not in ('postgresql', 'postgresql+psycopg2')
    or url.host not in ('localhost', '127.0.0.1') or url.port != 5432
    or url.database != 'cb01_booking_lab' or url.username != 'cb01_ci'):
    raise RuntimeError('REFUSED: exact disposable loopback PostgreSQL only')
engine = create_engine(url, pool_size=3, max_overflow=1, pool_pre_ping=True)
if engine.dialect.name != 'postgresql' or inspect(engine).get_table_names(schema='public'):
    raise RuntimeError('REFUSED: nonempty or non-PostgreSQL schema')

metadata = MetaData()
appointments = Table('appointments', metadata,
    Column('id', BigInteger, primary_key=True, autoincrement=True),
    Column('employer_id', BigInteger, nullable=False),
    Column('praticien_id', BigInteger, nullable=True),
    Column('resource_id', BigInteger, nullable=True),
    Column('datetime_start', DateTime, nullable=False),
    Column('duration_minutes', Integer, nullable=False),
    Column('status', String(35), nullable=False),
    Column('scheduling_type', String(32), nullable=False),
    Column('deleted_at', DateTime, nullable=True),
    Column('clinical_revision', Integer, nullable=False, server_default='0'),
)
# Deliberately minimal fixture; production lock, SQL predicate and DDL are real.
# This does not certify the complete ORM/router/alembic or clinical UI.
with engine.begin() as conn:
    metadata.create_all(conn)
    install_appointment_revision_guard(conn)
    install_appointment_overlap_index(conn)

tenant, doctor = 900001, 900009
start, duration = datetime(2027, 3, 9, 10, 0), 30

def conflicts(session, candidate, minutes):
    end = candidate + timedelta(minutes=minutes)
    rows = session.execute(select(
        appointments.c.id, appointments.c.datetime_start,
        appointments.c.duration_minutes,
    ).where(
        appointments.c.employer_id == tenant,
        appointments.c.praticien_id == doctor,
        appointments.c.deleted_at.is_(None),
        appointments.c.status.in_(['PREVU', 'CONFIRME']),
        appointments.c.scheduling_type == 'EXACT_TIME',
        appointments.c.datetime_start < end,
        indexed_end_after(session, candidate),
    )).all()
    return [int(row.id) for row in rows if exact_half_open_overlap(
        row.datetime_start, int(row.duration_minutes), candidate, end)]

first_locked, second_attempting = Event(), Event()
second_acquired, release_first = Event(), Event()

def writer_one():
    with Session(engine) as session:
        assert lock_cabinet_booking(session, tenant) is True
        first_locked.set()
        if not release_first.wait(10):
            raise RuntimeError('first writer release timeout')
        assert not conflicts(session, start, duration)
        session.execute(appointments.insert().values(
            employer_id=tenant, praticien_id=doctor, datetime_start=start,
            duration_minutes=duration, status='PREVU', scheduling_type='EXACT_TIME'))
        session.commit()
        return 'FIRST_COMMITTED'

def writer_two():
    with Session(engine) as session:
        second_attempting.set()
        assert lock_cabinet_booking(session, tenant) is True
        second_acquired.set()
        assert len(conflicts(session, start, duration)) == 1, (
            'second writer must see first committed slot after lock')
        session.rollback()
        return 'SECOND_REJECTED_AFTER_LOCK'

try:
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(writer_one)
        assert first_locked.wait(10), 'first writer lock never obtained'
        second = pool.submit(writer_two)
        assert second_attempting.wait(10), 'second writer never attempted lock'
        assert not second_acquired.wait(0.3), 'second writer bypassed advisory lock'
        release_first.set()
        outcomes = [first.result(timeout=15), second.result(timeout=15)]
finally:
    release_first.set()
assert outcomes == ['FIRST_COMMITTED', 'SECOND_REJECTED_AFTER_LOCK']
with Session(engine) as session:
    ids = session.execute(select(appointments.c.id).where(
        appointments.c.employer_id == tenant,
        appointments.c.datetime_start == start)).scalars().all()
    assert len(ids) == 1, 'two bookings occupied one concurrent slot'
    appointment_id = int(ids[0])

with Session(engine) as session:
    lock_cabinet_booking(session, tenant)
    adjacent = start + timedelta(minutes=duration)
    assert not conflicts(session, adjacent, duration), 'adjacent falsely conflicts'
    session.execute(appointments.insert().values(
        employer_id=tenant, praticien_id=doctor, datetime_start=adjacent,
        duration_minutes=duration, status='PREVU', scheduling_type='EXACT_TIME'))
    session.commit()
with Session(engine) as session:
    ids = session.execute(select(appointments.c.id).where(
        appointments.c.employer_id == tenant)).all()
    assert len(ids) == 2, 'adjacent slot missing or duplicate booking'

# S09 primitive: preview snapshot -> status changes away and back -> stale CAS
# MUST fail based on DB-owned revision even though visible status is identical.
with Session(engine) as session:
    original_revision = session.execute(select(
        appointments.c.clinical_revision).where(
        appointments.c.id == appointment_id)).scalar_one()
    assert original_revision == 0
for state in ('TERMINE', 'PREVU'):
    with Session(engine) as session:
        assert session.execute(update(appointments).where(
            appointments.c.id == appointment_id).values(status=state)).rowcount == 1
        session.commit()
with Session(engine) as session:
    snapshot = session.execute(select(
        appointments.c.status, appointments.c.clinical_revision).where(
        appointments.c.id == appointment_id)).one()
    assert snapshot.status == 'PREVU'
    assert snapshot.clinical_revision == original_revision + 2
    new_revision = int(snapshot.clinical_revision)
    rejected = session.execute(update(appointments).where(
        appointments.c.id == appointment_id,
        appointments.c.employer_id == tenant,
        appointments.c.status == 'PREVU',
        appointments.c.clinical_revision == original_revision,
    ).values(status='CONFIRME')).rowcount
    assert rejected == 0, 'stale ABA CAS unexpectedly accepted'
    session.rollback()
with Session(engine) as session:
    accepted = session.execute(update(appointments).where(
        appointments.c.id == appointment_id,
        appointments.c.employer_id == tenant,
        appointments.c.status == 'PREVU',
        appointments.c.clinical_revision == new_revision,
    ).values(status='CONFIRME')).rowcount
    assert accepted == 1, 'fresh revision CAS refused'
    session.commit()
with Session(engine) as session:
    end_revision = session.execute(select(
        appointments.c.clinical_revision).where(
        appointments.c.id == appointment_id)).scalar_one()
    assert end_revision == new_revision + 1

report = {
    'schema': 'CB01_PG_S07_S09_PRIMITIVES_V1',
    'sourceHead': head,
    'isolatedDatabase': 'LOOPBACK_POSTGRES_EMPTY_MINIMAL_FIXTURE',
    'productionCodeExercised': [
        'agenda_transaction_lock.lock_cabinet_booking',
        'agenda_interval_overlap.indexed_end_after',
        'agenda_interval_overlap.exact_half_open_overlap',
        'appointment_revision_ddl.install_appointment_revision_guard',
        'appointment_revision_ddl.install_appointment_overlap_index',
    ],
    'S07': {
        'status': 'PASS_PG_PRIMITIVES_ONLY',
        'independentTransactions': 2,
        'firstWriter': outcomes[0],
        'secondWriter': outcomes[1],
        'sameSlotCreated': 1, 'adjacentSlotCreated': 1,
        'fullAppointmentHttpRace': 'NOT_RUN',
    },
    'S09': {
        'status': 'PASS_PG_REVISION_PRIMITIVE_ONLY',
        'beforeRevision': original_revision, 'afterABARevision': new_revision,
        'staleCASUpdatedRows': rejected, 'freshCASUpdatedRows': accepted,
        'fullCrownBotBookingABA': 'NOT_RUN',
    },
    'humanE2EValidated': 0,
    'clinicalProductionDatabaseTouched': False,
    'converged': False,
}
out = Path('artifacts/cb01-concurrency/pg-s07-s09-evidence.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('CB01_PG_S07_S09: PASS_PRIMITIVES_ONLY; NO_CLINICAL_OR_HUMAN_E2E')
