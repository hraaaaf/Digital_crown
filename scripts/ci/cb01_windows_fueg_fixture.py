"""CB-01 Windows FUE-G: exact-HEAD synthetic staff and immutable clinical snapshot.

This isolated GitHub Actions fixture is not production, not cabinet data and
not a human E2E. It captures only table names/counts/hashes, never patient rows.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BASELINE = Path(os.environ.get("RUNNER_TEMP", ".")) / "cb01-windows-fueg-before.json"
OUTPUT = ROOT / "artifacts" / "cb01-windows-fueg-combined" / "clinical-final-state.json"
ALLOWED = {"audit_logs", "workstation_modes"}


def verify_runtime() -> str:
    expected = os.getenv("CB01_SOURCE_HEAD", "")
    if (os.getenv("GITHUB_ACTIONS") != "true"
        or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
        or os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"
        or not (ROOT / "t2-runtime-cert.db").is_file()
        or not expected or len(expected) != 40
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != expected):
        raise SystemExit("REFUSED: Windows FUE-G requires exact-head GitHub isolated synthetic SQLite")
    if not os.getenv("T2_PASSWORD"):
        raise SystemExit("REFUSED: synthetic staff password not available")
    return expected


def fingerprint(db) -> dict:
    from sqlalchemy import inspect, text
    names = sorted(n for n in inspect(db.bind).get_table_names() if not n.startswith("sqlite_"))
    if len(names) < 20 or not {"patients", "appointments"}.issubset(names):
        raise SystemExit("FAIL: missing synthetic clinical schema")
    data = {}
    for name in names:
        q = '"' + name.replace('"', '""') + '"'
        h = hashlib.sha256()
        count = 0
        for row in db.execute(text(f"SELECT * FROM {q}")):
            h.update((repr(tuple(row)) + "\n").encode("utf8"))
            count += 1
        data[name] = {"rows": count, "sha256": h.hexdigest()}
    return data


def seed(db) -> None:
    from backend import models
    from backend.security import get_password_hash
    from backend.routers.agenda_settings import _create_default_settings, _settings_row
    owner = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
    foreign = db.query(models.User).filter(models.User.email == "t2-setup-390@cabinet.ma").one()
    if owner.id == foreign.id or owner.employer_id is not None:
        raise SystemExit("FAIL: synthetic tenant setup invalid")
    password = get_password_hash(os.environ["T2_PASSWORD"])
    for email, agenda in [
        ("t2-s05-reception@cabinet.ma", True),
        ("t2-s06-no-agenda@cabinet.ma", False),
    ]:
        staff = db.query(models.User).filter(models.User.email == email).one_or_none()
        if staff is None:
            staff = models.User(
                email=email, hashed_password=password, role=models.UserRole.SECRETAIRE,
                nom_complet="Synthetic S05" if agenda else "Synthetic S06",
                is_active=True, is_licensed=True,
                approval_status=models.ApprovalStatus.APPROVED.value,
                employer_id=owner.id,
                permissions={"agenda": agenda, "patients": True,
                             "accounting": False, "clinical": False, "settings": False,
                             "admin": False},
            )
            db.add(staff)
            db.commit()
        if staff.employer_id != owner.id or staff.permissions.get("agenda") is not agenda:
            raise SystemExit("FAIL: synthetic staff permissions mismatch")
    for identity in [owner, foreign]:
        if _settings_row(db, identity.id) is None:
            _create_default_settings(db, identity.id)
        assert _settings_row(db, identity.id) is not None
    patient = db.query(models.Patient).filter(
        models.Patient.employer_id == owner.id,
        models.Patient.numero_dossier == "T2-0001").one()
    assert patient.deleted_at is None


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"before", "after"}:
        raise SystemExit("usage: cb01_windows_fueg_fixture.py before|after")
    head = verify_runtime()
    from backend import database
    with database.SessionLocal() as db:
        if sys.argv[1] == "before":
            seed(db)
            result = {"sourceHead": head, "tables": fingerprint(db)}
            BASELINE.write_text(json.dumps(result, indent=2), encoding="utf8")
            print("CB01_WINDOWS_FUEG_BASELINE: RECORDED",len(result["tables"]),"tables")
            return
        if not BASELINE.exists():
            raise SystemExit("FAIL: missing Windows exact-head clinical baseline")
        before = json.loads(BASELINE.read_text(encoding="utf8"))
        if before.get("sourceHead") != head:
            raise SystemExit("FAIL: baseline HEAD does not match")
        after = fingerprint(db)
    changed = sorted(name for name in set(after) | set(before["tables"])
                     if after.get(name) != before["tables"].get(name))
    nontechnical = sorted(set(changed) - ALLOWED)
    proof = {
        "sourceHead": head, "kind": "WINDOWS_FUEG_ALL_SYNTHETIC_SQLITE_TABLES_FINAL_STATE",
        "tablesChecked": len(after), "clinicalTablesChanged": nontechnical,
        "technicalExceptions": sorted(set(changed) & ALLOWED),
        "technicalAllowlist": sorted(ALLOWED),
        "status": "PASS_CLINICAL_FINAL_STATE_UNCHANGED" if not nontechnical else "FAIL_CLINICAL_TABLE_CHANGED",
        "humanE2EValidated": 0,
        "limitation": "Final state in isolated synthetic SQLite only; transient writes not detected; no human cabinet validation."
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(proof, indent=2), encoding="utf8")
    if nontechnical:
        raise SystemExit("FAIL: Windows FUE-G changed clinical tables: " + ",".join(nontechnical))
    print("CB01_WINDOWS_FUEG_CLINICAL_STATE: PASS",len(after),"tables",
          "technical exceptions", ",".join(proof["technicalExceptions"]))


if __name__ == "__main__":
    main()
