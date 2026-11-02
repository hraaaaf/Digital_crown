#!/usr/bin/env python3
"""A3 synthetic-only tenant/RBAC fixture and independent SQL + PNG proof oracle.

Guarded test database ONLY. The application API, not this script, owns all
post-fixture arrival, staff, call and workstation revocation mutations.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXPECTED_DB = "sqlite:///./t2-runtime-cert.db"
if not (
    os.environ.get("ENVIRONMENT") == "test"
    and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.environ.get("T2_STATION_FUE") == "1"
    and os.environ.get("DATABASE_URL") == EXPECTED_DB
):
    raise SystemExit("A3 FAIL CLOSED: isolated synthetic T2 DB and flags required")

os.environ["SECRET_KEY"] = "t2-runtime-certification-secret-key-000001"
os.environ["MOBILE_PAIRING_KEY_HEX"] = "2" * 64

from backend import database, models  # noqa: E402
from backend.security import get_password_hash  # noqa: E402

OUT = ROOT / "frontend" / "artifacts" / "v15-03-a3-real"
BASE_OUT = ROOT / "frontend" / "artifacts" / "v15-03-real-integration"
FOREIGN_EMAIL = "a3-other-owner@cabinet.ma"
RESTRICTED_EMAIL = "a3-no-agenda@cabinet.ma"
FOREIGN_DOSSIER = "A3-OTHER-FICTIF"


def seed():
    password = os.environ.get("T2_PASSWORD")
    if not password:
        raise SystemExit("A3 FAIL CLOSED: generated T2_PASSWORD required")
    OUT.mkdir(parents=True, exist_ok=True)
    with database.SessionLocal() as db:
        owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
        assert db.query(models.User).filter_by(email=FOREIGN_EMAIL).first() is None
        foreign = models.User(
            email=FOREIGN_EMAIL,
            hashed_password=get_password_hash(password),
            role=models.UserRole.DENTISTE,
            nom_complet="Foreign Synthetic Dentist",
            is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        restricted = models.User(
            email=RESTRICTED_EMAIL,
            hashed_password=get_password_hash(password),
            role=models.UserRole.SECRETAIRE,
            nom_complet="Restricted Synthetic Secretary",
            employer_id=owner.id,
            permissions={"agenda": False, "patients": False},
            is_active=True, is_licensed=True,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add_all([foreign, restricted])
        db.flush()
        patient = models.Patient(
            numero_dossier=FOREIGN_DOSSIER, nom="OTHER-CABINET-ONLY",
            prenom="Fictive", date_naissance=datetime(1990, 1, 1),
            telephone="0699900999", sexe="F", employer_id=foreign.id,
        )
        db.add(patient)
        db.flush()
        appt = models.Appointment(
            patient_id=patient.id, employer_id=foreign.id,
            datetime_start=datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
            duration_minutes=30, status=models.AppointmentStatus.EN_SALLE_ATTENTE,
            scheduling_type=models.SchedulingType.EXACT_TIME,
            motif="A3 foreign fixture private",
            ticket_number=901,
        )
        db.add(appt)
        db.commit()
        ids = {"primaryOwnerId": owner.id, "foreignOwnerId": foreign.id,
               "foreignAppointmentId": appt.id, "restrictedUserId": restricted.id}
    (OUT / "seed.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")
    print("A3_SYNTHETIC_TENANT_RBAC_SEED_PASS", json.dumps(ids))


def verify():
    fixture = json.loads((OUT / "seed.json").read_text(encoding="utf-8"))
    evidence = json.loads((OUT / "evidence-after.json").read_text(encoding="utf-8"))
    base_evidence = json.loads((BASE_OUT / "evidence-after.json").read_text(encoding="utf-8"))
    expected_sha = os.environ.get("EVALUATED_SHA")
    assert expected_sha and evidence["head"] == base_evidence["head"] == expected_sha
    expected = (
        "crossTenantCallDenied", "crossTenantWallIsolated", "restrictedFeedDenied",
        "restrictedCallDenied", "anonymousCallDenied", "callExpired",
        "revokeDenied", "revokedWallUnavailable", "outageWallUnavailable",
    )
    assert all(evidence["scenarios"].get(k) is True for k in expected), evidence["scenarios"]
    with database.SessionLocal() as db:
        foreign = db.get(models.User, fixture["foreignOwnerId"])
        assert foreign is not None
        foreign_appt = db.get(models.Appointment, fixture["foreignAppointmentId"])
        assert foreign_appt and foreign_appt.employer_id == foreign.id
        assert foreign_appt.ticket_number == 901
        assert foreign_appt.status == models.AppointmentStatus.EN_SALLE_ATTENTE
        owner_id = fixture["primaryOwnerId"]
        workstations = db.query(models.WorkstationMode).filter_by(employer_id=owner_id).all()
        revoked = [w for w in workstations if w.revoked_at is not None]
        active_station = [w for w in workstations if w.revoked_at is None and w.default_experience == "station"]
        active_cabinet = [w for w in workstations if w.revoked_at is None and w.default_experience == "cabinet"]
        assert len(revoked) == 1 and len(active_station) >= 2 and len(active_cabinet) >= 1
        audit_actions = ("WORKSTATION_REVOKED", "STATION_STAFF_ASSISTANCE_REQUESTED",
                         "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED", "STATION_WALL_PATIENT_CALLED")
        all_audits = db.query(models.AuditLog).filter_by(employer_id=owner_id).all()
        counts = {a: sum(log.action == a for log in all_audits) for a in audit_actions}
        assert counts == {
            "WORKSTATION_REVOKED": 1,
            "STATION_STAFF_ASSISTANCE_REQUESTED": 1,
            "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED": 1,
            "STATION_WALL_PATIENT_CALLED": 2,
        }, counts
    images = {}
    for folder, prefix in ((BASE_OUT, "g03.21"), (OUT, "a3")):
        for f in folder.glob("*.png"):
            raw = f.read_bytes()
            assert raw[:8] == b"\x89PNG\r\n\x1a\n", f
            images[prefix + "/" + f.name] = {
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)
            }
    assert len([k for k in images if k.startswith("g03.21/")]) == 12
    assert len([k for k in images if k.startswith("a3/")]) >= 3
    report = {
        "status": "PASS", "head": expected_sha, "isolation": "synthetic disposable T2",
        "revokedStationCount": len(revoked), "activeStationCount": len(active_station),
        "auditCounts": counts, "foreignAppointmentUnchanged": True,
        "cases": evidence["scenarios"], "screenshots": images,
    }
    (OUT / "sql-after.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "sha256-manifest.json").write_text(
        json.dumps({"head": expected_sha, "images": images}, indent=2), encoding="utf-8"
    )
    print("A3_INDEPENDENT_SQL_PNG_SHA_PASS", json.dumps({
        "head": expected_sha, "screenshots": len(images),
        "audits": counts, "revoked": len(revoked),
    }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify() if args.verify else seed()
