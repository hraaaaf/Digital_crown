"""03B.3f — isolated, real HTTP FastAPI server for browser Step1 certification.

This is an ephemeral CI-only process. It never contacts or opens a cabinet DB.
Test-only user/patients are seeded in shared in-memory SQLite; clinical service,
SRPose38 ONNX inference and regular auth/routes are not mocked. Only external
background synthesis and ruler candidate detection are neutralized.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"
assert os.environ.get("DC_CEPH03B3F_ACK") == "synthetic-only"
assert os.environ.get("CLOUD_AI_ENABLED") == "false"

# Imported test infrastructure sets up a StaticPool SQLite DB, without a real
# cabinet or external data. Use the same user factory as authenticated tests.
from backend.tests.conftest import _engine, _SessionLocal, make_user
from backend import database, models
from backend.models_document_provenance_p3 import install_document_provenance_p3

database.engine = _engine
database.SessionLocal = _SessionLocal
install_document_provenance_p3()
models.Base.metadata.create_all(bind=_engine)

from backend.main import app
from backend.routers import ia
from backend.core import media_paths
from backend.services.calibration_service import calibration_service
from backend.services.sota_vision_service import sota_vision_engine
from backend.services.cmo_agent_service import cmo_agent

assert sota_vision_engine.is_ready, "Real pinned SRPose38 ONNX must be loaded"

def isolated_db():
    with _SessionLocal() as db:
        yield db

app.dependency_overrides[database.get_db] = isolated_db
calibration_service.detect_candidate = lambda _path: None
cmo_agent.generate_global_synthesis = lambda *_args, **_kwargs: None

with TemporaryDirectory(prefix="dc-ceph03b3f-") as scratch:
    root = Path(scratch) / "imaging"
    root.mkdir(parents=True, exist_ok=True)
    # Upload and authenticated media readback must use the same isolated root.
    ia.get_imaging_root = lambda: root
    media_paths.get_imaging_root = lambda: root

    with _SessionLocal() as db:
        doctor = make_user(db, email="ceph03b3f-synthetic-doctor@cabinet.test")
        patient_ids = {}
        for film in ("A", "B"):
            patient = models.Patient(
                nom="SYNTHETIC-ONLY",
                prenom=f"PUBLIC-CEPH-{film}",
                date_naissance=datetime(2000, 1, 1),
                sexe="M",
                employer_id=doctor.id,
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            patient_ids[film] = patient.id

    out = Path(os.environ["DC_CEPH03B3F_METADATA"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "scope": "SYNTHETIC_ONLY_LIVE_HTTP_BACKEND_NO_PATIENT_DATA",
        "patient_ids": patient_ids,
        "doctor_email": "ceph03b3f-synthetic-doctor@cabinet.test",
        # The password belongs to a disposable account in ephemeral CI only.
    }), encoding="utf-8")
    print("DC_CEPH03B3F_EPHEMERAL_HTTP_READY", flush=True)

    import uvicorn
    # Lifespan OFF: prohibit production seed, scheduler and external connectors;
    # the app's actual routers, auth dependencies and ML runtime remain active.
    uvicorn.run(app, host="127.0.0.1", port=8005, lifespan="off", log_level="warning", access_log=False)
