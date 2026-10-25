"""LOT07 R2 FUE-I: synthetic second patient ONLY in disposable T2 database.

Never point at clinical data, master database, or remote service. The actual
runtime seeds synthetic patient A; add B only for one authenticated browser gate.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if (
    os.getenv("ENVIRONMENT") != "test"
    or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
    or os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"
    or Path("t2-runtime-cert.db").resolve() != (ROOT / "t2-runtime-cert.db").resolve()
):
    raise RuntimeError("REFUSED: R2 only permits the disposable T2 runtime database")
if not (ROOT / "t2-runtime-cert.db").is_file():
    raise RuntimeError("REFUSED: T2 database is missing")

from backend import database, models

with database.SessionLocal() as db:
    owner = db.query(models.User).filter(
        models.User.email == "t2-browser@cabinet.ma"
    ).one()
    patient_a = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-0001",
        models.Patient.employer_id == owner.id,
    ).one()
    patient_b = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-R2-B",
        models.Patient.employer_id == owner.id,
    ).first()
    if patient_b is None:
        patient_b = models.Patient(
            numero_dossier="T2-R2-B",
            nom="SYNTHETIC_B",
            prenom="R2",
            date_naissance=datetime(2000, 1, 1),
            sexe="F",
            employer_id=owner.id,
            telephone="0600000018",
            email="t2-r2-b@example.com",
            assurance="AUCUNE",
        )
        db.add(patient_b)
        db.flush()
        db.add(models.DossierClinique(patient_id=patient_b.id, is_ortho_active=False))
        db.commit()
        db.refresh(patient_b)
    assert patient_a.id != patient_b.id and patient_b.employer_id == owner.id
    print("R2_T2_PATIENT_A_ID=" + str(patient_a.id), flush=True)
    print("R2_T2_PATIENT_B_ID=" + str(patient_b.id), flush=True)
