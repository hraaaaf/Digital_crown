"""QA-only: two separately persisted SYNTHETIC CEPHALO records on disposable T2.

No actual radiographs, no legitimate clinical interpretation; the purpose is to
prove an authenticated source link and independent R-only T0/T1 panel binding.
Never run against a cabinet database, patient data, staging or production.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
target = "sqlite:///./t2-runtime-cert.db"
if (
    os.getenv("ENVIRONMENT") != "test"
    or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
    or os.getenv("DATABASE_URL") != target
    or Path.cwd().resolve() != ROOT.resolve()
    or Path("t2-runtime-cert.db").resolve() != (ROOT / "t2-runtime-cert.db").resolve()
    or not Path("t2-runtime-cert.db").is_file()
):
    raise RuntimeError("REFUSED: R3 CEPHALO QA requires isolated disposable T2 runtime")
from backend.core.runtime_safety import database_target_fingerprint, is_known_cabinet_database

if is_known_cabinet_database(target) or (
    os.getenv("DIGITALCROWN_ISOLATION_DB_FINGERPRINT") != database_target_fingerprint(target)
):
    raise RuntimeError("REFUSED: R3 CEPHALO QA database identity mismatch")

from backend import database, models

with database.SessionLocal() as db:
    owner = db.query(models.User).filter(
        models.User.email == "t2-browser@cabinet.ma"
    ).one()
    patient = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-0001",
        models.Patient.employer_id == owner.id,
    ).one()
    ids = {}
    for ordinal, angles in (
        (0, {"SNA": 82.0, "SNB": {"valeur": 80.0}}),
        (1, {"SNA": 83.2, "SNB": {"valeur": 79.5}}),
    ):
        # No image content or inferred landmarks: explicit non-clinical test fixture.
        marker = f"QA_SYNTHETIC_R3_T{ordinal}_NO_RADIOGRAPH.png"
        if db.query(models.CephaloAnalysis).filter(
            models.CephaloAnalysis.patient_id == patient.id,
            models.CephaloAnalysis.image_original_path == marker,
        ).first():
            raise RuntimeError("REFUSED: fixture is not a fresh isolated T2 database")
        analysis = models.CephaloAnalysis(
            patient_id=patient.id,
            image_original_path=marker,
            landmarks_data={},
            angles_data=angles,
            is_calibrated=True,
            mm_per_pixel=0.2,
        )
        db.add(analysis)
        db.flush()
        ids[ordinal] = analysis.id
    assert ids[0] != ids[1] and ids[0] > 0 and ids[1] > 0
    db.commit()
    print(f"R3_T2_CEPHALO_T0_ID={ids[0]}", flush=True)
    print(f"R3_T2_CEPHALO_T1_ID={ids[1]}", flush=True)
