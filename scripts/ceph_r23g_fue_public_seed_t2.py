"""Seed two source-verified ORIGINAL public cephalograms into an isolated T2 Cabinet.

No landmarks, inferred source graph, calibration, clinical metric or patient material.
This is NOT a scientific reference set and does not certify Ricketts geometry.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if (os.getenv("ENVIRONMENT") != "test"
    or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
    or os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"):
    raise SystemExit("REFUSED: not the disposable isolated T2 environment")
db_file = Path("t2-runtime-cert.db").resolve()
if not db_file.is_file() or db_file.name != "t2-runtime-cert.db":
    raise SystemExit("REFUSED: disposable database absent")

from backend import database, models

SOURCES = {
    "anug": {
        "sha1": "2a284993c666790a72d0c004044b35a92534ce9d",
        "dimensions": (2272, 1818),
        "author": "ANUG",
        "source": "https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG",
    },
    "challiyan": {
        "sha1": "66c74c588af3c54dfc581f8a870c5276c3427498",
        "dimensions": (1000, 1255),
        "author": "Challiyan",
        "source": "https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg",
    },
}
from PIL import Image

source_dir = Path(os.environ.get("CEPH_PUBLIC_SOURCE_DIR", "/tmp/ceph-public-originals"))
media_dir = ROOT / "backend/static/uploads/radios"
assert media_dir.is_dir(), "Protected media root absent"
manifest = {}
with database.SessionLocal() as db:
    owner = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
    patient = db.query(models.Patient).filter_by(
        numero_dossier="T2-0001", employer_id=owner.id
    ).one()
    # The product rightly locks Cephalo when orthodontic follow-up is off.
    # Only enable it for this disposable, synthetic T2 patient (as prior
    # ceph_p2ter_seed_t2.py does); never bypass product permission checks.
    clinical = db.query(models.DossierClinique).filter_by(
        patient_id=patient.id,
    ).one()
    clinical.is_ortho_active = True
    db.flush()
    for name, spec in SOURCES.items():
        original = source_dir / (name + ".jpg")
        data = original.read_bytes()
        if not data.startswith(bytes.fromhex("ffd8ff")):
            raise RuntimeError(name + ": not a JPEG source")
        if hashlib.sha1(data).hexdigest() != spec["sha1"]:
            raise RuntimeError(name + ": original image digest mismatch")
        with Image.open(original) as picture:
            picture.verify()
        with Image.open(original) as picture:
            if picture.size != spec["dimensions"] or picture.format != "JPEG":
                raise RuntimeError(name + ": original image format/dimensions mismatch")
        destination = media_dir / ("t2-fue-public-" + name + ".jpg")
        if destination.exists():
            raise RuntimeError("Do not overwrite an earlier test artifact")
        shutil.copyfile(original, destination)
        stored_data = destination.read_bytes()
        if stored_data != data:
            raise RuntimeError(name + ": protected media bytes changed")
        stored_path = "api/static/uploads/radios/" + destination.name
        if db.query(models.CephaloAnalysis).filter_by(image_original_path=stored_path).first():
            raise RuntimeError(name + ": study already seeded")
        study = models.CephaloAnalysis(
            patient_id=patient.id,
            image_original_path=stored_path,
            landmarks_data=[], angles_data={},
            is_calibrated=False, mm_per_pixel=None, calibration_data=None,
        )
        db.add(study)
        db.flush()
        manifest[name] = {
            "study_id": study.id,
            "sha256": hashlib.sha256(data).hexdigest(),
            "sha1": spec["sha1"],
            "width": spec["dimensions"][0], "height": spec["dimensions"][1],
            "author": spec["author"], "source": spec["source"],
            "license": "CC BY-SA 4.0",
            "source_path": stored_path,
            "landmark_count": 0, "calibration": None,
            "clinical_release": False,
        }
    db.commit()
    for case in manifest.values():
        refreshed = db.get(models.CephaloAnalysis, case["study_id"])
        assert refreshed is not None and refreshed.landmarks_data == []
        assert refreshed.angles_data == {} and refreshed.is_calibrated is False
        assert refreshed.mm_per_pixel is None and refreshed.calibration_data is None
    print("CEPH_R23G_FUE_REAL_PUBLIC_STUDIES=" + json.dumps(
        {"patient_id": patient.id, "cases": manifest, "scientific_goldset": False},
        separators=(",", ":"), sort_keys=True,
    ), flush=True)
