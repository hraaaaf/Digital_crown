"""Disposable V1.5-03.21 FUE-G station seed and independent SQL oracle.

Run ONLY on ephemeral test SQLite. The application API owns all workflow mutations;
this helper seeds synthetic patients/appointments BEFORE the browser begins.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_DB = "sqlite:///./t2-runtime-cert.db"
if (
    os.environ.get("T2_STATION_FUE") != "1"
    or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
    or os.environ.get("ENVIRONMENT") != "test"
    or os.environ.get("DATABASE_URL") != EXPECTED_DB
):
    raise SystemExit("FAIL CLOSED: isolated T2 Station FUE SQLite context required")

from backend import database, models  # noqa: E402

OUT = Path("frontend/artifacts/v15-03-real-integration")
SEED = OUT / "seed.json"
SPECS = (
    ("zero", "STFUE-ZERO", "Zero", "0699900301", "1993-03-01", ()),
    ("single", "STFUE-ONE", "Single", "0699900302", "1992-03-02", ((10, 0, 307),)),
    ("multiple", "STFUE-MULTI", "Multi", "0699900303", "1991-03-03", ((11, 0, 308), (12, 0, 309))),
)


def seed():
    OUT.mkdir(parents=True, exist_ok=True)
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
        assert db.query(models.CabinetConfig).filter_by(owner_id=owner.id).one()
        rows = {}
        for key, dossier, given, phone, dob, appointments in SPECS:
            assert db.query(models.Patient).filter_by(numero_dossier=dossier, employer_id=owner.id).first() is None, (
                "FUE seed re-execution refused: " + dossier
            )
            patient = models.Patient(
                numero_dossier=dossier, nom="STATION-FICTIF", prenom=given,
                employer_id=owner.id, sexe="F", date_naissance=datetime.fromisoformat(dob),
                telephone=phone,
            )
            db.add(patient)
            db.flush()
            app_ids = []
            for hour, minute, ticket in appointments:
                appointment = models.Appointment(
                    patient_id=patient.id, employer_id=owner.id,
                    datetime_start=datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0),
                    duration_minutes=30, status=models.AppointmentStatus.PREVU,
                    scheduling_type=models.SchedulingType.EXACT_TIME,
                    motif="FUE-G03 fictif",
                    ticket_number=ticket,
                )
                db.add(appointment)
                db.flush()
                app_ids.append(appointment.id)
            rows[key] = {
                "patientId": patient.id, "dossier": dossier,
                "birthDate": dob, "phone": phone, "appointmentIds": app_ids,
                "ticketNumbers": [a[2] for a in appointments],
            }
        db.commit()
    SEED.write_text(json.dumps({"lab": "FUE-G03-21", "patients": rows}, indent=2), encoding="utf-8")
    print("STATION_G03_SYNTHETIC_SEED_PASS " + json.dumps({k: len(v["appointmentIds"]) for k,v in rows.items()}))


def verify():
    fixture = json.loads(SEED.read_text(encoding="utf-8"))["patients"]
    with database.SessionLocal() as db:
        statuses = {}
        for key, spec in fixture.items():
            for index, aid in enumerate(spec["appointmentIds"]):
                app = db.get(models.Appointment, aid)
                assert app is not None and app.patient_id == spec["patientId"]
                if key == "multiple" and index == 1:
                    # The second appointment must remain unarrived, not be silently marked.
                    assert app.status == models.AppointmentStatus.PREVU, (key, app.status)
                else:
                    assert app.status == models.AppointmentStatus.EN_SALLE_ATTENTE, (key, app.status)
                    assert app.ticket_number == spec["ticketNumbers"][index]
                statuses[str(aid)] = str(app.status.value)
        owner = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
        actions = db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == owner.id,
            models.AuditLog.action.in_((
                "STATION_STAFF_ASSISTANCE_REQUESTED",
                "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED",
                "STATION_WALL_PATIENT_CALLED",
            )),
        ).all()
        counts = {name: sum(a.action == name for a in actions) for name in (
            "STATION_STAFF_ASSISTANCE_REQUESTED",
            "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED",
            "STATION_WALL_PATIENT_CALLED",
        )}
        assert counts == {
            "STATION_STAFF_ASSISTANCE_REQUESTED": 1,
            "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED": 1,
            "STATION_WALL_PATIENT_CALLED": 2,
        }, counts
        workstations = db.query(models.WorkstationMode).filter_by(employer_id=owner.id).all()
        modes = [w.default_experience for w in workstations if w.revoked_at is None]
        assert modes.count("station") >= 2 and modes.count("cabinet") >= 1, modes
        report = {"status": "PASS", "database": "ephemeral SQLite", "statuses": statuses,
                  "audits": counts, "workstations": {"station": modes.count("station"), "cabinet": modes.count("cabinet")}}
    (OUT / "sql-after.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("STATION_G03_INDEPENDENT_SQL_PASS " + json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify() if args.verify else seed()
