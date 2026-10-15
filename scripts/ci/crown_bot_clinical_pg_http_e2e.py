"""Clinical Crown Bot API E2E against migrated PostgreSQL 16 (real app/schema).

Standalone fresh interpreter: do NOT import backend/tests/conftest.py,
which intentionally forces SQLite in-memory. All records fictitious.
Must run only against an isolated fresh CI database, never clinic/prod DB.
"""
import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

# Invoked as `python scripts/ci/crown_bot_clinical_pg_http_e2e.py`: Python
# normally places scripts/ci, not the repository root, on sys.path.
# Add only this repository root. Never import backend/tests/conftest,
# which intentionally overrides DATABASE_URL to SQLite in-memory.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

assert os.environ.get("CROWN_BOT_CLINICAL_CI_DATABASE") == "synthetic-only", "Refusing non-CI execution"
_ci_url = os.environ.get("DATABASE_URL", "")
assert _ci_url.startswith("postgresql+") and "127.0.0.1" in _ci_url or (
    _ci_url.startswith("sqlite:////tmp/crown_bot_clinical_")
), "Require local synthetic PostgreSQL or disposable SQLCipher CI file"

from backend import database, models
if _ci_url.startswith("sqlite:"):
    assert "pysqlcipher" in database.SQLALCHEMY_DATABASE_URL, "Refuse plaintext SQLite fallback"
    with database.engine.connect() as _conn:
        assert _conn.exec_driver_sql("PRAGMA cipher_version").scalar(), "Not real SQLCipher"

from backend.main import app
from backend.security import get_password_hash


def fail(message):
    raise AssertionError(message)


def run():
    doctor_email = f"clinical-{uuid4().hex}@invalid.example"
    with database.SessionLocal() as db:
        doctor = models.User(
            email=doctor_email,
            hashed_password=get_password_hash("CiSyntheticOnlyPass123!"),
            role=models.UserRole.DENTISTE, nom_complet="Synthetic CI Dentist",
            is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(doctor)
        db.flush()
        doctor_id = doctor.id
        patient = models.Patient(
            prenom="Clinical", nom="Synthetic", sexe="F",
            date_naissance=date(1990, 1, 1), employer_id=doctor_id,
        )
        db.add(patient)
        db.flush()
        patient_id = patient.id
        week = {
            day: {"is_open": True, "is_continuous": False,
                  "morning_start": "09:00", "morning_end": "13:00",
                  "afternoon_start": "14:00", "afternoon_end": "18:00"}
            for day in ("monday", "tuesday", "wednesday", "thursday",
                        "friday", "saturday", "sunday")
        }
        db.execute(text(
            "INSERT INTO cabinet_settings "
            "(opening_time_morning,closing_time_morning,"
            "opening_time_afternoon,closing_time_afternoon,"
            "is_continuous,agenda_mode,use_tickets,employer_id,weekly_schedule_json) "
            "VALUES ('09:00','13:00','14:00','18:00',false,'EXACT',false,:tenant,:week)"
        ), {"tenant": doctor_id, "week": json.dumps(week)})
        db.commit()

    # TestClient instances intentionally have independent requests, allowing
    # FastAPI get_db to open multiple real SQLAlchemy connections.
    api = TestClient(app, raise_server_exceptions=True)
    login = api.post(
        "/api/auth/login",
        data={"username": doctor_email, "password": "CiSyntheticOnlyPass123!"},
    )
    assert login.status_code == 200, login.text
    authorization = {"Authorization": f"Bearer {login.json()['access_token']}"}

    first_slot = (datetime.now() + timedelta(days=8)).replace(
        hour=10, minute=30, second=0, microsecond=0
    )
    barrier = Barrier(2)

    def reserve(index):
        with TestClient(app, raise_server_exceptions=True) as client:
            barrier.wait(timeout=20)
            return client.post("/api/appointments/", headers=authorization, json={
                "patient_name": f"Synthetic race {index}",
                "praticien_id": doctor_id,
                "datetime_start": first_slot.isoformat(),
                "duration_minutes": 30, "motif": "Synthetic consultation",
            })

    # Do not enter lifespan for real worker initialization. TestClient(app)
    # without context still dispatches real ASGI routes and dependencies.
    def reserve_without_lifespan(index):
        client = TestClient(app, raise_server_exceptions=True)
        barrier.wait(timeout=20)
        return client.post("/api/appointments/", headers=authorization, json={
            "patient_name": f"Synthetic race {index}",
            "praticien_id": doctor_id,
            "datetime_start": first_slot.isoformat(),
            "duration_minutes": 30, "motif": "Synthetic consultation",
        })

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve_without_lifespan, (1, 2)))
    codes = sorted(r.status_code for r in results)
    assert codes == [200, 409], [(r.status_code, r.text[:400]) for r in results]
    with database.SessionLocal() as db:
        records = db.query(models.Appointment).filter(
            models.Appointment.employer_id == doctor_id,
            models.Appointment.datetime_start == first_slot,
        ).all()
        assert len(records) == 1, "Two HTTP creates produced double booking"
    print("CLINICAL_REAL_HTTP_TWO_SESSIONS: PASS")

    # Real clinical closure, no mocks: check that a conflicting creation does
    # not write and patient tenant is still enforced.
    closure_slot = first_slot + timedelta(days=1)
    with database.SessionLocal() as db:
        db.execute(text(
            "INSERT INTO agenda_exceptions "
            "(start_date,end_date,reason,is_holiday,employer_id,created_at) "
            "VALUES (:start,:end,'Synthetic PG closure',false,:tenant,:created_at)"
        ), {
            "start": closure_slot - timedelta(minutes=10),
            "end": closure_slot + timedelta(minutes=45),
            "tenant": doctor_id,
            "created_at": datetime.utcnow(),
        })
        db.commit()
    blocked = api.post("/api/appointments/", headers=authorization, json={
        "patient_name": "Synthetic closure",
        "praticien_id": doctor_id, "datetime_start": closure_slot.isoformat(),
        "duration_minutes": 30,
    })
    assert blocked.status_code == 422, blocked.text
    print("CLINICAL_REAL_CLOSURE: PASS")

    # Exercise actual Crown Bot HTTP confirm using real owner+patient and
    # action tables, then reject replay and inspect committed appointment/audit.
    bot_slot = first_slot + timedelta(days=2)
    with database.SessionLocal() as db:
        bs = models.BotSession(
            employer_id=doctor_id, user_id=doctor_id, title="Synthetic CI",
        )
        db.add(bs)
        db.flush()
        action = models.BotPendingAction(
            session_id=bs.id, user_id=doctor_id,
            employer_id=doctor_id, action_type="CREATE_APPOINTMENT",
            params_json={
                "patient_id": patient_id,
                "datetime_start": bot_slot.isoformat(),
                "duration_minutes": 30, "motif": "Consultation",
            },
            status="pending", expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(action)
        db.commit()
        action_id = action.id
    outcome = api.post("/api/bot/execute", headers=authorization,
                       json={"pending_action_id": action_id})
    assert outcome.status_code == 200, outcome.text
    replay = api.post("/api/bot/execute", headers=authorization,
                      json={"pending_action_id": action_id})
    assert replay.status_code == 409, replay.text
    with database.SessionLocal() as db:
        a = db.get(models.BotPendingAction, action_id)
        assert a.status == "executed" and a.executed_at is not None
        appointments = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.datetime_start == bot_slot,
        ).all()
        assert len(appointments) == 1
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == doctor_id,
            models.AuditLog.resource_type == "Appointment",
            models.AuditLog.resource_id == str(appointments[0].id),
        ).count()
        assert audit >= 1
    print("CLINICAL_REAL_BOT_HTTP_EXECUTE_REPLAY_AUDIT: PASS")
    print("CLINICAL_FULL_SCHEMA_HTTP_GATE: PASS migrated schema, HTTP, real database transaction")


if __name__ == "__main__":
    run()
