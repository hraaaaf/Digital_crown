"""CB-03 G4: real FastAPI TestClient + isolated full Alembic PostgreSQL.

No live server, no real person and NO production/Neon access. The process
refuses any URL except the disposable loopback PostgreSQL CI service, checks
an empty migrated DB, and records the exact immutable source SHA.
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from urllib.parse import urlsplit

url = urlsplit(os.environ.get("DATABASE_URL", ""))
HEAD = os.getenv("CB03_G4_SOURCE_HEAD", "")
if not (
    os.getenv("GITHUB_ACTIONS") == "true"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.getenv("ENVIRONMENT") == "rehearsal"
    and url.scheme == "postgresql"
    and url.hostname in {"127.0.0.1", "localhost"}
    and url.port == 5432
    and url.username == "cb03_g4"
    and url.path == "/cb03_g4_ephemeral"
    and not url.query and not url.fragment
    and len(HEAD) == 40 and all(c in "0123456789abcdef" for c in HEAD)
    and subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == HEAD
):
    raise RuntimeError("REFUSED: requires disposable loopback PG and exact CI SHA")

from fastapi.testclient import TestClient
from backend import database, models
from backend.config import settings
from backend.main import app
from backend.security import get_password_hash
from backend.core.schema_runtime import assert_database_at_current_head

assert database.engine.dialect.name == "postgresql"
assert_database_at_current_head(database.engine)
with database.SessionLocal() as db:
    assert db.query(models.User).count() == 0, "not an empty synthetic DB"
    assert db.query(models.Appointment).count() == 0
    assert db.query(models.BotPendingAction).count() == 0

# Settings flags are patched within this one test process only. The CI runner
# environment deliberately leaves ALL CB03 flags OFF outside this scope.
with ExitStack() as flags:
    for key in (
        "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED",
        "CROWN_BOT_GUIDED_NLU_ENABLED",
        "CROWN_BOT_CB03_PREPARATION_ENABLED",
        "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED",
        "CROWN_BOT_CB03_CONFIRMATION_ENABLED",
    ):
        flags.enter_context(patch.object(settings, key, True))

    password = secrets.token_urlsafe(26)
    def new_owner(label):
        with database.SessionLocal() as db:
            u = models.User(
                email=f"cb03-g4-{label}@synthetic.invalid",
                hashed_password=get_password_hash(password),
                role=models.UserRole.DENTISTE,
                nom_complet=f"Synthetic G4 {label}",
                is_active=True, is_licensed=True,
                approval_status=models.ApprovalStatus.APPROVED.value,
            )
            db.add(u)
            db.flush()
            p = models.Patient(
                numero_dossier=f"CB03-G4-{label}",
                nom="BENALI" if label == "a" else "FOREIGN",
                prenom="SYNTHETIC", sexe="F",
                date_naissance=datetime(1990, 1, 1),
                employer_id=u.id,
            )
            db.add(p)
            db.commit()
            return u.id, p.id

    owner, patient = new_owner("a")
    foreign_owner, foreign_patient = new_owner("b")

    def auth_client(label):
        client = TestClient(app, raise_server_exceptions=True)
        res = client.post("/api/auth/login", data={
            "username": f"cb03-g4-{label}@synthetic.invalid",
            "password": password,
        })
        assert res.status_code == 200, f"LOGIN_{label}_{res.status_code} {res.text[:500]}"
        return client

    a1, a2, foreign = auth_client("a"), auth_client("a"), auth_client("b")
    def create_appt(status=models.AppointmentStatus.PREVU):
        with database.SessionLocal() as db:
            row = models.Appointment(
                employer_id=owner, patient_id=patient, praticien_id=owner,
                datetime_start=datetime.now() + timedelta(days=28),
                duration_minutes=30, motif="CB03-G4 synthetic",
                status=status,
            )
            db.add(row)
            db.commit()
            return row.id

    def prepare_status(appt_id, target="salle d'attente"):
        return a1.post("/api/bot/guided/prepare-status", json={
            "selected_appointment_id": appt_id,
            "utterance": f"Prépare le statut du RDV en {target}",
        })

    def confirm(client, key):
        return client.post("/api/bot/guided/confirm", json={
            "preparation_id": key, "confirm": True,
        })

    events = []

    # Two independent PostgreSQL connections/HTTP clients race the SAME G2
    # confirmation. 1 action, 1 status mutation, exactly 1 final audit.
    appt = create_appt()
    p = prepare_status(appt)
    assert p.status_code == 200, f"PREPARE_STATUS_{p.status_code}_{p.text[:700]}"
    key = p.json()["preparation_id"]
    with database.SessionLocal() as db:
        old_revision = db.get(models.Appointment, appt).clinical_revision
    barrier = Barrier(2, timeout=25)
    def race(client):
        barrier.wait()
        return confirm(client, key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(race, a1), pool.submit(race, a2)]
        answers = [f.result(timeout=40) for f in futures]
    statuses = sorted(x.status_code for x in answers)
    assert statuses == [200, 409], f"STATUS_RACE_{statuses}_{[x.text[:300] for x in answers]}"
    own = a1.get("/api/bot/guided/actions/" + key)
    assert own.status_code == 200
    assert own.json()["status"] == "executed"
    assert own.json()["result"] == {"appointment_id": appt, "status": "EN_SALLE_ATTENTE"}
    assert own.json()["safe_to_retry_automatically"] is False
    denied = foreign.get("/api/bot/guided/actions/" + key)
    assert denied.status_code == 404
    denied_confirm = confirm(foreign, key)
    assert denied_confirm.status_code == 404
    with database.SessionLocal() as db:
        a = db.get(models.Appointment, appt)
        assert a.status == models.AppointmentStatus.EN_SALLE_ATTENTE
        assert a.clinical_revision == old_revision + 1
        action = db.get(models.BotPendingAction, key)
        assert action.status == "executed"
        audits = db.query(models.AuditLog).filter_by(
            action="CB03_ACTION_CONFIRMED", resource_id=key,
        ).count()
        assert audits == 1
    events.append({"case": "SAME_ACTION_PARALLEL_G2_HTTP", "statuses": statuses,
                   "oneAudit": True, "ownerIsolation": [denied.status_code, denied_confirm.status_code]})

    # PG monotonic trigger + G2 fresh revision at actual HTTP confirm, so
    # an ABA status restored to same visible state is NOT confirmable.
    stale_appt = create_appt()
    p = prepare_status(stale_appt)
    assert p.status_code == 200, f"PREPARE_ABA_{p.status_code}_{p.text[:500]}"
    stale_id = p.json()["preparation_id"]
    with database.SessionLocal() as db:
        rev0 = db.get(models.Appointment, stale_appt).clinical_revision
    for st in (models.AppointmentStatus.ANNULE, models.AppointmentStatus.PREVU):
        with database.SessionLocal() as db:
            assert db.query(models.Appointment).filter_by(id=stale_appt).update(
                {"status": st}, synchronize_session=False,
            ) == 1
            db.commit()
    attempt = confirm(a1, stale_id)
    assert attempt.status_code == 409, f"ABA_EXPECT_409_{attempt.status_code}_{attempt.text[:350]}"
    with database.SessionLocal() as db:
        a = db.get(models.Appointment, stale_appt)
        assert a.status == models.AppointmentStatus.PREVU
        assert a.clinical_revision == rev0 + 2
        assert db.get(models.BotPendingAction, stale_id).status == "prepared"
    events.append({"case": "ABA_REVISION_HTTP_PG", "http": attempt.status_code,
                   "revisionDelta": 2})

    # Expired action never mutates, even with explicit confirm.
    exp_appt = create_appt()
    expired = prepare_status(exp_appt)
    assert expired.status_code == 200
    exp_id = expired.json()["preparation_id"]
    with database.SessionLocal() as db:
        db.get(models.BotPendingAction, exp_id).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    rejected = confirm(a1, exp_id)
    after = a1.get("/api/bot/guided/actions/" + exp_id)
    assert rejected.status_code == 410
    assert after.status_code == 200 and after.json()["status"] == "expired"
    events.append({"case": "TTL_HTTP_PG", "post": 410, "reconciled": "expired"})

    # Confirm a real SQL booking via G1-A -> G2, discard ACK, GET proof later.
    # Date is chosen by the client but revalidated by server at confirmation.
    today = datetime.now() + timedelta(days=22)
    while today.weekday() != 0:
        today += timedelta(days=1)
    day = today.date().isoformat()
    phrase = f"Prépare un RDV le {day} à 10h pour Mme Benali contrôle"
    booking = a1.post("/api/bot/guided/prepare-appointment", json={
        "utterance": phrase, "duration_minutes": 30, "praticien_id": owner,
    })
    assert booking.status_code == 200, f"BOOK_PREPARE_{booking.status_code}_{booking.text[:700]}"
    booking_id = booking.json()["preparation_id"]
    done = confirm(a1, booking_id)
    assert done.status_code == 200, f"BOOK_CONFIRM_{done.status_code}_{done.text[:700]}"
    success_receipt = done.json()["result"]
    # Simulate application losing HTTP ACK: throw response away and fetch via
    # a newly authenticated, independent client. No second POST ever performed.
    del done
    independent = auth_client("a")
    receipt = independent.get("/api/bot/guided/actions/" + booking_id)
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "executed"
    assert receipt.json()["result"] == success_receipt
    assert success_receipt["status"] == "CREATED"
    with database.SessionLocal() as db:
        a = db.get(models.Appointment, success_receipt["appointment_id"])
        assert a.patient_id == patient and a.employer_id == owner
        assert db.get(models.BotPendingAction, booking_id).status == "executed"
        assert db.query(models.AuditLog).filter_by(
            action="CB03_ACTION_CONFIRMED", resource_id=booking_id
        ).count() == 1
    events.append({"case": "REAL_BOOKING_HTTP_PG_LOST_ACK_GET", "post": 200,
                   "get": 200, "receiptMatches": True, "replayed": False})
    independent.close()

    # A fresh preparation may be persisted, but a slot booked by a different
    # HTTP transaction after preview must refuse at confirm (rollback claim).
    # A second prep for the already-reserved slot is rejected immediately.
    conflict = a1.post("/api/bot/guided/prepare-appointment", json={
        "utterance": phrase, "duration_minutes": 30, "praticien_id": owner,
    })
    assert conflict.status_code == 409, f"BOOK_CONFLICT_{conflict.status_code}_{conflict.text[:600]}"
    events.append({"case": "CANONICAL_SLOT_CONFLICT_PG", "http": 409})

    a1.close(); a2.close(); foreign.close()

with database.SessionLocal() as db:
    assert db.query(models.User).count() == 2
    assert db.query(models.Patient).count() == 2
    total_confirm = db.query(models.AuditLog).filter(
        models.AuditLog.action == "CB03_ACTION_CONFIRMED"
    ).count()
    assert total_confirm == 2

report = {
    "schema": "CB03_G4_POSTGRES_FULL_ALEMBIC_HTTP_V1",
    "head": HEAD, "database": "fresh-job-disposable-loopback",
    "real_postgresql": True, "main_app": True, "lifespan_started": False,
    "real_cabinet": False, "external_network_db": False,
    "cases": events, "confirmedAuditCount": total_confirm,
    "unresolved": [
        "No real multi-process OS kill during COMMIT; lost ACK emulated by discarding response",
        "No integration via real headed browser with PostgreSQL",
        "No patient or operator real session; no clinic production database",
    ],
}
dest = Path("artifacts/cb03-g4/postgres-real-http.json")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("CB03_G4_POSTGRES_HTTP_PASS", json.dumps(report))
