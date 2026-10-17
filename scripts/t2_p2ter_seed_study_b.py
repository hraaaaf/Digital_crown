"""Seed a second synthetic cephalo study in the disposable T2 Cabinet E2E DB.

MUST run only with ENVIRONMENT=test and DIGITALCROWN_ISOLATED_RUNTIME=true.
Never modifies real patient databases or the clinical algorithm.
"""
import os
import sys
import shutil
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if os.environ.get("ENVIRONMENT") != "test" or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"true", "1"}:
    raise SystemExit("P2TER E2E fixture refused: not an isolated synthetic runtime")
if os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
    raise SystemExit("P2TER E2E fixture refused: unexpected database")

from backend import database, models

with database.SessionLocal() as db:
    user = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
    patient = db.query(models.Patient).filter_by(numero_dossier="T2-0001", employer_id=user.id).one()
    a = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient.id,
        models.CephaloAnalysis.image_original_path.like("%t2-cephalo-seeded.png"),
    ).one()
    target = "api/static/uploads/radios/p2ter-synthetic-study-B.png"
    b = db.query(models.CephaloAnalysis).filter_by(
        patient_id=patient.id, image_original_path=target,
    ).first()
    if b is None:
        root = Path(__file__).resolve().parents[1] / "backend" / "static" / "uploads" / "radios"
        src = root / "t2-cephalo-seeded.png"
        if not src.is_file():
            raise SystemExit("T2 source synthetic radiograph missing")
        shutil.copyfile(src, root / "p2ter-synthetic-study-B.png")
        landmarks = deepcopy(a.landmarks_data)
        next(p for p in landmarks if p["id"] == "A")["x"] += 20.0
        source_angles = deepcopy(a.angles_data or {})
        source_angles["vision_metadata"] = {"mode_inference": "P2TER_SYNTHETIC_B_ISOLATED"}
        b = models.CephaloAnalysis(
            patient_id=patient.id, image_original_path=target,
            landmarks_data=landmarks, angles_data=source_angles,
            is_calibrated=a.is_calibrated, mm_per_pixel=a.mm_per_pixel,
            calibration_data=deepcopy(a.calibration_data),
        )
        db.add(b)
        db.commit()
        db.refresh(b)
    assert a.id != b.id
    print(f"P2TER_SEED patient_id={patient.id} A={a.id} B={b.id}", flush=True)
