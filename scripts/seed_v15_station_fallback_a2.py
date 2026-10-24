"""FUE-G03 A2: strictly isolated synthetic fallback patients and independent SQL oracle.

NEVER run against a cabinet or any non-disposable database.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if not (
    os.getenv("T2_G03_A2") == "1"
    and os.getenv("T2_STATION_FUE") == "1"
    and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.getenv("ENVIRONMENT") == "test"
    and os.getenv("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"
):
    raise SystemExit("FAIL CLOSED: isolated synthetic G03-A2 runtime required")

# Match the disposable T2 runtime's SQLCipher key, never a real cabinet key.
os.environ["SECRET_KEY"] = "t2-runtime-certification-secret-key-000001"
os.environ["MOBILE_PAIRING_KEY_HEX"] = "2" * 64

from backend import database, models  # noqa: E402

OUT = ROOT / "frontend" / "artifacts" / "v15-03-a2-fallback-real"
SEED = OUT / "seed.json"
EVIDENCE = OUT / "evidence-after.json"
PATIENTS = (
    ("unique", "G03A2-UNIQUE", "Élodie", "Benmoussa", "1992-05-04", "0612345678"),
    ("collisionA", "G03A2-COLL-A", "Nora", "Collision", "1990-06-07", "0698877665"),
    ("collisionB", "G03A2-COLL-B", "Aya", "Collision", "1990-06-07", "0698877665"),
)


def seed():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = {}
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        assert db.query(models.CabinetConfig).filter_by(owner_id=owner.id).one()
        for key, dossier, first, last, dob, phone in PATIENTS:
            assert db.query(models.Patient).filter_by(
                numero_dossier=dossier, employer_id=owner.id
            ).first() is None
            patient = models.Patient(
                employer_id=owner.id, numero_dossier=dossier,
                prenom=first, nom=last, date_naissance=datetime.fromisoformat(dob),
                sexe="F", telephone=phone,
            )
            db.add(patient)
            db.flush()
            rows[key] = {"patientId": patient.id, "displayName": first + " " + last}
        db.commit()
    SEED.write_text(json.dumps({"lab": "G03-A2-FALLBACK", "patients": rows}, indent=2), encoding="utf-8")
    print("G03_A2_SYNTHETIC_SEED_PASS patients=3 appointments=0")


def expire_session(session_id):
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        row = db.query(models.WorkstationPatientSession).filter_by(
            id=session_id, employer_id=owner.id, claimed_at=None, purged_at=None
        ).one()
        row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    print("G03_A2_EXPIRY_INJECTED")


def verify():
    patients = json.loads(SEED.read_text(encoding="utf-8"))["patients"]
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    exact_sha = os.environ.get("EVALUATED_SHA", "")
    assert len(exact_sha) == 40 and all(c in "0123456789abcdef" for c in exact_sha), "missing exact SHA"
    checkout_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=10
    ).strip()
    assert evidence["head"] == exact_sha == checkout_sha, "CI checkout/artifact SHA mismatch"
    assert evidence["cases"].get("phone_success") is True
    assert evidence["cases"].get("name_success") is True
    assert evidence["cases"].get("collision_lock") == [403, 403, 403, 403, 429]
    assert evidence["cases"].get("regen_locked") == 429
    assert evidence["cases"].get("wrong_pin") == 403
    assert evidence["cases"].get("disabled") == 403
    assert evidence["cases"].get("wrong_station") == 404
    assert evidence["cases"].get("wrong_dob_unknown") == [403, 403]
    assert evidence["cases"].get("other_station_accepted") == 200
    assert evidence["cases"].get("expiry") in (404, 409)
    assert len(evidence["screenshots"]) >= 10, "missing before/after visual artifacts"
    manifest = evidence["screenshotManifest"]
    assert set(evidence["screenshots"]) == set(manifest), "screenshot manifest mismatch"
    assert len(evidence["screenshots"]) == len(set(evidence["screenshots"])), "duplicate screenshot name"
    for filename, spec in manifest.items():
        assert filename.endswith(".png") and Path(filename).name == filename, "unsafe screenshot name"
        raw = (OUT / filename).read_bytes()
        assert len(raw) >= 1000 and raw[:8] == b"\x89PNG\r\n\x1a\n", "invalid PNG proof"
        w = int.from_bytes(raw[16:20], "big")
        h = int.from_bytes(raw[20:24], "big")
        assert w == spec["width"] and h == spec["height"], "PNG header mismatch"
        assert len(raw) == spec["bytes"], "PNG size mismatch"
        assert hashlib.sha256(raw).hexdigest() == spec["sha256"], "PNG integrity mismatch"
    assert {390, 430, 768, 1280}.issubset(
        {int(spec["width"]) for spec in manifest.values()}
    ), "missing required responsive viewport"
    for image in (
        "03-phone-identified-after.png",
        "04-name-normalized-after.png",
        "07-invalid-dob-and-phone-denied.png",
        "08-expired-session-verified.png",
        "10-collision-locked-after.png",
    ):
        assert image in manifest, "missing essential AFTER screenshot: " + image
    assert not any(item.get("pageerror") for item in evidence["http"]), "browser runtime error"
    assert all("stationSession=" not in json.dumps(item) for item in evidence["http"]), "QR bearer leakage"
    owner_station = evidence["actors"]["kiosk"]
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        sessions = db.query(models.WorkstationPatientSession).filter_by(
            workstation_id=owner_station, employer_id=owner.id
        ).all()
        failure_count = sum(int(row.fallback_failed_attempts or 0) for row in sessions)
        assert failure_count >= 5, f"Missing persistent lock attempts: {failure_count}"
        audits = db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == owner.id,
            models.AuditLog.action == "STATION_PATIENT_FALLBACK_IDENTIFIED",
        ).all()
        assert len(audits) >= 2, "Successful fallback identity not independently audited twice"
        sensitive = ("0612345678", "0698877665", "1992-05-04", "1990-06-07")
        assert all(not any(secret in (audit.details or "") for secret in sensitive) for audit in audits)
        ids = [x["patientId"] for x in patients.values()]
        assert db.query(models.Patient).filter(models.Patient.id.in_(ids)).count() == 3
        assert db.query(models.Appointment).filter(models.Appointment.patient_id.in_(ids)).count() == 0
        result = {
            "status": "PASS", "head": exact_sha, "environment": "disposable SQLCipher SQLite",
            "seedPatients": 3, "appointmentCount": 0,
            "successfulFallbackAuditEvents": len(audits),
            "stationFailureCount": failure_count,
            "blockedRegeneration": True, "noClinicalArrivalMutation": True,
            "auditCredentialsExcluded": True,
            "wrongDobAndUnknownPhoneRefused": True,
            "crossStationDenied": True,
            "expiredSessionDenied": True,
            "visualCaptures": len(evidence["screenshots"]),
            "verifiedViewports": sorted({int(spec["width"]) for spec in manifest.values()}),
            "screenManifestSha256": hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode("utf-8")
            ).hexdigest()
        }
    (OUT / "sql-after.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("G03_A2_INDEPENDENT_SQL_PASS " + json.dumps(result))


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
