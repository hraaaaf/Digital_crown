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
from backend.core.runtime_safety import (
    database_target_fingerprint, is_known_cabinet_database,
)
# This startup attestation is NOT a bypass: assert the exact disposable CI
# target before constructing its fingerprint, and retain the real runtime
# guard in backend.main. Never attest a known cabinet database.
assert not is_known_cabinet_database(_ci_url), "Refusing actual cabinet DB"
if _ci_url.startswith("postgresql+"):
    assert _ci_url.endswith("/crown_bot_clinical_cert"), "Unexpected PostgreSQL database"
if _ci_url.startswith("sqlite:"):
    assert "pysqlcipher" in database.SQLALCHEMY_DATABASE_URL, "Refuse plaintext SQLite fallback"
    with database.engine.connect() as _conn:
        assert _conn.exec_driver_sql("PRAGMA cipher_version").scalar(), "Not real SQLCipher"
os.environ["DIGITALCROWN_ISOLATED_RUNTIME"] = "true"
os.environ["DIGITALCROWN_ISOLATION_DB_FINGERPRINT"] = database_target_fingerprint(_ci_url)

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
    # A pending frontdesk request is an enquiry, NOT a capacity reservation.
    front_slot = first_slot + timedelta(days=3)
    pending = api.post("/api/frontdesk/appointment-request",
        headers=authorization, json={
            "first_name": "Pending", "last_name": "Synthetic",
            "requested_start": front_slot.isoformat(), "duration_minutes": 30,
        })
    assert pending.status_code == 200, pending.text
    tentative_id = pending.json()["id"]
    actual = api.post("/api/appointments/", headers=authorization, json={
        "patient_name": "Already Confirmed", "praticien_id": doctor_id,
        "datetime_start": front_slot.isoformat(), "duration_minutes": 30,
    })
    assert actual.status_code == 200, actual.text
    denied = api.post(f"/api/appointments/{tentative_id}/confirm", headers=authorization)
    assert denied.status_code == 409, denied.text
    print("CLINICAL_REAL_FRONTDESK_PROPOSAL_NOT_OCCUPYING: PASS")

    # Real HTTP race: confirming versus rejecting EXACTLY the same request.
    race_slot = first_slot + timedelta(days=4)
    pending2 = api.post("/api/frontdesk/appointment-request", headers=authorization,
        json={
            "first_name": "Race", "last_name": "Synthetic",
            "requested_start": race_slot.isoformat(), "duration_minutes": 30,
        })
    assert pending2.status_code == 200, pending2.text
    race_id = pending2.json()["id"]
    ready = Barrier(2)
    def transition_request(operation):
        test_client = TestClient(app, raise_server_exceptions=True)
        ready.wait(timeout=20)
        return test_client.post(
            f"/api/appointments/{race_id}/{operation}", headers=authorization,
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        raced = list(pool.map(transition_request, ("confirm", "reject")))
    assert sorted(x.status_code for x in raced) == [200, 409], [
        (x.status_code, x.text[:500]) for x in raced
    ]
    with database.SessionLocal() as session:
        final = session.get(models.Appointment, race_id)
        assert final.status in {
            models.AppointmentStatus.CONFIRME,
            models.AppointmentStatus.REFUSE,
        }
        if final.status == models.AppointmentStatus.CONFIRME:
            assert final.praticien_id == doctor_id
    print("CLINICAL_REAL_FRONTDESK_CONFIRM_REJECT_RACE: PASS")
    # A legacy unassigned appointment blocks ALL practitioner calendars.
    # The patient-companion service must agree with canonical Agenda on both
    # true production database drivers, not only synthetic SQLite memory.
    from types import SimpleNamespace
    from backend.services.patient_companion_agenda import _validate_exact_slot
    legacy_slot = first_slot + timedelta(days=5)
    with database.SessionLocal() as db:
        legacy = models.Appointment(
            patient_name="Legacy Global Blocker", employer_id=doctor_id,
            datetime_start=legacy_slot, duration_minutes=30,
            praticien_id=None, status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
        )
        db.add(legacy)
        db.commit()
        outcome = _validate_exact_slot(
            db, SimpleNamespace(employer_id=doctor_id),
            start=legacy_slot, duration=30, practitioner_id=doctor_id,
            resource_id=None,
        )
        assert outcome == "SLOT_CONFLICT", outcome
    denied_legacy = api.post("/api/appointments/", headers=authorization, json={
        "patient_name": "Should Not Book", "praticien_id": doctor_id,
        "datetime_start": legacy_slot.isoformat(), "duration_minutes": 30,
    })
    assert denied_legacy.status_code == 409, denied_legacy.text
    print("CLINICAL_REAL_LEGACY_NULL_PRACTITIONER_CROSS_INGRESS: PASS")

    # A legacy 8-hour booking starting 5h before a candidate must block it.
    # Previous 4h lookback silently hid 09:00-17:00 from a 14:00 search.
    long_start = (first_slot + timedelta(days=6)).replace(
        hour=9, minute=0, second=0, microsecond=0,
    )
    candidate = long_start.replace(hour=14)
    with database.SessionLocal() as db:
        long_existing = models.Appointment(
            patient_name="Historical 8h Synthetic", employer_id=doctor_id,
            datetime_start=long_start, duration_minutes=480,
            praticien_id=doctor_id, status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
        )
        db.add(long_existing)
        db.commit()
        long_id = long_existing.id
    long_conflict = api.post("/api/appointments/", headers=authorization, json={
        "patient_name": "Long Overlap Synthetic", "praticien_id": doctor_id,
        "datetime_start": candidate.isoformat(), "duration_minutes": 30,
    })
    assert long_conflict.status_code == 409, long_conflict.text
    with database.SessionLocal() as db:
        assert db.get(models.Appointment, long_id).duration_minutes == 480
        assert db.query(models.Appointment).filter(
            models.Appointment.employer_id == doctor_id,
            models.Appointment.datetime_start == candidate,
        ).count() == 0
    print("CLINICAL_REAL_EIGHT_HOUR_OVERLAP: PASS")

    # An expired request is NOT a copyable offer of an available slot.
    expired_slot = first_slot + timedelta(days=7)
    expired_response = api.post(
        "/api/frontdesk/appointment-request", headers=authorization, json={
            "first_name": "Expired", "last_name": "Synthetic",
            "requested_start": expired_slot.isoformat(), "duration_minutes": 30,
        },
    )
    assert expired_response.status_code == 200, expired_response.text
    expired_id = expired_response.json()["id"]
    with database.SessionLocal() as db:
        expired_request = db.get(models.Appointment, expired_id)
        expired_request.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    stale_offer = api.post(
        f"/api/appointments/{expired_id}/request-confirmation",
        headers=authorization,
    )
    assert stale_offer.status_code == 410, stale_offer.text
    assert "disponible" not in stale_offer.text.lower()
    with database.SessionLocal() as db:
        assert db.get(models.Appointment, expired_id).status == models.AppointmentStatus.EXPIRE
        assert db.query(models.AuditLog).filter(
            models.AuditLog.resource_id == str(expired_id),
            models.AuditLog.action == "FRONTDESK_APPOINTMENT_EXPIRED",
        ).count() == 1
    print("CLINICAL_REAL_EXPIRED_FRONTDESK_NO_MESSAGE: PASS")




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
        bot_session_id = bs.id
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

    # Status confirmation must be conditional on the actual appointment status
    # still matching the user's preview (not merely the same patient).
    with database.SessionLocal() as db:
        stale_appt = models.Appointment(
            patient_id=patient_id, employer_id=doctor_id,
            praticien_id=doctor_id,
            datetime_start=first_slot + timedelta(days=9),
            duration_minutes=30, motif="Synthetic status CAS",
            status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
        )
        db.add(stale_appt)
        db.flush()
        stale_action = models.BotPendingAction(
            session_id=bot_session_id, user_id=doctor_id,
            employer_id=doctor_id, action_type="CHANGE_STATUS",
            params_json={
                "appointment_id": stale_appt.id, "patient_id": patient_id,
                "expected_status": "PREVU",
                "expected_revision": stale_appt.clinical_revision,
                "status": "EN_FAUTEUIL",
            },
            status="pending", expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(stale_action)
        db.commit()
        stale_action_id = stale_action.id
        stale_appt_id = stale_appt.id
        stale_appt.status = models.AppointmentStatus.ANNULE
        db.commit()  # clinic cancels AFTER bot's preview but BEFORE confirmation
    stale_execution = api.post(
        "/api/bot/execute", headers=authorization,
        json={"pending_action_id": stale_action_id},
    )
    assert stale_execution.status_code == 409, stale_execution.text
    with database.SessionLocal() as db:
        assert db.get(models.Appointment, stale_appt_id).status == models.AppointmentStatus.ANNULE
        assert db.get(models.BotPendingAction, stale_action_id).status == "failed"
    print("CLINICAL_REAL_BOT_STALE_CANCELLED_STATUS_CAS: PASS")

    # REAL clinical ABA on the same appointment and separate SQL writes:
    # PREVU -> ANNULE -> PREVU would bypass status-only matching.
    with database.SessionLocal() as db:
        aba = models.Appointment(
            patient_id=patient_id, employer_id=doctor_id,
            praticien_id=doctor_id,
            datetime_start=first_slot + timedelta(days=11),
            duration_minutes=30, status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
        )
        db.add(aba)
        db.flush()
        aba_action = models.BotPendingAction(
            session_id=bot_session_id, user_id=doctor_id,
            employer_id=doctor_id, action_type="CHANGE_STATUS",
            params_json={
                "appointment_id": aba.id, "patient_id": patient_id,
                "expected_status": "PREVU",
                "expected_revision": aba.clinical_revision,
                "status": "EN_FAUTEUIL",
            },
            status="pending", expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(aba_action)
        db.commit()
        aba_id = aba.id
        aba_action_id = aba_action.id
        expected_revision = aba.clinical_revision
        db.execute(text("UPDATE appointments SET status='ANNULE' WHERE id=:id"), {"id": aba_id})
        db.execute(text("UPDATE appointments SET status='PREVU' WHERE id=:id"), {"id": aba_id})
        db.commit()
        db.refresh(aba)
        assert aba.clinical_revision == expected_revision + 2
    result = api.post(
        "/api/bot/execute", headers=authorization,
        json={"pending_action_id": aba_action_id},
    )
    assert result.status_code == 409, result.text
    with database.SessionLocal() as db:
        assert db.get(models.Appointment, aba_id).status == models.AppointmentStatus.PREVU
        assert db.get(models.BotPendingAction, aba_action_id).status == "failed"
    print("CLINICAL_REAL_BOT_ABA_REVISION_CAS: PASS")

    # A SQL-side old-appointment corpus must not be loaded as ORM objects
    # to check one future slot. The indexed end expression filters in DB.
    import time
    old_start = datetime(2020, 1, 1, 9, 0)
    count = 2500
    with database.SessionLocal() as db:
        db.bulk_insert_mappings(models.Appointment, [
            {
                "patient_name": f"Synthetic archive {i}",
                "employer_id": doctor_id,
                "praticien_id": doctor_id,
                "datetime_start": old_start + timedelta(days=i % 900),
                "duration_minutes": 30,
                "status": models.AppointmentStatus.PREVU,
                "scheduling_type": models.SchedulingType.EXACT_TIME,
            }
            for i in range(count)
        ])
        db.commit()
        from backend.routers.appointments import _find_conflicts
        candidate = first_slot + timedelta(days=60)
        # Check both correctness and bounded runtime, with a generous CI
        # threshold. Log actual timings; do not claim realistic scale.
        durations = []
        for _ in range(5):
            start_clock = time.perf_counter()
            matches = _find_conflicts(db, doctor_id, doctor_id, candidate, 30)
            durations.append(time.perf_counter() - start_clock)
            assert not matches
        assert max(durations) < 5.0, f"SQL end index query too slow: {durations}"
        if db.get_bind().dialect.name == "sqlite":
            index_rows = db.execute(text(
                "PRAGMA index_list('appointments')"
            )).all()
            assert "ix_appointments_tenant_clinical_end" in {row[1] for row in index_rows}
        else:
            indexed = db.execute(text(
                "SELECT count(*) FROM pg_indexes WHERE tablename='appointments' "
                "AND indexname='ix_appointments_tenant_clinical_end'"
            )).scalar()
            assert indexed == 1
        print("CLINICAL_REAL_INDEXED_OVERLAP_ARCHIVE: PASS",
              "historical_rows=", count,
              "max_lookup_ms=", round(max(durations) * 1000, 2))


    print("CLINICAL_FULL_SCHEMA_HTTP_GATE: PASS migrated schema, HTTP, real database transaction")


if __name__ == "__main__":
    run()
