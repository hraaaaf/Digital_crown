"""P2ter ONLY: create two nonpatient versioned ceph study records on disposable T2.

Run only against isolated sqlite t2-runtime-cert.db after T2 fixture server starts.
Does not change runtime code, clinical references, hardware or real patient rows.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if os.getenv("ENVIRONMENT") != "test" or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise RuntimeError("P2ter seed requires disposable isolated test runtime")
_pg_lab = "postgresql://postgres:postgres@127.0.0.1:5432/dc_atomic_synthetic"
pg_lab = (os.getenv("T2_POSTGRES_ATOMIC_LAB") == "1"
          and os.getenv("GITHUB_ACTIONS") == "true"
          and os.getenv("DATABASE_URL") == _pg_lab)
if not pg_lab:
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
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_consistency_validator import cephalo_consistency_validator

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
        # A real SRPose38 acquisition intentionally has only 38 automated points.
        # Complete the UI's two additional occlusal anchors as synthetic *manual*
        # corrections with provenance in this disposable test case only.
        # Never pretend SRPose38 automatically predicted Occ_Ant or Occ_Post.
        manual_points = [
            *points,
            {"id": "Occ_Ant", "x": 145.0, "y": 165.0},
            {"id": "Occ_Post", "x": 185.0, "y": 195.0},
        ]
        corrected_result = cephalo_safe_engine.calculate_metrics(
            {p["id"]: (p["x"], p["y"]) for p in manual_points},
            custom_mm_ratio=ratio,
        )
        corrected_graph = rebuild_evidence_after_landmark_edit(
            previous_payload=graph,
            patient_id=patient.id,
            image_record_id=image,
            result=corrected_result,
            runtime_landmarks=manual_points,
            clinician_id=str(owner.id),  # disposable T2 user, not a clinical sign-off
            validated_at=datetime.now(timezone.utc),
        )
        data = {**corrected_result.model_dump(), EVIDENCE_GRAPH_KEY: corrected_graph}
        scientific = project_runtime_chain_read_path(data, patient_id=patient.id)
        assert scientific["scientific_read_path"]["revision"] == 2
        assert scientific["scientific_read_path"]["active_chain"] == "VERIFIED"
        validation = cephalo_consistency_validator.validate(data)
        if not validation.is_valid:
            raise RuntimeError("Synthetic manual occlusal fixture inconsistent: " + repr(validation.fatals))
        study = models.CephaloAnalysis(
            patient_id=patient.id, image_original_path=image,
            landmarks_data=manual_points,
            angles_data=data,
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
