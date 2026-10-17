"""F05 synthetic PostgreSQL multiprocess HTTP verification; NOT patient-device auth certification.

Never mounted in backend.main. Must run only against CI's disposable dc_agenda_synthetic.
"""
import os

def _guard():
    assert os.environ.get("ENVIRONMENT") == "test"
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    assert os.environ.get("PG_CERT_LAB") == "1"
    url = os.environ.get("DATABASE_URL", "")
    assert url.startswith("postgresql+psycopg://") and url.endswith("/dc_agenda_synthetic")
_guard()

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend import database, models
from backend.routers import appointments, auth, bot, frontdesk
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionIdentity,
    PatientCompanionAgendaSlot, PatientCompanionAppointmentRef,
)
from backend.services import patient_companion_agenda as pc_agenda

app = FastAPI(title="F05 synthetic-only multiprocess probe")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(appointments.router, prefix="/api/appointments")
app.include_router(frontdesk.router, prefix="/api")
app.include_router(bot.router, prefix="/api/bot")

class PcLabRequest(BaseModel):
    access_id: int
    slot_ref: str
    appointment_ref: str | None = None

@app.post("/_f05_lab/pc/{operation}")
def pc_lab_write(
    operation: str, req: PcLabRequest,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(auth.get_current_user),
):
    # Substitution explicitly lab-only: REAL staff JWT + real PC domain service,
    # NOT the Patient Companion JWE/device-authenticated remote transport.
    if not auth.has_permission(user, "agenda"):
        raise HTTPException(403)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.id == req.access_id,
        PatientCompanionAccess.employer_id == user.get_employer_id(),
    ).first()
    if access is None:
        raise HTTPException(404)
    if operation == "create":
        outcome = pc_agenda.create_appointment(db, access, {"slot_ref": req.slot_ref})
    elif operation == "reschedule" and req.appointment_ref:
        outcome = pc_agenda.reschedule_appointment(
            db, access, {"slot_ref": req.slot_ref, "appointment_ref": req.appointment_ref}
        )
    else:
        raise HTTPException(422)
    db.commit()
    if outcome.status != "ACCEPTED":
        raise HTTPException(409, outcome.response)
    return outcome.response

def _runner():
    import sys
    import uuid
    import socket
    import subprocess
    import time
    from datetime import datetime, timedelta
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    import httpx
    from backend.security import get_password_hash

    assert database.engine.dialect.name == "postgresql"
    with database.engine.connect() as c:
        assert c.scalar(text("SELECT current_database()")) == "dc_agenda_synthetic"
        assert "PostgreSQL 16" in c.scalar(text("SELECT version()"))
    models.Base.metadata.create_all(bind=database.engine)
    Session = database.SessionLocal
    password = "F05_LAB_PASSWORD_ONLY"
    suffix = uuid.uuid4().hex[:9]
    def user(db, name, employer=None):
        row = models.User(
            email=f"f05-{name}-{suffix}@example.invalid",
            hashed_password=get_password_hash(password),
            role=models.UserRole.DENTISTE,
            is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
            employer_id=employer,
        )
        db.add(row);db.flush()
        return row
    with Session() as db:
        owner = user(db, "owner")
        colleague = user(db, "colleague", owner.id)
        other = user(db, "other")
        chair = models.AgendaResource(
            employer_id=owner.id, name="F05 SYNTHETIC CHAIR",
            resource_type="CHAIR", is_active=True,
        )
        db.add(chair)
        patient = models.Patient(
            numero_dossier=f"F05-{suffix}", nom="SYNTHETIC", prenom="F05",
            date_naissance=datetime(2010,1,1), sexe="F", employer_id=owner.id,
        )
        identity = PatientCompanionIdentity(provider="local_bridge", subject=f"f05:{suffix}")
        db.add_all([patient,identity]);db.flush()
        access = PatientCompanionAccess(
            public_id=str(uuid.uuid4()), employer_id=owner.id,
            patient_id=patient.id, identity_id=identity.id,
            relationship_type="SELF",
        )
        db.add(access);db.flush()
        owner_id, colleague_id, other_id, chair_id = owner.id, colleague.id, other.id, chair.id
        patient_id, access_id = patient.id, access.id
        db.commit()

    def free_port():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            return sock.getsockname()[1]
    ports = [free_port(), free_port()]
    assert ports[0] != ports[1]
    servers = []
    try:
        for port in ports:
            servers.append(subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "scripts.verification.lot07_07a_f05_multiprocess:app",
                 "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
                env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
            ))
        urls = [f"http://127.0.0.1:{p}" for p in ports]
        for proc, url in zip(servers, urls):
            for _ in range(120):
                if proc.poll() is not None:
                    raise AssertionError(f"FastAPI process exited early: {proc.returncode}")
                try:
                    if httpx.get(url+"/openapi.json", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.1)
            else:
                raise AssertionError(f"FastAPI failed to start: {url}")

        def token(url, email):
            r = httpx.post(url+"/api/auth/login",
                           data={"username":email,"password":password},timeout=8)
            assert r.status_code == 200, (r.status_code,r.text[:120])
            return r.json()["access_token"]
        owner_tokens = [token(u,f"f05-owner-{suffix}@example.invalid") for u in urls]
        colleague_token = token(urls[1],f"f05-colleague-{suffix}@example.invalid")
        other_token = token(urls[1],f"f05-other-{suffix}@example.invalid")
        print("F05_REAL_AUTH", "JWT_LOGIN_3_ACCOUNTS_ACROSS_2_PROCESSES", flush=True)
        print("F05_WORKERS", len(servers), "OS_PIDS", [p.pid for p in servers], flush=True)

        def api(port_idx, method, path, token_value, body, barrier=None):
            if barrier:
                barrier.wait(timeout=10)
            with httpx.Client(timeout=25) as client:
                r = client.request(method, urls[port_idx]+path,
                                   headers={"Authorization": f"Bearer {token_value}"}, json=body)
                return r.status_code, r.text[:2048]
        def race(first, second):
            barrier = Barrier(2)
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(api,*op,barrier) for op in (first,second)]
                return [f.result(timeout=35) for f in futures]
        def post(port, start, who=None, resource=None, practitioner=None):
            return (port,"POST","/api/appointments/",who or owner_tokens[port],
                    {"patient_name":"F05 SYNTHETIC","datetime_start":start,
                     "duration_minutes":30,"praticien_id":practitioner,
                     "resource_id":resource})
        def frontdesk(port,start):
            return (port,"POST","/api/frontdesk/appointment-request",
                    owner_tokens[port],
                    {"first_name":"F05","last_name":"SYNTHETIC",
                     "requested_start":start,"duration_minutes":30})
        def bot_pending(start):
            with Session() as db:
                session=models.BotSession(
                    employer_id=owner_id,user_id=owner_id,
                    title="F05 SYNTHETIC multiprocess",
                )
                db.add(session);db.flush()
                pending=models.BotPendingAction(
                    session_id=session.id,user_id=owner_id,employer_id=owner_id,
                    action_type="CREATE_APPOINTMENT",
                    params_json={"patient_id":None,"patient_name":"F05 SYNTHETIC BOT",
                                 "datetime_start":start,"duration_minutes":30,
                                 "motif":"F05 only"},
                    status="pending",expires_at=datetime.utcnow()+timedelta(minutes=10),
                )
                db.add(pending);db.flush()
                action_id=pending.id
                db.commit()
            return (1,"POST","/api/bot/execute",owner_tokens[1],
                    {"pending_action_id":action_id})
        def counts(t):
            with Session() as db:
                rows=db.execute(text(
                    "SELECT employer_id,praticien_id,resource_id,status "
                    "FROM appointments WHERE datetime_start=:start AND deleted_at IS NULL"
                ),{"start":datetime.fromisoformat(t)}).all()
                return [(int(a),p,r,str(s)) for a,p,r,s in rows]
        def reset():
            with Session() as db:
                db.execute(text("DELETE FROM patient_companion_appointment_refs"))
                db.execute(text("DELETE FROM patient_companion_agenda_slots"))
                db.execute(text("DELETE FROM appointments"))
                db.commit()
        def verify(case, results, expected, start, active_count):
            codes=sorted(s for s,_ in results)
            actual=counts(start)
            active=[r for r in actual if "ANNUL" not in r[3] and "REFUS" not in r[3] and "EXPIR" not in r[3]]
            assert codes == sorted(expected),(case,codes,expected,results)
            assert len(active)==active_count,(case,active)
            print("F05_RACE",case,"HTTP",codes,"SQL_TOTAL",len(actual),
                  "SQL_ACTIVE",len(active),flush=True)

        rounds=5
        for i in range(rounds):
            t=f"2030-01-02T{10+i:02}:00:00"
            reset()
            results=race(post(0,t),post(1,t))
            verify("AGENDA_VS_AGENDA",results,[200,409],t,1)
            reset()
            results=race(post(0,t),frontdesk(1,t))
            verify("AGENDA_VS_FRONTDESK_REQUEST",results,[200,409],t,1)
            reset()
            results=race(frontdesk(0,t),frontdesk(1,t))
            verify("FRONTDESK_REQUEST_VS_REQUEST",results,[200,409],t,1)
            reset()
            results=race(post(0,t),bot_pending(t))
            verify("AGENDA_VS_BOT",results,[200,409],t,1)
            reset()
            results=race(post(0,t,resource=chair_id),
                         post(1,t,who=colleague_token,practitioner=colleague_id,resource=chair_id))
            verify("SHARED_RESOURCE",results,[200,409],t,1)
            reset()
            results=race(post(0,t),post(1,t,who=other_token,practitioner=other_id))
            verify("CABINET_ISOLATION",results,[200,200],t,2)
            reset()
            with Session() as db:
                slot=PatientCompanionAgendaSlot(
                    employer_id=owner_id,practitioner_id=owner_id,
                    datetime_start=datetime.fromisoformat(t),duration_minutes=30,
                    expires_at=datetime.utcnow()+timedelta(minutes=15))
                db.add(slot);db.commit()
                slot_ref=slot.public_id
            pc_create=(1,"POST","/_f05_lab/pc/create",owner_tokens[1],
                       {"access_id":access_id,"slot_ref":slot_ref})
            results=race(post(0,t),pc_create)
            verify("AGENDA_VS_PC_CREATE_LAB_WRAPPER",results,[200,409],t,1)
            with Session() as db:
                s=db.query(PatientCompanionAgendaSlot).filter_by(public_id=slot_ref).one()
                assert (s.consumed_at is not None) == (results[1][0]==200)
            reset()
            with Session() as db:
                bot_slot=PatientCompanionAgendaSlot(
                    employer_id=owner_id,practitioner_id=owner_id,
                    datetime_start=datetime.fromisoformat(t),duration_minutes=30,
                    expires_at=datetime.utcnow()+timedelta(minutes=15))
                db.add(bot_slot);db.commit()
                bot_slot_ref=bot_slot.public_id
            pc_bot=(0,"POST","/_f05_lab/pc/create",owner_tokens[0],
                    {"access_id":access_id,"slot_ref":bot_slot_ref})
            results=race(bot_pending(t),pc_bot)
            verify("BOT_VS_PC_CREATE_LAB_WRAPPER",results,[200,409],t,1)
            reset()
            with Session() as db:
                source=models.Appointment(
                    patient_id=patient_id,employer_id=owner_id,
                    praticien_id=owner_id,datetime_start=datetime(2030,1,2,8,0),
                    duration_minutes=30,status=models.AppointmentStatus.CONFIRME,
                    scheduling_type=models.SchedulingType.EXACT_TIME)
                db.add(source);db.flush()
                ref=PatientCompanionAppointmentRef(
                    public_id=str(uuid.uuid4()), employer_id=owner_id,
                    patient_id=patient_id, appointment_id=source.id)
                slot=PatientCompanionAgendaSlot(
                    employer_id=owner_id,practitioner_id=owner_id,
                    datetime_start=datetime.fromisoformat(t),duration_minutes=30,
                    expires_at=datetime.utcnow()+timedelta(minutes=15))
                db.add_all([ref,slot]);db.commit()
                pc_ref,slot_ref=ref.public_id,slot.public_id
            pc_resch=(1,"POST","/_f05_lab/pc/reschedule",owner_tokens[1],
                      {"access_id":access_id,"appointment_ref":pc_ref,"slot_ref":slot_ref})
            results=race(post(0,t),pc_resch)
            verify("AGENDA_VS_PC_RESCHEDULE_LAB_WRAPPER",results,[200,409],t,1)
            with Session() as db:
                s=db.query(PatientCompanionAgendaSlot).filter_by(public_id=slot_ref).one()
                assert (s.consumed_at is not None)==(results[1][0]==200)
        # Frontdesk CONFIRM must race with other producers after REQUEST exists.
        reset()
        t="2030-01-02T16:00:00"
        import json
        created=api(*frontdesk(0,t))
        assert created[0]==200,created
        request_id=json.loads(created[1])["id"]
        confirm=(1,"POST",f"/api/appointments/{request_id}/confirm",owner_tokens[1],{})
        results=race(confirm,post(0,t))
        verify("FRONTDESK_CONFIRM_VS_AGENDA",results,[200,409],t,1)
        reset()
        created=api(*frontdesk(0,t))
        assert created[0]==200,created
        request_id=json.loads(created[1])["id"]
        confirm=(0,"POST",f"/api/appointments/{request_id}/confirm",owner_tokens[0],{})
        results=race(confirm,bot_pending(t))
        verify("FRONTDESK_CONFIRM_VS_BOT",results,[200,409],t,1)
        # Confirm/reject and confirm/expire are mutually exclusive transitions.
        # No stale read may demote a confirmed appointment after COMMIT.
        for verb, status_if_competitor_wins in (("reject","REFUSE"),("expire","EXPIRE")):
            reset()
            created=api(*frontdesk(0,t))
            assert created[0]==200,created
            request_id=json.loads(created[1])["id"]
            confirm=(0,"POST",f"/api/appointments/{request_id}/confirm",owner_tokens[0],{})
            competitor=(1,"POST",f"/api/appointments/{request_id}/{verb}",owner_tokens[1],{})
            results=race(confirm,competitor)
            assert sorted(code for code,_ in results)==[200,409],(verb,results)
            with Session() as db:
                final=db.execute(text("SELECT status FROM appointments WHERE id=:id"),
                                 {"id":request_id}).scalar_one()
            target="CONFIRME" if results[0][0]==200 else status_if_competitor_wins
            assert final==target,(verb,results,final,target)
            print("F05_STATUS_RACE","CONFIRM_VS_"+verb.upper(),
                  "HTTP",sorted(x[0] for x in results),"PERSISTED",final,flush=True)
        # Frontdesk expiry and HTTP confirmation via a second FastAPI PID.
        reset()
        t="2030-01-02T17:00:00"
        created=api(*frontdesk(0,t))
        assert created[0]==200,created
        import json
        request_id=json.loads(created[1])["id"]
        with Session() as db:
            db.execute(text("UPDATE appointments SET expires_at=:expiry WHERE id=:id"),
                       {"expiry":datetime.utcnow()-timedelta(seconds=1),"id":request_id})
            db.commit()
        confirm=(1,"POST",f"/api/appointments/{request_id}/confirm",owner_tokens[1],{})
        results=race(confirm,post(0,t))
        assert sorted(s for s,_ in results)==[200,410],results
        with Session() as db:
            rows=db.execute(text("SELECT id,status FROM appointments WHERE employer_id=:e AND datetime_start=:t"),
                            {"e":owner_id,"t":datetime.fromisoformat(t)}).all()
            assert len(rows)==2,rows
        print("F05_EXPIRED_REQUEST_CONFIRM", "HTTP",sorted(s for s,_ in results),
              "SQL_ROWS",len(rows),flush=True)
        print("F05_MULTIPROCESS_RACES",rounds*9+5,flush=True)
        print("F05_PC_AUTH","SUBSTITUTED_STAFF_JWT_LAB_WRAPPER_NOT_DEVICE_JWE",flush=True)
        print("F05_RECEIPTS","UNTESTED_BY_THIS_LAB",flush=True)
    finally:
        for proc in servers:
            if proc.poll() is None:
                proc.terminate()
        for proc in servers:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

if __name__ == "__main__":
    _runner()
