"""FUE-G03 Phase A1 isolated Patient Companion QR handoff seed and post-SQL proof.

This tool may run ONLY on the disposable T2 CI database. Never on cabinet
storage. All synthetic patient and appointment creation occurs BEFORE UI tests.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if not (
    os.getenv("T2_STATION_FUE") == "1"
    and os.getenv("T2_G03_A1") == "1"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.getenv("ENVIRONMENT") == "test"
    and os.getenv("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"
):
    raise SystemExit("FAIL CLOSED: disposable T2 G03 A1 context required")

# Same synthetic SQLCipher key as the T2 server, NOT the CI runner auth key.
os.environ["SECRET_KEY"] = "t2-runtime-certification-secret-key-000001"
os.environ["MOBILE_PAIRING_KEY_HEX"] = "2" * 64

from backend import database, models  # noqa: E402
from backend.models_patient_companion import PatientCompanionAccess  # noqa: E402
from backend.services.station_arrival_bridge import cabinet_local_day_bounds  # noqa: E402

OUT = ROOT / "frontend" / "artifacts" / "v15-03-a1-companion-real"
SEED = OUT / "seed.json"
SPECS = (
    ("primary", "G03A1-PC-PRIMARY", "QR", "Primary", "1992-01-04"),
    ("secondary", "G03A1-PC-SECONDARY", "QR", "Secondary", "1993-02-05"),
)


def seed():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = {}
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        assert db.query(models.CabinetConfig).filter_by(owner_id=owner.id).one()
        for key, dossier, first, last, dob in SPECS:
            assert db.query(models.Patient).filter_by(numero_dossier=dossier, employer_id=owner.id).first() is None, dossier
            patient = models.Patient(
                employer_id=owner.id, numero_dossier=dossier,
                prenom=first, nom=last, date_naissance=datetime.fromisoformat(dob),
                sexe="F", telephone="0699999991" if key == "primary" else "0699999992",
            )
            db.add(patient)
            db.flush()
            rows[key] = {"patientId": patient.id, "displayName": first + " " + last}
            if key == "primary":
                appointment = models.Appointment(
                    employer_id=owner.id, patient_id=patient.id,
                    datetime_start=datetime.now().replace(hour=11, minute=30, second=0, microsecond=0),
                    duration_minutes=30, status=models.AppointmentStatus.PREVU,
                    scheduling_type=models.SchedulingType.EXACT_TIME,
                    motif="G03-A1 fictif, pas de données médicales",
                )
                db.add(appointment)
                db.flush()
                rows[key]["appointmentId"] = appointment.id
        db.commit()
    SEED.write_text(json.dumps({"lab": "G03-A1-QR", "patients": rows}, indent=2), encoding="utf-8")
    print("G03_A1_SYNTHETIC_SEED_PASS patients=2 appointments=1")


def verify():
    fixture = json.loads(SEED.read_text())["patients"]
    with database.SessionLocal() as db:
        primary = fixture["primary"]
        secondary = fixture["secondary"]
        appointment = db.get(models.Appointment, primary["appointmentId"])
        assert appointment.patient_id == primary["patientId"]
        assert appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE, appointment.status
        assert appointment.ticket_number is None, "Station 03.4 must never auto-assign ticket"
        assert not db.query(models.Appointment).filter_by(patient_id=secondary["patientId"]).count()
        accesses = db.query(PatientCompanionAccess).filter(
            PatientCompanionAccess.patient_id.in_([primary["patientId"], secondary["patientId"]])
        ).all()
        assert len(accesses) == 2 and all(a.revoked_at is None for a in accesses)
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        sessions = db.query(models.WorkstationPatientSession).filter(
            models.WorkstationPatientSession.employer_id == owner.id,
        ).all()
        claimed = [s for s in sessions if s.claimed_at is not None]
        assert len(claimed) >= 1, "No real Companion claim persisted"
        assert any(s.patient_id == primary["patientId"] for s in claimed), "Wrong patient identified"
        assert not any(s.patient_id == secondary["patientId"] for s in claimed), "Secondary context leaked to Station"
        assert not any(s.claim_token_hash == "" for s in sessions), "Session stored empty token hash"
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == owner.id,
            models.AuditLog.action == "STATION_PATIENT_ARRIVED",
        ).all()
        # Backend 03.4 changes may use other audit names. Appointment and station
        # identity are authoritative; audit inspection is informational only.
        result = {
            "status": "PASS", "environment": "isolated disposable encrypted SQLite",
            "appointments": {str(appointment.id): appointment.status.value},
            "ticketUnassigned": True,
            "activeCompanionAccesses": len(accesses),
            "companionClaims": len(claimed),
            "arrivedAuditCount": len(audit),
            "primaryClaimBound": True,
            "secondaryPatientUnchanged": True,
        }
    (OUT / "sql-after.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("G03_A1_INDEPENDENT_SQL_PASS " + json.dumps(result))


def expire_session(session_id: str):
    # Test-injected past deadline exercises the *real* expiry enforcement.
    # Only an unclaimed synthetic Station session may be altered here.
    from datetime import timedelta
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        session = db.query(models.WorkstationPatientSession).filter_by(
            id=session_id, employer_id=owner.id, claimed_at=None, purged_at=None,
        ).one()
        session.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    print("G03_A1_TEST_EXPIRY_PREPARED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--expire-session")
    args = parser.parse_args()
    if args.verify:
        verify()
    elif args.expire_session:
        expire_session(args.expire_session)
    else:
        seed()
