"""F05 adversarial two-process HTTP lab. Synthetic PostgreSQL only.

This intentionally does NOT certify real auth, encrypted remote delivery or
Patient Companion receipt durability. The PC adapter invokes the real domain
handler but substitutes the remote envelope. Every substitution is reported.
"""
import os
assert os.getenv("ENVIRONMENT") == "test"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.getenv("PG_CERT_LAB") == "1"
assert os.getenv("DATABASE_URL", "").startswith("postgresql+psycopg://")
assert os.getenv("DATABASE_URL", "").endswith("/dc_agenda_synthetic")

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import json
import subprocess
import sys
import time
import uuid

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_patient_companion import (
    PatientCompanionIdentity, PatientCompanionAccess,
    PatientCompanionAgendaSlot, PatientCompanionAppointmentRef,
)
from backend.routers import appointments, frontdesk, bot as bot_routes, auth as auth_routes
from backend.security import get_password_hash
from backend.services import patient_companion_agenda as pc

LAB_PASSWORD = "F05_TEST_ONLY_NOT_A_PRODUCTION_CREDENTIAL"

SessionLocal = database.SessionLocal
app = FastAPI()
app.include_router(appointments.router, prefix="/api/appointments")
app.include_router(frontdesk.router, prefix="/api")
app.include_router(bot_routes.router, prefix="/api/bot")
# Separate ASGI subapp: no dependency overrides. The product's real JWT,
# permission and workstation dependencies run against disposable PostgreSQL.
real_auth_app = FastAPI()
real_auth_app.include_router(appointments.router, prefix="/api/appointments")
real_auth_app.include_router(frontdesk.router, prefix="/api")
real_auth_app.include_router(bot_routes.router, prefix="/api/bot")
real_auth_app.include_router(auth_routes.router, prefix="/api/auth")
app.mount("/real-auth", real_auth_app)

def lab_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.rollback()

def lab_actor(request: Request):
    actor = request.headers.get("X-PG-Lab-Actor", "")
    lookup = {"A": "f05-a@example.invalid", "B": "f05-b@example.invalid",
              "C": "f05-c@example.invalid"}
    email = lookup.get(actor)
    if not email:
        raise HTTPException(401, "synthetic actor missing")
    with SessionLocal() as db:
        user = db.query(models.User).filter_by(email=email).one()
        db.expunge(user)
        return user

app.dependency_overrides[database.get_db] = lab_db
for module in (frontdesk, appointments, bot_routes):
    if hasattr(module, "get_db"):
        app.dependency_overrides[module.get_db] = lab_db
for route in app.routes:
    if isinstance(route, APIRoute):
        for dep in route.dependant.dependencies:
            if dep.name == "current_user":
                app.dependency_overrides[dep.call] = lab_actor

@app.get("/lab/pid")
def pid():
    return {"pid": os.getpid()}

@app.post("/lab/pc/{operation}")
def companion(operation: str, payload: dict, request: Request,
              db: Session = Depends(lab_db)):
    if request.headers.get("X-PG-Lab-Actor") != "A":
        raise HTTPException(403, "synthetic PC fixture actor")
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.employer_id ==
        db.query(models.User.id).filter_by(email="f05-a@example.invalid").scalar()
    ).one()
    if operation == "create":
        outcome = pc.create_appointment(db, access, payload)
    elif operation == "reschedule":
        outcome = pc.reschedule_appointment(db, access, payload)
    else:
        raise HTTPException(404, "invalid operation")
    # Remote worker in the real product owns the transaction/receipt.
    # This laboratory adapter cannot assert actual encrypted receipts.
    db.commit()
    if outcome.status != "ACCEPTED":
        raise HTTPException(409, outcome.response)
    return outcome.response

def seed():
    models.Base.metadata.create_all(bind=database.engine)
    with SessionLocal() as db:
        root = models.User(email="f05-a@example.invalid", hashed_password=get_password_hash(LAB_PASSWORD),
                           role=models.UserRole.DENTISTE, is_active=True,
                           is_licensed=True, approval_status=models.ApprovalStatus.APPROVED.value)
        other = models.User(email="f05-c@example.invalid", hashed_password=get_password_hash(LAB_PASSWORD),
                            role=models.UserRole.DENTISTE, is_active=True,
                            is_licensed=True, approval_status=models.ApprovalStatus.APPROVED.value)
        db.add_all([root, other]); db.flush()
        colleague = models.User(email="f05-b@example.invalid", hashed_password=get_password_hash(LAB_PASSWORD),
                               role=models.UserRole.DENTISTE, employer_id=root.id,
                               is_active=True, is_licensed=True,
                               approval_status=models.ApprovalStatus.APPROVED.value)
        chair = models.AgendaResource(employer_id=root.id, name="F05 synthetic chair",
                                      resource_type="CHAIR", is_active=True)
        patient = models.Patient(numero_dossier="F05-PG-MP", nom="F05",
                                 prenom="Synthetic", date_naissance=datetime(2000, 1, 1),
                                 sexe="F", employer_id=root.id)
        identity = PatientCompanionIdentity(provider="local_bridge",
                                            subject="f05-mp-"+str(uuid.uuid4()))
        db.add_all([colleague, chair, patient, identity]); db.flush()
        access = PatientCompanionAccess(employer_id=root.id, patient_id=patient.id,
                                         identity_id=identity.id, relationship_type="SELF")
        db.add(access); db.commit()
        return root.id, colleague.id, other.id, chair.id, patient.id, access.id

def request(port, method, path, actor="A", body=None, barrier=None):
    if barrier:
        barrier.wait(timeout=12)
    with httpx.Client(timeout=22) as c:
        r = c.request(method, f"http://127.0.0.1:{port}{path}",
                      headers={"X-PG-Lab-Actor":actor}, json=body)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:180]

def race(left, right):
    barrier=Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as ex:
        tasks=[ex.submit(request,*args,barrier=barrier) for args in (left,right)]
        return [t.result(timeout=29) for t in tasks]

def book(t, actor="A", practitioner=None, resource=None):
    payload={"patient_name":"SYNTHETIC F05", "datetime_start":t,
             "duration_minutes":30, "status":"PRÉVU","scheduling_type":"EXACT_TIME"}
    if practitioner is not None:
        payload["praticien_id"]=practitioner
    if resource is not None:
        payload["resource_id"]=resource
    return (18061,"POST","/api/appointments/",actor,payload)

def front(t):
    return (18062,"POST","/api/frontdesk/appointment-request","A",
            {"first_name":"Synthetic","last_name":"F05",
             "requested_start":t,"duration_minutes":30})

def slot(db, employer, practitioner, start):
    record=PatientCompanionAgendaSlot(public_id=str(uuid.uuid4()),
                                     employer_id=employer, practitioner_id=practitioner,
                                     datetime_start=datetime.fromisoformat(start),
                                     duration_minutes=30,
                                     expires_at=datetime.utcnow()+timedelta(minutes=20))
    db.add(record); db.flush()
    return record.public_id

def clear():
    with database.engine.begin() as con:
        con.execute(text("DELETE FROM patient_companion_appointment_refs"))
        con.execute(text("DELETE FROM appointments"))
        con.execute(text("DELETE FROM patient_companion_agenda_slots"))

def rows_at(start, employer=None):
    with database.engine.connect() as con:
        sql=("SELECT employer_id, praticien_id, status, resource_id, datetime_start "
             "FROM appointments WHERE datetime_start=:dt AND deleted_at IS NULL")
        rows=con.execute(text(sql),{"dt":datetime.fromisoformat(start)}).mappings().all()
        return [dict(r) for r in rows if employer is None or r["employer_id"]==employer]

def assert_case(name, responses, expected, t, employer, expected_rows=1):
    statuses=sorted(r[0] for r in responses)
    persisted=rows_at(t, employer)
    print("F05_MP_CASE",name, "HTTP",statuses, "SQL_COUNT",len(persisted),
          "ROWS",[(r["employer_id"],r["praticien_id"],
                    getattr(r["status"],"value",r["status"]),r["resource_id"]) for r in persisted],
          flush=True)
    assert statuses==sorted(expected), (name,statuses,responses)
    assert len(persisted)==expected_rows, (name,persisted)

def exercise():
    root,colleague,other,chair,patient,access=seed()
    procs=[]
    try:
        for port in (18061,18062):
            p=subprocess.Popen([sys.executable,"-m","uvicorn",
                                "scripts.verification.lot07_07a_f05_multiprocess:app",
                                "--host","127.0.0.1","--port",str(port),"--workers","1"],
                               stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            procs.append(p)
        for _ in range(80):
            try:
                ids=[request(port,"GET","/lab/pid")[1]["pid"] for port in (18061,18062)]
                if all(p.poll() is None for p in procs) and ids[0]!=ids[1]:
                    break
            except Exception:
                pass
            time.sleep(0.25)
        else:
            raise AssertionError("distinct FastAPI processes never became ready")
        print("F05_MP_PROCESS_IDS",ids,"DISTINCT",ids[0]!=ids[1],flush=True)
        t="2026-11-02T10:00:00"
        for i in range(10):
            clear()
            assert_case("AGENDA_VS_FRONTDESK_REQUEST",race(book(t),front(t)),
                        [200,409],t,root)
            clear()
            with SessionLocal() as db:
                ref=slot(db,root,root,t); db.commit()
            pc_op=(18062,"POST","/lab/pc/create","A",{"slot_ref":ref})
            assert_case("AGENDA_VS_PC_CREATE",race(book(t),pc_op),
                        [200,409],t,root)
            clear()
            with SessionLocal() as db:
                ref=slot(db,root,root,t); db.commit()
            pc_op=(18062,"POST","/lab/pc/create","A",{"slot_ref":ref})
            assert_case("PC_REPLAY_VS_PC_CREATE",race(
                (18061,"POST","/lab/pc/create","A",{"slot_ref":ref}),pc_op),
                [200,409],t,root)
            with database.engine.connect() as con:
                consumed=con.scalar(text(
                    "SELECT COUNT(*) FROM patient_companion_agenda_slots "
                    "WHERE public_id=:ref AND consumed_at IS NOT NULL"
                ),{"ref":ref})
            assert consumed==1,("PC_SLOT_CONSUMPTION",consumed)
            clear()
            assert_case("FRONTDESK_REQUEST_VS_REQUEST",race(
                (18061,*front(t)[1:]),front(t)),[200,409],t,root)
            clear()
            with SessionLocal() as db:
                session=models.BotSession(employer_id=root,user_id=root,
                                          title="F05 synthetic bot")
                db.add(session);db.flush()
                pending_bot=models.BotPendingAction(
                    session_id=session.id,user_id=root,employer_id=root,
                    action_type="CREATE_APPOINTMENT",
                    params_json={"patient_id":None,"patient_name":"F05 synthetic Bot",
                                 "datetime_start":t,"duration_minutes":30,"motif":"LAB"},
                    status="pending",expires_at=datetime.utcnow()+timedelta(minutes=10))
                db.add(pending_bot);db.flush()
                action_id=pending_bot.id
                db.commit()
            bot_op=(18062,"POST","/api/bot/execute","A",
                    {"pending_action_id":str(action_id)})
            assert_case("CROWN_BOT_VS_AGENDA_TWO_WORKERS",race(
                book(t),bot_op),[200,409],t,root)
            clear()
            pending=request(*front(t))
            assert pending[0]==200,pending
            confirm=(18062,"POST",f"/api/appointments/{pending[1]['id']}/confirm","A",{})
            assert_case("FRONTDESK_CONFIRM_VS_AGENDA",race(book(t),confirm),
                        [200,409],t,root)
            clear()
            with SessionLocal() as db:
                old=models.Appointment(patient_name="F05 MOVABLE",patient_id=patient,
                                       employer_id=root,praticien_id=root,
                                       datetime_start=datetime(2026,11,2,8),duration_minutes=30,
                                       status=models.AppointmentStatus.CONFIRME,
                                       scheduling_type=models.SchedulingType.EXACT_TIME)
                db.add(old); db.flush()
                ref_obj=PatientCompanionAppointmentRef(
                    public_id=str(uuid.uuid4()), employer_id=root, patient_id=patient,
                    appointment_id=old.id)
                ref=slot(db,root,root,t)
                db.add(ref_obj);db.commit()
                appointment_ref=ref_obj.public_id
            move=(18062,"POST","/lab/pc/reschedule","A",
                  {"appointment_ref":appointment_ref,"slot_ref":ref})
            assert_case("PC_RESCHEDULE_VS_AGENDA",race(book(t),move),
                        [200,409],t,root)
            clear()
            left=book(t,resource=chair)
            right=book(t,actor="B",practitioner=colleague,resource=chair)
            assert_case("CROSS_WORKER_SHARED_RESOURCE",race(
                left,(18062,*right[1:])),[200,409],t,root)
            clear()
            right=book(t,actor="C")
            assert_case("TWO_CABINETS",race(book(t),(18062,*right[1:])),
                        [200,200],t,root)
            assert len(rows_at(t))==2
        print("F05_MP_TOTAL_RACES",90,flush=True)
        clear()
        with SessionLocal() as db:
            ref=slot(db,root,root,t)
            db.add(models.Appointment(patient_name="LEGACY NULL",employer_id=root,
                                      datetime_start=datetime.fromisoformat(t),
                                      duration_minutes=30,praticien_id=None,
                                      status=models.AppointmentStatus.PREVU,
                                      scheduling_type=models.SchedulingType.EXACT_TIME))
            db.commit()
        legacy=request(18062,"POST","/lab/pc/create","A",{"slot_ref":ref})
        assert legacy[0]==409 and len(rows_at(t,root))==1,legacy
        print("F05_MP_LEGACY_NULL",legacy[0],"ROWS",len(rows_at(t,root)),flush=True)
        for inactive in (models.AppointmentStatus.REFUSE,models.AppointmentStatus.EXPIRE):
            clear()
            with SessionLocal() as db:
                db.add(models.Appointment(patient_name="INACTIVE",employer_id=root,
                           datetime_start=datetime.fromisoformat(t),duration_minutes=30,
                           praticien_id=None,status=inactive,
                           scheduling_type=models.SchedulingType.EXACT_TIME))
                db.commit()
            allowed=request(*book(t))
            assert allowed[0]==200 and len(rows_at(t,root))==2,(inactive,allowed)
            print("F05_MP_INACTIVE",inactive.value,"HTTP",allowed[0],flush=True)
        # Controlled PostgreSQL 40P01: two separate sessions, inverted locks.
        # Verify failed transaction rollback releases its advisory lock.
        sync=Barrier(2)
        def deadlock_worker(first,second):
            from sqlalchemy.exc import OperationalError
            with SessionLocal() as db:
                db.execute(text("SELECT pg_advisory_xact_lock(:k)"),{"k":first})
                sync.wait(timeout=8)
                try:
                    db.execute(text("SELECT pg_advisory_xact_lock(:k)"),{"k":second})
                    outcome="ACQUIRED"
                except OperationalError as exc:
                    outcome=getattr(exc.orig,"sqlstate","UNKNOWN")
                finally:
                    db.rollback()
                return outcome
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(deadlock_worker,90107,90108),
                     pool.submit(deadlock_worker,90108,90107)]
            outcomes=[f.result(timeout=18) for f in futures]
        assert sorted(outcomes)==["40P01","ACQUIRED"],outcomes
        print("F05_MP_DEADLOCK",outcomes,"ROLLBACK_RELEASED",flush=True)
        # Authenticated HTTP replay: unlike earlier races, these requests go
        # through the unchanged backend.auth.get_current_user JWT verification.
        # Real product local-login endpoint issues bearer tokens after checking
        # synthetic bcrypt password hashes against actual PostgreSQL users.
        with httpx.Client(timeout=20) as cli:
            login_a=cli.post("http://127.0.0.1:18061/real-auth/api/auth/login",
                        data={"username":"f05-a@example.invalid","password":LAB_PASSWORD})
            login_c=cli.post("http://127.0.0.1:18062/real-auth/api/auth/login",
                        data={"username":"f05-c@example.invalid","password":LAB_PASSWORD})
        assert login_a.status_code==200 and login_c.status_code==200,(
            "REAL_LOGIN_FAILURE",login_a.status_code,login_c.status_code,
            login_a.text[:110],login_c.text[:110])
        access_token=login_a.json()["access_token"]
        other_token=login_c.json()["access_token"]
        print("F05_MP_REAL_PASSWORD_LOGIN",login_a.status_code,login_c.status_code,
              "PASSWORD_NOT_LOGGED",flush=True)
        clear()
        target="http://127.0.0.1:18061/real-auth/api/appointments/"
        with httpx.Client(timeout=15) as client:
            missing=client.post(target,json=book(t)[4])
            forged=client.post(target,json=book(t)[4],
                               headers={"Authorization":"Bearer malformed"})
        assert missing.status_code==401 and forged.status_code==401,(
            "REAL_AUTH_REJECT",missing.status_code,forged.status_code)
        signed_barrier=Barrier(2)
        def signed_request(port,token):
            signed_barrier.wait(timeout=8)
            with httpx.Client(timeout=18) as cli:
                response=cli.post(
                    f"http://127.0.0.1:{port}/real-auth/api/appointments/",
                    json=book(t)[4],
                    headers={"Authorization":f"Bearer {token}"})
                return response.status_code,response.text[:150]
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1=pool.submit(signed_request,18061,access_token)
            f2=pool.submit(signed_request,18062,access_token)
            signed=[f1.result(timeout=22),f2.result(timeout=22)]
        assert sorted(v[0] for v in signed)==[200,409],signed
        assert len(rows_at(t,root))==1
        with httpx.Client(timeout=18) as cli:
            second_tenant=cli.post(
                "http://127.0.0.1:18062/real-auth/api/appointments/",
                json=book(t)[4],headers={"Authorization":f"Bearer {other_token}"})
        assert second_tenant.status_code==200,second_tenant.text[:160]
        assert len(rows_at(t))==2
        print("F05_MP_REAL_JWT_HTTP",{
             "missing":missing.status_code, "malformed":forged.status_code,
             "race":sorted(v[0] for v in signed),
             "other_tenant":second_tenant.status_code},
             "SQL",len(rows_at(t)),"AUTH_IMPL","backend.routers.auth.get_current_user",
             "TOKEN_ORIGIN","REAL_LOCAL_LOGIN_SYNTHETIC_PASSWORD",
             flush=True)
        with database.engine.connect() as con:
            protected_id=con.scalar(text(
                "SELECT id FROM appointments WHERE employer_id=:employer "
                "AND datetime_start=:dt LIMIT 1"),
                {"employer":root,"dt":datetime.fromisoformat(t)})
        with httpx.Client(timeout=18) as cli:
            denied=cli.put(
                f"http://127.0.0.1:18062/real-auth/api/appointments/{protected_id}",
                json={"datetime_start":"2026-11-02T11:00:00"},
                headers={"Authorization":f"Bearer {other_token}"})
        assert denied.status_code==404,("REAL_AUTH_TENANT_DENIAL",denied.status_code,denied.text[:150])
        print("F05_MP_REAL_JWT_OTHER_TENANT_UPDATE",denied.status_code,flush=True)
        print("F05_MP_AUTH_MODE","HEADER_OVERRIDE_FOR_80_RACES;REAL_LOGIN_JWT_FOR_1_RACE",flush=True)
        print("F05_MP_PC_MODE","DIRECT_DOMAIN_ADAPTER_NOT_REMOTE_RECEIPT",flush=True)
        print("F05_MP_RESULT","LIMITED_PASS_NOT_F05_CERTIFICATION",flush=True)
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill()

if __name__ == "__main__":
    exercise()
