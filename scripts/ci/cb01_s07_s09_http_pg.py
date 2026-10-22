"""CB-01 S07/S09 real FastAPI HTTP handlers on disposable full Alembic PostgreSQL.

Uses the production app and routers with real ASGI HTTP requests (TestClient).
Lifespan is deliberately NOT started: schema is migrated by operator Alembic
before this script, and no scheduler, ML engine or external connector is loaded.
This is an integration proof, not a Windows/human/production certification.
"""
from __future__ import annotations

import json
import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier
from urllib.parse import urlsplit

from sqlalchemy import inspect

EXPECTED_DB = "cb01_http_lab"
EXPECTED_USER = "cb01_http"
EXPECTED_HOSTS = {"127.0.0.1", "localhost"}

def require_isolated():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("REFUSED: GitHub Actions only")
    if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
        raise RuntimeError("REFUSED: isolated runtime required")
    if os.environ.get("ENVIRONMENT") != "rehearsal":
        raise RuntimeError("REFUSED: rehearsal mode required")
    url = os.environ.get("DATABASE_URL", "")
    parsed = urlsplit(url)
    if (parsed.scheme != "postgresql" or parsed.hostname not in EXPECTED_HOSTS
            or parsed.port != 5432 or parsed.path != f"/{EXPECTED_DB}"
            or parsed.username != EXPECTED_USER
            or parsed.query or parsed.fragment):
        raise RuntimeError("REFUSED: exact loopback PostgreSQL lab URL required")
    head = os.environ.get("CB01_SOURCE_HEAD", "")
    if (len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head)
            or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != head):
        raise RuntimeError("REFUSED: exact HEAD mismatch")
    return head

source_head = require_isolated()

# Imports deliberately occur AFTER isolation has been proven. This is the real
# product ASGI app, dependencies, ORM and route code, not a copied mini-router.
from fastapi.testclient import TestClient
from backend import database, models
from backend.core.schema_runtime import assert_database_at_current_head
from backend.main import app
from backend.security import get_password_hash
from backend.services.agenda_transaction_lock import lock_cabinet_booking

assert database.engine.dialect.name == "postgresql"
assert_database_at_current_head(database.engine)
assert "appointments" in inspect(database.engine).get_table_names()
with database.SessionLocal() as db:
    assert db.query(models.User).count() == 0, "REFUSED: fixture DB not empty"
    assert db.query(models.Appointment).count() == 0, "REFUSED: appointment DB not empty"
    assert db.query(models.BotPendingAction).count() == 0, "REFUSED: bot action DB not empty"

owner_email = "cb01-http-owner@synthetic.invalid"
password = os.environ.get("T2_PASSWORD", "")
if len(password) < 24:
    raise RuntimeError("REFUSED: disposable owner secret missing")
with database.SessionLocal() as db:
    owner = models.User(
        email=owner_email, hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE, nom_complet="Synthetic HTTP PG Owner",
        is_active=True, is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
    )
    db.add(owner)
    db.flush()
    patient = models.Patient(
        numero_dossier="CB01-HTTP-0001", nom="FICTIF", prenom="PG_HTTP",
        sexe="F", date_naissance=datetime(1990, 1, 1),
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    owner_id, patient_id = int(owner.id), int(patient.id)

def fresh_authorized_client():
    # No shared auth cookie jar: one browser-equivalent client per HTTP worker.
    client = TestClient(app, raise_server_exceptions=True)
    result = client.post("/api/auth/login", data={
        "username": owner_email, "password": password,
    })
    assert result.status_code == 200, f"HTTP_LOGIN_{result.status_code}"
    return client

first_client = fresh_authorized_client()
second_client = fresh_authorized_client()
barrier = Barrier(2, timeout=15)
start = datetime(2027, 3, 9, 10, 0)
def appointment_payload(target):
    return {
        "patient_id": patient_id,
        "patient_name": "FICTIF PG HTTP",
        "datetime_start": target.isoformat(),
        "duration_minutes": 30,
        "motif": "Simulation cabinet",
        "status": "PRÉVU",
        "scheduling_type": "EXACT_TIME",
        "praticien_id": owner_id,
    }

def book(client):
    barrier.wait()
    return client.post("/api/appointments/", json=appointment_payload(start))
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(book, c) for c in (first_client, second_client)]
    answers = [f.result(timeout=30) for f in futures]
codes = sorted(r.status_code for r in answers)
assert codes in ([200, 409], [201, 409]), f"S07_HTTP_EXPECT_ONE_409_GOT_{codes}"
# Assert the actual 409 JSON contract consumed by AgendaModal S10 UI.
loser = next(r for r in answers if r.status_code == 409)
conflict_detail = loser.json().get("detail")
assert isinstance(conflict_detail, dict), "S10_REAL_409_DETAIL_NOT_OBJECT"
assert conflict_detail.get("message") == "Créneau en conflit avec un autre rendez-vous", (
    "S10_REAL_409_MESSAGE_CONTRACT_CHANGED")
assert isinstance(conflict_detail.get("conflicts"), list) and len(conflict_detail["conflicts"]) == 1, (
    "S10_REAL_409_CONFLICT_LIST_MISSING")

with database.SessionLocal() as db:
    overlapping = db.query(models.Appointment).filter(
        models.Appointment.employer_id == owner_id,
        models.Appointment.datetime_start == start,
        models.Appointment.deleted_at.is_(None),
    ).all()
    assert len(overlapping) == 1, "S07_DOUBLE_BOOKING"
    booked_id = int(overlapping[0].id)
    assert int(overlapping[0].patient_id) == patient_id

adjacent = first_client.post("/api/appointments/", json=appointment_payload(
    start + timedelta(minutes=30)))
assert adjacent.status_code in (200, 201), f"S07_ADJACENT_HTTP_{adjacent.status_code}"

with database.SessionLocal() as db:
    appt = db.get(models.Appointment, booked_id)
    assert appt is not None
    initial_revision = int(appt.clinical_revision)
    assert appt.status == models.AppointmentStatus.PREVU
    all_appointments = db.query(models.Appointment).filter(
        models.Appointment.employer_id == owner_id).count()
    assert all_appointments == 2, f"S07_APPOINTMENT_COUNT_{all_appointments}"
    # The real /api/bot/execute path requires its action to belong to an
    # existing, tenant-scoped BotSession. Preserve the actual FK contract on
    # full Alembic PostgreSQL instead of inventing an orphan pending action.
    bot_session_id = str(uuid.uuid4())
    db.add(models.BotSession(
        id=bot_session_id, employer_id=owner_id, user_id=owner_id,
        patient_id=patient_id, title="CB-01 isolated HTTP ABA fixture",
    ))
    db.flush()
    # The real /api/bot/execute path will consume this server-side action
    # by UUID only. No action payload is accepted from the HTTP caller.
    stale_action_id = str(uuid.uuid4())
    stale_action = models.BotPendingAction(
        id=stale_action_id, session_id=bot_session_id,
        user_id=owner_id, employer_id=owner_id,
        action_type="CHANGE_STATUS", status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        params_json={
            "appointment_id": booked_id, "patient_id": patient_id,
            "expected_status": "PREVU", "expected_revision": initial_revision,
            "status": "TERMINE", "status_label": "Terminé",
        },
    )
    db.add(stale_action)
    db.commit()

# Another real database session performs A -> B -> A. Postgres trigger must
# increment clinical_revision for BOTH changes; stale action cannot resurrect.
for new_status in (models.AppointmentStatus.TERMINE, models.AppointmentStatus.PREVU):
    with database.SessionLocal() as db:
        assert db.query(models.Appointment).filter(
            models.Appointment.id == booked_id,
            models.Appointment.employer_id == owner_id,
        ).update({"status": new_status}, synchronize_session=False) == 1
        db.commit()
with database.SessionLocal() as db:
    appt = db.get(models.Appointment, booked_id)
    after_aba_revision = int(appt.clinical_revision)
    assert appt.status == models.AppointmentStatus.PREVU
    assert after_aba_revision == initial_revision + 2, "S09_DB_TRIGGER_NOT_MONOTONIC"

stale = first_client.post("/api/bot/execute", json={"pending_action_id": stale_action_id})
assert stale.status_code == 409, f"S09_STALE_BOT_HTTP_{stale.status_code}"
with database.SessionLocal() as db:
    appt = db.get(models.Appointment, booked_id)
    pending = db.get(models.BotPendingAction, stale_action_id)
    assert appt.status == models.AppointmentStatus.PREVU, "S09_STALE_BOT_MUTATED_STATUS"
    assert int(appt.clinical_revision) == after_aba_revision
    assert pending.status != "executed", "S09_STALE_BOT_FALSE_SUCCESS"
    # Create a NEW action from the CURRENT version, not a retry of stale ID.
    fresh_action_id = str(uuid.uuid4())
    db.add(models.BotPendingAction(
        id=fresh_action_id, session_id=bot_session_id,
        user_id=owner_id, employer_id=owner_id,
        action_type="CHANGE_STATUS", status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        params_json={
            "appointment_id": booked_id, "patient_id": patient_id,
            "expected_status": "PREVU", "expected_revision": after_aba_revision,
            "status": "TERMINE", "status_label": "Terminé",
        },
    ))
    db.commit()
fresh = first_client.post("/api/bot/execute", json={"pending_action_id": fresh_action_id})
assert fresh.status_code == 200 and fresh.json().get("action_type") == "write_done", (
    f"S09_FRESH_BOT_HTTP_{fresh.status_code}")
with database.SessionLocal() as db:
    appt = db.get(models.Appointment, booked_id)
    assert appt.status == models.AppointmentStatus.TERMINE
    assert int(appt.clinical_revision) == after_aba_revision + 1
    assert db.get(models.BotPendingAction, fresh_action_id).status == "executed"
    assert db.get(models.BotPendingAction, stale_action_id).status != "executed"

# S12 HTTP: real GhostBrain read-ACK against migrated PostgreSQL.
# Assert own unread remains after foreign/unrecognized 404, then own 200
# persists, disappears from subsequent read and other-tenant alert stays unread.
with database.SessionLocal() as db:
    other_owner = models.User(
        email="cb01-foreign-ghost@synthetic.invalid",
        hashed_password=get_password_hash(password), role=models.UserRole.DENTISTE,
        nom_complet="Synthetic Foreign Ghost Owner", is_active=True,
        is_licensed=True, approval_status=models.ApprovalStatus.APPROVED.value,
    )
    db.add(other_owner)
    db.flush()
    own_insight = models.GhostMemoryLog(
        employer_id=owner_id, patient_id=None, insight_type="STOCK",
        content="Synthétique : vérifier un stock fictif",
        context_hash="c" * 64, is_read=False,
    )
    foreign_insight = models.GhostMemoryLog(
        employer_id=other_owner.id, patient_id=None, insight_type="STOCK",
        content="Synthétique : alerte d'un autre cabinet",
        context_hash="d" * 64, is_read=False,
    )
    db.add_all([own_insight, foreign_insight])
    db.commit()
    own_id, foreign_id = int(own_insight.id), int(foreign_insight.id)
initial = first_client.get("/api/ai/ghost-insights")
assert initial.status_code == 200 and any(
    row["id"] == own_id for row in initial.json().get("insights", [])
), f"S12_OWN_UNREAD_MISSING_{initial.status_code}"
missing = first_client.post("/api/ai/ghost-insights/2147483637/read")
foreign = first_client.post(f"/api/ai/ghost-insights/{foreign_id}/read")
assert missing.status_code == 404 and foreign.status_code == 404, (
    f"S12_NONEXISTENT_FOREIGN_GUARD_{missing.status_code}_{foreign.status_code}")
with database.SessionLocal() as db:
    assert db.get(models.GhostMemoryLog, own_id).is_read is False, "S12_REFUSAL_MUTATED_OWN"
    assert db.get(models.GhostMemoryLog, foreign_id).is_read is False, "S12_FOREIGN_READ_LEAK"
ack = first_client.post(f"/api/ai/ghost-insights/{own_id}/read")
assert ack.status_code == 200 and ack.json() == {"status": "read"}, (
    f"S12_OWN_READ_ACK_{ack.status_code}")
after_ack = first_client.get("/api/ai/ghost-insights")
assert after_ack.status_code == 200 and not any(
    row["id"] == own_id for row in after_ack.json().get("insights", [])
), "S12_READ_ALERT_STILL_IN_FEED"
with database.SessionLocal() as db:
    assert db.get(models.GhostMemoryLog, own_id).is_read is True, "S12_ACK_NOT_PERSISTED"
    assert db.get(models.GhostMemoryLog, foreign_id).is_read is False, "S12_FOREIGN_MUTATED"
first_client.close()
second_client.close()
report = {
    "schema": "CB01_HTTP_PG_S07_S09_V1",
    "sourceHead": source_head,
    "database": "ISOLATED_POSTGRESQL_ALEMBIC_FULL_SCHEMA",
    "httpTransport": "FASTAPI_TESTCLIENT_REAL_MAIN_APP_LIFESPAN_NOT_STARTED",
    "S07": {
        "status": "PASS_HTTP_ROUTER_PG_INTEGRATION",
        "simultaneousPostStatuses": codes,
        "identicalSlotCreated": 1, "adjacentSlotCreated": 1,
    },
    "S10": {
        "status": "PASS_REAL_409_RESPONSE_CONTRACT",
        "httpConflictStatus": 409,
        "errorFormat": "detail.message+detail.conflicts",
        "frontendRealBrowserJourney": "NOT_RUN",
    },
    "S12": {
        "status": "PASS_HTTP_READ_ACK_PERSISTENCE",
        "initialUnread": True, "missingHttpStatus": missing.status_code,
        "otherTenantHttpStatus": foreign.status_code,
        "authorizedAckStatus": ack.status_code,
        "ownUnreadAfterAck": False, "foreignStillUnread": True,
        "frontendRealWebSocketJourney": "NOT_RUN",
    },
    "S09": {
        "status": "PASS_HTTP_BOT_EXECUTE_ABA_INTEGRATION",
        "oldClinicalRevision": initial_revision,
        "revisionAfterABA": after_aba_revision,
        "staleBotHttpStatus": stale.status_code,
        "staleActionExecuted": False,
        "freshBotHttpStatus": fresh.status_code,
        "currentRevisionActionExecuted": True,
    },
    "limitations": [
        "In-process FastAPI TestClient, not two remote Windows clients",
        "App lifespan not started; schema upgraded separately via Alembic",
        "All entities are synthetic; not the CB-01 proposal-only UI workflow",
        "No full DB snapshot / native browser zoom / SQLCipher concurrency",
        "No staff human E2E and no real cabinet data",
    ],
    "humanE2EValidated": 0, "converged": False,
}
out = Path("artifacts/cb01-associate-sidecar/http-pg-s07-s09-evidence.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("CB01_HTTP_PG_S07_S09_S10_S12: PASS_REAL_ROUTERS_FULL_PG_SCHEMA; NOT_STAFF_E2E")
