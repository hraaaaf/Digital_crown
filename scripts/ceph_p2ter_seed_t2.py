"""P2ter ONLY: create two nonpatient versioned ceph study records on disposable T2.

Run only against isolated sqlite t2-runtime-cert.db after T2 fixture server starts.
Does not change runtime code, clinical references, hardware or real patient rows.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

if os.getenv("ENVIRONMENT") != "test" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise RuntimeError("P2ter seed requires disposable isolated test runtime")
if os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db":
    raise RuntimeError("Refusing any other database path")
path = Path("t2-runtime-cert.db").resolve()
if not path.is_file() or path.name != "t2-runtime-cert.db":
    raise RuntimeError("T2 database missing")

from backend import models, database
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

with database.SessionLocal() as db:
    owner = db.query(models.User).filter(models.User.email == "t2-browser@cabinet.ma").one()
    patient = db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-0001",
        models.Patient.employer_id == owner.id,
    ).one()
    clinical = db.query(models.DossierClinique).filter(
        models.DossierClinique.patient_id == patient.id,
    ).one()
    clinical.is_ortho_active = True

    points = [
        {"id": name, "x": float(100 + i * 2), "y": float(120 + i * 3)}
        for i, name in SOTA_LANDMARKS_MAPPING.items()
    ]
    if len(points) != 38:
        raise RuntimeError("SOTA synthetic landmark count changed")
    ratio = 0.2
    calibration = {
        "method": "MANUAL_TWO_POINT", "state": "MANUAL_TWO_POINT",
        "p1": {"x": 100.0, "y": 100.0},
        "p2": {"x": 200.0, "y": 100.0},
        "distance_mm": 20.0,
    }
    result = cephalo_safe_engine.calculate_metrics(
        {p["id"]: (p["x"], p["y"]) for p in points},
        custom_mm_ratio=ratio,
    )
    ids = []
    for suffix in ("OLDER_A", "LATEST_B"):
        image = "api/static/uploads/radios/t2-cephalo-seeded.png"
        graph = build_cephalo_runtime_evidence_payload(
            patient_id=patient.id,
            image_record_id=image,
            result=result,
            landmarks=points,
            inference_mode="SOTA_ONNX_38",
            is_calibrated=True,
            calibration_data=calibration,
            case_id=f"p2ter:synthetic:{patient.id}:{suffix}",
        )
        study = models.CephaloAnalysis(
            patient_id=patient.id, image_original_path=image,
            landmarks_data=points,
            angles_data={**result.model_dump(), EVIDENCE_GRAPH_KEY: graph},
            is_calibrated=True, mm_per_pixel=ratio, calibration_data=calibration,
        )
        db.add(study)
        db.flush()
        ids.append(study.id)
    db.commit()
    assert ids[0] < ids[1]
    print("P2TER_SYNTHETIC_STUDIES="+json.dumps({
        "patient_id":patient.id, "older_id":ids[0], "latest_id":ids[1],
    }), flush=True)
