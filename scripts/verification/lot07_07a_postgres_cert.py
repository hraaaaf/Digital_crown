"""Isolated exact-source PostgreSQL/FastAPI concurrency adversarial laboratory.

Never run outside a dedicated synthetic CI PostgreSQL database.
Auth is replaced by an explicit test-only dependency; real HTTP routing,
Pydantic models, SQLAlchemy sessions, locking, and PostgreSQL persistence are used.
"""
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier, Event
from time import monotonic, sleep

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
url = os.environ.get("DATABASE_URL", "")
assert url.startswith("postgresql+psycopg://")
assert url.endswith("/dc_agenda_synthetic")
assert os.environ.get("PG_CERT_LAB") == "1"

from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from backend import database, models
from backend.routers import appointments
from backend.services.agenda_write_lock import lock_cabinet_appointment_writes

engine = database.engine
assert engine.dialect.name == "postgresql"
with engine.connect() as c:
    db_name = c.scalar(text("SELECT current_database()"))
    assert db_name == "dc_agenda_synthetic", db_name
    print("PG_CERT_SERVER", c.scalar(text("SELECT version()")))
    print("PG_CERT_ISOLATION", c.scalar(text("SHOW default_transaction_isolation")))
    print("PG_CERT_DATABASE", db_name)
models.Base.metadata.create_all(bind=engine)
Session = database.SessionLocal
with Session() as s:
    root1 = models.User(email="pg-lab-root1@example.invalid", hashed_password="SYNTHETIC", role=models.UserRole.DENTISTE,
                        is_active=True, is_licensed=True, approval_status=models.ApprovalStatus.APPROVED.value)
    root2 = models.User(email="pg-lab-root2@example.invalid", hashed_password="SYNTHETIC", role=models.UserRole.DENTISTE,
                        is_active=True, is_licensed=True, approval_status=models.ApprovalStatus.APPROVED.value)
    s.add_all((root1, root2))
    s.flush()
    colleague = models.User(email="pg-lab-colleague@example.invalid", hashed_password="SYNTHETIC",
                            role=models.UserRole.DENTISTE, is_active=True, is_licensed=True,
                            approval_status=models.ApprovalStatus.APPROVED.value, employer_id=root1.id)
    chair = models.AgendaResource(employer_id=root1.id, name="SYNTHETIC CHAIR", resource_type="CHAIR", is_active=True)
    s.add_all((colleague, chair))
    s.flush()
    A, B, C, CHAIR = root1.id, colleague.id, root2.id, chair.id
    s.commit()

app = FastAPI()
app.include_router(appointments.router, prefix="/api/appointments")

def db_override():
    with Session() as s:
        try:
            yield s
        finally:
            s.rollback()

def fake_user(request: Request):
    actor = {"A": A, "B": B, "C": C}.get(request.headers.get("X-PG-Lab-Actor"))
    if actor is None:
        raise HTTPException(403, "CI actor required")
    with Session() as s:
        user = s.get(models.User, actor)
        assert user is not None
        s.expunge(user)
        return user

app.dependency_overrides[database.get_db] = db_override
auth_overrides = 0
for route in app.routes:
    if isinstance(route, APIRoute):
        for dep in route.dependant.dependencies:
            if dep.name == "current_user":
                app.dependency_overrides[dep.call] = fake_user
                auth_overrides += 1
assert auth_overrides >= 3, auth_overrides
print("PG_CERT_HTTP", "REAL_APPOINTMENTS_ROUTER", "AUTH_TEST_OVERRIDE", auth_overrides)

def payload(slot, *, practitioner=None, resource=None, minutes=30, name="PG SYNTHETIC"):
    result = {"datetime_start": slot, "patient_name": name, "duration_minutes": minutes,
              "status": "PRÉVU", "scheduling_type": "EXACT_TIME"}
    if practitioner is not None:
        result["praticien_id"] = practitioner
    if resource is not None:
        result["resource_id"] = resource
    return result

def call(method, path, actor="A", body=None, barrier=None):
    if barrier is not None:
        barrier.wait(timeout=10)
    with TestClient(app, raise_server_exceptions=False) as cli:
        response = cli.request(method, path, headers={"X-PG-Lab-Actor": actor}, json=body)
    return response.status_code, response.text[:240]

def race(*operations):
    b = Barrier(len(operations))
    with ThreadPoolExecutor(max_workers=len(operations)) as ex:
        fs = [ex.submit(call, op[0], op[1], op[2], op[3], b) for op in operations]
        return [f.result(timeout=25) for f in fs]

def post(slot, actor="A", practitioner=None, resource=None, minutes=30):
    return ("POST", "/api/appointments/", actor,
            payload(slot, practitioner=practitioner, resource=resource, minutes=minutes))

def bulk(*items):
    return ("POST", "/api/appointments/bulk", "A",
            {"appointments": [dict(patient_name="PG SYNTHETIC BULK", datetime_start=slot,
                                   duration_minutes=30, status="PRÉVU", scheduling_type="EXACT_TIME")
                              for slot in items]})

def persisted():
    with engine.connect() as c:
        return [dict(row) for row in c.execute(text(
            "SELECT id, employer_id, praticien_id, resource_id, datetime_start, "
            "duration_minutes FROM appointments WHERE deleted_at IS NULL ORDER BY id"
        )).mappings().all()]

def clear_appointments():
    with engine.begin() as c:
        c.execute(text("DELETE FROM appointments"))

def require_statuses(name, statuses, expected, rows, round_index):
    got = sorted(x[0] for x in statuses)
    if got != sorted(expected):
        raise AssertionError(f"{name} iteration {round_index}: HTTP {got}, expected {expected}, SQL rows={rows}")
    if round_index in (0, 19):
        print("PG_CERT_CASE", name, "ITER", round_index + 1, "HTTP", got,
              "SQL", [(r["id"],r["employer_id"],r["praticien_id"],r["resource_id"],
                       r["datetime_start"].isoformat(),r["duration_minutes"]) for r in rows])

def assert_one_slot(rows, slot, employer=A):
    matching = [r for r in rows if r["employer_id"] == employer
                and r["datetime_start"].isoformat() == slot]
    assert len(matching) == 1, matching

# Transaction-lock semantics including first statement, committed/reverted locks, wait-timeout.
def lock_checks():
    key = (0xDC07 << 32) | A
    with Session() as holder, Session() as observer:
        lock_cabinet_appointment_writes(holder, A)
        backend_pid = holder.execute(text("SELECT pg_backend_pid()")).scalar_one()
        seen = observer.execute(text(
            "SELECT count(*) FROM pg_locks WHERE pid=:pid AND locktype='advisory' AND granted"
        ), {"pid": backend_pid}).scalar_one()
        assert seen >= 1
        assert observer.execute(text("SELECT pg_try_advisory_xact_lock(:k)"),
                                {"k":key}).scalar_one() is False
        observer.rollback()
        print("PG_CERT_ADVISORY_GRANTED", backend_pid, seen, "blocked=YES")
        with Session() as waiting:
            waiting.execute(text("SET LOCAL lock_timeout = '250ms'"))
            try:
                lock_cabinet_appointment_writes(waiting, A)
                raise AssertionError("Lock timeout was unexpectedly bypassed")
            except HTTPException as e:
                assert e.status_code == 503, e
                waiting.rollback()
                print("PG_CERT_LOCK_TIMEOUT_HTTP_MAPPING", 503)
        holder.commit()
        assert observer.execute(text("SELECT pg_try_advisory_xact_lock(:k)"),
                                {"k":key}).scalar_one() is True
        observer.rollback()
        with Session() as rollback_holder:
            lock_cabinet_appointment_writes(rollback_holder,A)
            rollback_holder.rollback()
        assert observer.execute(text("SELECT pg_try_advisory_xact_lock(:k)"),
                                {"k":key}).scalar_one() is True
        observer.rollback()
        print("PG_CERT_LOCK_RELEASE", "COMMIT=PASS", "ROLLBACK=PASS")

    locked, waiting, done = Event(), Event(), Event()
    output=[]
    def waiter():
        with Session() as s:
            waiting.set()
            try:
                lock_cabinet_appointment_writes(s,A)
                output.append("unexpected_acquired")
            except HTTPException as e:
                output.append(f"http_{e.status_code}")
            except Exception as e:
                output.append(type(e).__name__)
            finally:
                s.rollback()
                done.set()
    with Session() as h:
        lock_cabinet_appointment_writes(h,A)
        with ThreadPoolExecutor(max_workers=1) as ex:
            f = ex.submit(waiter)
            assert waiting.wait(5)
            timeout_at = monotonic() + 5
            waiter_pid = None
            with Session() as monitor:
                while monotonic() < timeout_at:
                    row = monitor.execute(text(
                        "SELECT pid FROM pg_stat_activity WHERE datname=current_database() "
                        "AND wait_event_type='Lock' AND pid <> pg_backend_pid() "
                        "AND query LIKE '%pg_advisory_xact_lock%' ORDER BY pid LIMIT 1"
                    )).first()
                    monitor.rollback()
                    if row:
                        waiter_pid = row[0]
                        break
                    sleep(.05)
                assert waiter_pid is not None, "No actual waiting PostgreSQL backend observed"
                cancelled = monitor.execute(text("SELECT pg_cancel_backend(:pid)"),
                                            {"pid":waiter_pid}).scalar_one()
                monitor.rollback()
                assert cancelled
            assert done.wait(5)
            f.result(timeout=5)
        h.rollback()
    assert output and output[0] != "unexpected_acquired", output
    print("PG_CERT_INTERRUPTION", "pg_cancel_backend", "waiter_pid", waiter_pid,
          "outcome", output[0], "released_by_rollback=YES")

lock_checks()
rounds = 20
for i in range(rounds):
    t = "2026-11-02T12:00:00"
    clear_appointments()
    results = race(post(t), post(t))
    rows = persisted()
    require_statuses("POST_POST", results, [200,409], rows, i)
    assert len(rows)==1
    assert_one_slot(rows,t)

    clear_appointments()
    seed = call(*post("2026-11-02T08:00:00"))
    assert seed[0] == 200, seed
    with engine.connect() as c:
        old_id=c.scalar(text("SELECT id FROM appointments WHERE employer_id=:e"),{"e":A})
    t = "2026-11-02T13:00:00"
    results = race(("PUT",f"/api/appointments/{old_id}","A",{"datetime_start":t}), post(t))
    rows = persisted()
    require_statuses("PUT_POST", results, [200,409], rows, i)
    assert len(rows) in (1,2) and len([r for r in rows if r["datetime_start"].isoformat()==t])==1

    clear_appointments()
    t = "2026-11-02T14:00:00"
    results = race(post(t,"A",resource=CHAIR), post(t,"B",practitioner=B,resource=CHAIR))
    rows = persisted()
    require_statuses("RESOURCE_CAPACITY_ONE", results, [200,409], rows, i)
    assert len(rows)==1 and rows[0]["resource_id"]==CHAIR

    clear_appointments()
    t = "2026-11-02T15:00:00"
    results = race(post(t,"A"),post(t,"C"))
    rows = persisted()
    require_statuses("INDEPENDENT_CABINETS", results, [200,200], rows, i)
    assert len(rows)==2 and {r["employer_id"] for r in rows} == {A,C}

    clear_appointments()
    results = race(post("2026-11-02T09:00:00",minutes=360),
                   post("2026-11-02T14:30:00"))
    rows = persisted()
    require_statuses("SIX_HOURS_OVERLAP", results, [200,409], rows, i)
    assert len(rows)==1

    clear_appointments()
    results = race(bulk("2026-11-02T18:00:00","2026-11-02T18:30:00"),
                   post("2026-11-02T18:00:00"))
    rows = persisted()
    require_statuses("BULK_VS_SINGLE", results, [200,409], rows, i)
    assert len(rows) in (1,2), rows
    assert len([r for r in rows if r["datetime_start"].hour==18 and
                r["datetime_start"].minute==0]) == 1
    assert len(rows)==1 or (len(rows)==2 and
                          sorted(r["datetime_start"].minute for r in rows)==[0,30])

print("PG_CERT_TOTAL_RACES", rounds * 6)
print("PG_CERT_HTTP_500", 0)
print("PG_CERT_DB_SQL_ASSERTIONS", "ALL_PASS")
print("PG_CERT_RESULT", "PASS_WITH_SYNTHETIC_AUTH_NO_MULTI_PROCESS_WORKERS")

# Adversarial cross-entrypoint: a separate real Bot HTTP route must not bypass
# the exact same practitioner's canonical appointment write lock.
from datetime import timedelta
from backend.routers import bot as bot_routes

app.include_router(bot_routes.router, prefix="/api/bot")
app.dependency_overrides[bot_routes.get_db] = db_override
app.dependency_overrides[bot_routes.get_current_user] = fake_user

clear_appointments()
bot_slot = "2026-11-03T11:00:00"
primary = call(*post(bot_slot))
assert primary[0] == 200, primary
with Session() as s:
    session = models.BotSession(employer_id=A, user_id=A, title="Synthetic PG cross writer")
    s.add(session)
    s.flush()
    action = models.BotPendingAction(
        session_id=session.id, user_id=A, employer_id=A, action_type="CREATE_APPOINTMENT",
        params_json={"patient_id": None, "patient_name": "PG SYNTHETIC BOT",
                     "datetime_start": bot_slot, "duration_minutes": 30,
                     "motif": "test only"},
        status="pending", expires_at=datetime.utcnow() + timedelta(minutes=10))
    s.add(action)
    s.flush()
    action_id = action.id
    s.commit()

second = call("POST", "/api/bot/execute", "A", {"pending_action_id": action_id})
rows = persisted()
duplicates = [r for r in rows if r["employer_id"] == A
              and r["datetime_start"].isoformat() == bot_slot]
print("PG_CERT_CROSS_ENTRY_BOT", "HTTP", [primary[0],second[0]],
      "PERSISTED_SAME_CABINET_SAME_SLOT", len(duplicates),
      "PRACTITIONERS", [r["praticien_id"] for r in duplicates],
      flush=True)
assert second[0] == 409 and len(duplicates) == 1, (
    "BLOCKER: bot /execute bypasses PostgreSQL advisory booking lock; "
    f"HTTP={primary[0],second[0]} same-slot={len(duplicates)}")
print("PG_CERT_CROSS_ENTRY_BOT", "PASS", flush=True)


# F05 adversarial extension: independent operating-system processes. These
# forks have distinct SQLAlchemy pools and genuine FastAPI/ASGI request handling.
# Authentication remains an EXPLICIT LAB SUBSTITUTION (X-PG-Lab-Actor); this
# is not a workstation-authenticated production HTTP or encrypted PC transport.
import multiprocessing as _multiprocessing
import os as _os
import uuid as _uuid
from fastapi import Depends
from fastapi.responses import JSONResponse
from backend.routers import frontdesk as _frontdesk
from backend.services import patient_companion_agenda as _pc_agenda
from backend.models_patient_companion import (
    PatientCompanionIdentity as _Identity,
    PatientCompanionAccess as _Access,
    PatientCompanionAgendaSlot as _Slot,
    PatientCompanionAppointmentRef as _Ref,
)

app.include_router(_frontdesk.router, prefix="/api")
app.dependency_overrides[_frontdesk.get_current_user] = fake_user


@app.post("/__synthetic_f05__/pc-create")
def _synthetic_pc_create(body: dict, db=Depends(database.get_db)):
    access = db.get(_Access, int(body["access_id"]))
    if access is None:
        raise HTTPException(404, "synthetic access not found")
    result = _pc_agenda.create_appointment(db, access, {"slot_ref": body["slot_ref"]})
    db.commit()
    return JSONResponse(
        status_code=200 if result.status == "ACCEPTED" else 409,
        content={"state": result.status, **result.response},
    )


@app.post("/__synthetic_f05__/pc-reschedule")
def _synthetic_pc_reschedule(body: dict, db=Depends(database.get_db)):
    access = db.get(_Access, int(body["access_id"]))
    if access is None:
        raise HTTPException(404, "synthetic access not found")
    result = _pc_agenda.reschedule_appointment(
        db, access, {"slot_ref": body["slot_ref"], "appointment_ref": body["appointment_ref"]}
    )
    db.commit()
    return JSONResponse(
        status_code=200 if result.status == "ACCEPTED" else 409,
        content={"state": result.status, **result.response},
    )


def _mp_worker(operation, gate, ready, answer):
    # fork inherited an Engine pool: discard it without touching the parent's
    # real connection; this forces independent PostgreSQL sessions per PID.
    engine.dispose(close=False)
    pid = _os.getpid()
    ready.put(pid)
    if not gate.wait(timeout=20):
        answer.put((pid, 599, "race gate timeout"))
        return
    try:
        response = call(*operation)
        answer.put((pid, response[0], response[1]))
    except BaseException as exc:
        answer.put((pid, 599, type(exc).__name__))


def _mp_race(first, second):
    ctx = _multiprocessing.get_context("fork")  # explicit Ubuntu/Linux runner only
    gate, ready, answer = ctx.Event(), ctx.Queue(), ctx.Queue()
    processes = [
        ctx.Process(target=_mp_worker, args=(op, gate, ready, answer))
        for op in (first, second)
    ]
    try:
        for proc in processes:
            proc.start()
        pids = [ready.get(timeout=15) for _ in processes]
        assert len(set(pids)) == 2 and _os.getpid() not in pids, pids
        gate.set()
        results = [answer.get(timeout=30) for _ in processes]
        for proc in processes:
            proc.join(timeout=15)
            assert proc.exitcode == 0, (proc.pid, proc.exitcode)
        assert len({row[0] for row in results}) == 2, results
        return [(row[1], row[2]) for row in results], sorted(pids)
    finally:
        gate.set()
        for proc in processes:
            if proc.is_alive():
                proc.terminate()
            proc.join(timeout=3)


def _mp_cleanup():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM patient_companion_appointment_refs"))
        conn.execute(text("DELETE FROM appointments"))


def _pc_slot(session, access, target):
    slot = _Slot(
        public_id=str(_uuid.uuid4()), employer_id=A, practitioner_id=A,
        datetime_start=datetime.fromisoformat(target), duration_minutes=30,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    session.add(slot)
    session.flush()
    return slot.public_id, slot.id


with Session() as s:
    patient = models.Patient(
        numero_dossier="MP-PC-" + _uuid.uuid4().hex[:10],
        nom="Synthetic", prenom="CrossChannel",
        date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=A,
    )
    identity = _Identity(provider="local_bridge", subject="mp-" + _uuid.uuid4().hex)
    s.add_all([patient, identity])
    s.flush()
    access = _Access(
        public_id=str(_uuid.uuid4()), employer_id=A, patient_id=patient.id,
        identity_id=identity.id, relationship_type="SELF",
    )
    s.add(access)
    s.flush()
    MP_ACCESS, MP_PATIENT = access.id, patient.id
    s.commit()

print("F05_MP_AUTH", "SYNTHETIC_ACTOR_OVERRIDE", "PC_REMOTE_ENVELOPE_SUBSTITUTED", flush=True)
mp_counts = Counter()
for iteration in range(4):
    slot_time = "2026-11-04T10:00:00"

    _mp_cleanup()
    statuses, pids = _mp_race(post(slot_time), post(slot_time))
    rows = persisted()
    require_statuses("MP_AGENDA_AGENDA", statuses, [200, 409], rows, iteration)
    assert len(rows) == 1
    mp_counts["agenda-agenda"] += 1

    _mp_cleanup()
    fd = ("POST", "/api/frontdesk/appointment-request", "A", {
        "first_name": "MP", "last_name": "Synthetic", "requested_start": slot_time,
        "duration_minutes": 30, "source": "frontdesk"
    })
    statuses, pids = _mp_race(post(slot_time), fd)
    rows = persisted()
    require_statuses("MP_AGENDA_FRONTDESK_REQUEST", statuses, [200, 409], rows, iteration)
    assert len(rows) == 1
    mp_counts["agenda-frontdesk-request"] += 1

    _mp_cleanup()
    response = call(*fd)
    assert response[0] == 200, response
    with engine.connect() as c:
        pending_id = c.scalar(text(
            "SELECT id FROM appointments WHERE employer_id=:e AND status='EN_ATTENTE_DEMANDE'"
        ), {"e": A})
    assert pending_id is not None
    confirm = ("POST", f"/api/appointments/{pending_id}/confirm", "A", None)
    statuses, pids = _mp_race(post(slot_time), confirm)
    rows = persisted()
    require_statuses("MP_AGENDA_FRONTDESK_CONFIRM", statuses, [200, 409], rows, iteration)
    assert len(rows) == 1
    mp_counts["agenda-frontdesk-confirm"] += 1

    _mp_cleanup()
    with Session() as s:
        slot_ref, slot_id = _pc_slot(s, MP_ACCESS, slot_time)
        s.commit()
    pc_create = ("POST", "/__synthetic_f05__/pc-create", "A", {
        "access_id": MP_ACCESS, "slot_ref": slot_ref
    })
    statuses, pids = _mp_race(post(slot_time), pc_create)
    rows = persisted()
    require_statuses("MP_AGENDA_PC_CREATE", statuses, [200, 409], rows, iteration)
    assert len(rows) == 1
    with Session() as s:
        persisted_slot = s.get(_Slot, slot_id)
        assert (persisted_slot.consumed_at is not None) == (statuses[1][0] == 200)
    mp_counts["agenda-pc-create"] += 1

    _mp_cleanup()
    with Session() as s:
        old = models.Appointment(
            patient_id=MP_PATIENT, employer_id=A, praticien_id=A,
            datetime_start=datetime(2026, 11, 4, 8), duration_minutes=30,
            status=models.AppointmentStatus.CONFIRME,
            scheduling_type=models.SchedulingType.EXACT_TIME, source="patient_companion",
        )
        s.add(old)
        s.flush()
        ref = _Ref(
            public_id=str(_uuid.uuid4()), appointment_id=old.id,
            employer_id=A, patient_id=MP_PATIENT,
        )
        s.add(ref)
        slot_ref, slot_id = _pc_slot(s, MP_ACCESS, slot_time)
        appt_ref = ref.public_id
        s.commit()
    pc_move = ("POST", "/__synthetic_f05__/pc-reschedule", "A", {
        "access_id": MP_ACCESS, "slot_ref": slot_ref, "appointment_ref": appt_ref,
    })
    statuses, pids = _mp_race(post(slot_time), pc_move)
    rows = persisted()
    require_statuses("MP_AGENDA_PC_RESCHEDULE", statuses, [200, 409], rows, iteration)
    assert len([row for row in rows if row["datetime_start"].isoformat() == slot_time]) == 1
    with Session() as s:
        persisted_slot = s.get(_Slot, slot_id)
        assert (persisted_slot.consumed_at is not None) == (statuses[1][0] == 200)
    mp_counts["agenda-pc-reschedule"] += 1

    _mp_cleanup()
    with Session() as s:
        bot_session = models.BotSession(
            employer_id=A, user_id=A, title="MP synthetic",
        )
        s.add(bot_session)
        s.flush()
        pending = models.BotPendingAction(
            session_id=bot_session.id, user_id=A, employer_id=A,
            action_type="CREATE_APPOINTMENT",
            params_json={
                "patient_id": None, "patient_name": "MP BOT", "datetime_start": slot_time,
                "duration_minutes": 30, "motif": "synthetic",
            },
            status="pending", expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        s.add(pending)
        s.flush()
        action_id = pending.id
        s.commit()
    bot_request = ("POST", "/api/bot/execute", "A", {"pending_action_id": action_id})
    statuses, pids = _mp_race(post(slot_time), bot_request)
    rows = persisted()
    require_statuses("MP_AGENDA_BOT", statuses, [200, 409], rows, iteration)
    assert len(rows) == 1
    mp_counts["agenda-bot"] += 1

print("F05_MP_RESULTS", dict(mp_counts), "TOTAL", sum(mp_counts.values()), flush=True)
print("F05_MP_PIDS", "DISTINCT_AT_EACH_RACE", "FASTAPI_ASGI_TESTCLIENT_NOT_UVICORN", flush=True)
print("F05_MP_SQL", "NO_DUPLICATE_IN_EXECUTED_FIXTURES", "PC_SLOTS_CONSISTENT", flush=True)
print("F05_MP_RESULT", "PARTIAL_AUTH_AND_REMOTE_TRANSPORT_SUBSTITUTED", flush=True)
