"""FUE-H seed: one genuinely empty fictitious orthodontic patient on isolated T2.

Unlike FUE-G, NO cephalo image, analysis, measurement or landmark is pre-seeded.
All radio studies must be created by actual authenticated UI uploads.
"""
import json
import os
from datetime import datetime
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if (os.environ.get("ENVIRONMENT")!="test"
    or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME")!="1"
    or os.environ.get("DATABASE_URL")!="sqlite:///./t2-runtime-cert.db"
    or not Path("t2-runtime-cert.db").is_file()):
    raise RuntimeError("FUE-H refuses non-disposable database")

from backend import database, models

with database.SessionLocal() as db:
    dentist=db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
    if db.query(models.Patient).filter_by(numero_dossier="T2-FUEH-0001").first():
        raise RuntimeError("FUE-H must start with a NEW fictitious patient")
    patient=models.Patient(
        numero_dossier="T2-FUEH-0001",
        nom="RADIO-PUBLIQUE", prenom="FUEH-TEST",
        date_naissance=datetime(1990,1,1), sexe="M",
        employer_id=dentist.id,
        telephone="0600000000",
        email="fueh-test@example.com",
        assurance="AUCUNE",
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id,is_ortho_active=True))
    db.commit()
    if db.query(models.CephaloAnalysis).filter_by(patient_id=patient.id).count()!=0:
        raise RuntimeError("FUE-H not a blank first use")
    print("CEPH_R23H_EMPTY_TEST_PATIENT="+json.dumps({
        "patient_id":patient.id,"numero_dossier":"T2-FUEH-0001",
        "initial_studies":0,"clinical_release":False,
    }),flush=True)
