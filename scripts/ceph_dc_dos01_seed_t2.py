"""DC-DOS-01 synthetic multi-patient/tenant FUE fixture; disposable T2 ONLY.

Creates patient B in cabinet A, patient X in a separate cabinet, and a
versioned science study for B. No production DB, real patient or official PDF.
Executed after the existing authenticated four-step FUE so its IDs remain stable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if (os.getenv("ENVIRONMENT") != "test"
        or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
        or os.getenv("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"):
    raise RuntimeError("DC-DOS-01 requires the exact disposable isolated T2 database")
if not Path("t2-runtime-cert.db").is_file():
    raise RuntimeError("Refusing to seed a non-existent disposable T2 database")
password = os.getenv("T2_PASSWORD")
studies = json.loads(os.getenv("P2TER_STUDIES", "{}"))
if not password or not all(isinstance(studies.get(k), int) for k in
                           ("patient_id", "older_id", "latest_id")):
    raise RuntimeError("Missing signed-off synthetic T2 fixture context")

import fitz
from PIL import Image
from backend import database, models
from backend.security import get_password_hash
from backend.services.archive_service import ArchiveService
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload,
)
from backend.services.cephalo_landmark_correction_evidence import (
    rebuild_evidence_after_landmark_edit,
)
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path

with database.SessionLocal() as db:
    owner = db.query(models.User).filter(
        models.User.email == "t2-browser@cabinet.ma"
    ).one()
    source_a = db.query(models.Patient).filter(
        models.Patient.id == studies["patient_id"],
        models.Patient.employer_id == owner.id,
    ).one()
    source_study = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.id == studies["older_id"],
        models.CephaloAnalysis.patient_id == source_a.id,
    ).one()

    if db.query(models.Patient).filter(
        models.Patient.numero_dossier == "T2-DC-DOS01-B"
    ).first():
        raise RuntimeError("Disposable DC-DOS01 fixture must be new")

    patient_b = models.Patient(
        numero_dossier="T2-DC-DOS01-B", nom="SYNTHETIC_B",
        prenom="CABINET_A", date_naissance=datetime(1992, 1, 1),
        sexe="F", employer_id=owner.id,
    )
    db.add(patient_b)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient_b.id, is_ortho_active=True))

    user_x = models.User(
        email="t2-dos01-foreign@cabinet.ma",
        hashed_password=get_password_hash(password),
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Synthetic Foreign Cabinet",
        is_active=True, is_licensed=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
    )
    db.add(user_x)
    db.flush()
    db.add(models.CabinetConfig(
        owner_id=user_x.id, nom_cabinet="CABINET_X_SYNTHETIC",
        nom_praticien="Dr Synthetic Foreign Cabinet",
        is_initialized=True, hide_header=False, hide_footer=False,
    ))
    patient_x = models.Patient(
        numero_dossier="T2-DC-DOS01-X", nom="SYNTHETIC_X",
        prenom="CABINET_X", date_naissance=datetime(1993, 1, 1),
        sexe="M", employer_id=user_x.id,
    )
    db.add(patient_x)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient_x.id, is_ortho_active=True))

    # Same synthetic plate, DIFFERENT clinical case and scientific graph.
    # Do not clone the source patient's case_id or stage/clinician receipts.
    full_points = source_study.landmarks_data
    initial_points = [p for p in full_points
                      if p["id"] not in ("Occ_Ant", "Occ_Post")]
    if len(initial_points) != 38 or len(full_points) != 40:
        raise RuntimeError("Source study is not the approved T2 38+2 fixture")
    ratio = source_study.mm_per_pixel
    calibration = source_study.calibration_data
    if ratio != 0.2 or not isinstance(calibration, dict):
        raise RuntimeError("Synthetic calibration contract changed")
    source_result = cephalo_safe_engine.calculate_metrics(
        {p["id"]: (p["x"], p["y"]) for p in initial_points},
        custom_mm_ratio=ratio,
    )
    case_id = f"dc-dos01:synthetic:{patient_b.id}:b"
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=patient_b.id,
        image_record_id=source_study.image_original_path,
        result=source_result,
        landmarks=initial_points,
        inference_mode="SOTA_ONNX_38",
        is_calibrated=True,
        calibration_data=calibration,
        case_id=case_id,
    )
    revised = cephalo_safe_engine.calculate_metrics(
        {p["id"]: (p["x"], p["y"]) for p in full_points},
        custom_mm_ratio=ratio,
    )
    graph = rebuild_evidence_after_landmark_edit(
        previous_payload=graph,
        patient_id=patient_b.id,
        image_record_id=source_study.image_original_path,
        result=revised,
        runtime_landmarks=full_points,
        clinician_id=str(owner.id),  # only a synthetic provenance, no signoff
        validated_at=datetime.now(timezone.utc),
    )
    payload = {**revised.model_dump(), EVIDENCE_GRAPH_KEY: graph}
    verified = project_runtime_chain_read_path(payload, patient_id=patient_b.id)
    if (verified["scientific_read_path"]["revision"] != 2
            or verified["scientific_read_path"]["active_chain"] != "VERIFIED"):
        raise RuntimeError("Synthetic patient B graph integrity could not be verified")
    study_b = models.CephaloAnalysis(
        patient_id=patient_b.id,
        image_original_path=source_study.image_original_path,
        landmarks_data=full_points, angles_data=payload,
        is_calibrated=True, mm_per_pixel=ratio,
        calibration_data=calibration,
    )
    db.add(study_b)
    db.commit()
    db.refresh(study_b)

    image_paths = {}
    for name, color in (("a", (192, 35, 50)), ("b", (22, 115, 192)),
                        ("x", (45, 151, 78))):
        p = Path(f"/tmp/dc-dos01-{name}.png")
        Image.new("RGB", (800, 600), color).save(p, "PNG")
        image_paths[name] = str(p)
    # DC-DOS-02: distinct synthetic, explicitly NON-CLINICAL manual import fixtures.
    # Separate content prevents accidental same-tenant content-address dedup from
    # masking storage-count assertions on the new three original sources.
    from PIL import ImageDraw
    dos02_imports = {}
    for media_type, code, color in (
        ("PHOTO", "photo", (60, 135, 175)),
        ("RADIOGRAPH", "radio", (135, 135, 135)),
    ):
        filename = Path(f"/tmp/dc-dos02-a-{code}.png")
        sample = Image.new("RGB", (920, 720), color)
        drawer = ImageDraw.Draw(sample)
        drawer.text((70, 95), f"DC-DOS02 SYNTHETIC {media_type} - NOT CLINICAL", fill=(0, 0, 0))
        sample.save(filename, "PNG")
        data = filename.read_bytes()
        dos02_imports[code] = {"path": str(filename), "sha256": hashlib.sha256(data).hexdigest()}
    filename = Path("/tmp/dc-dos02-a-document.pdf")
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((65, 90), "DC-DOS02 SYNTHETIC IMPORTED PDF - NOT CLINICAL")
        filename.write_bytes(pdf.tobytes(garbage=4, deflate=True))
    dos02_imports["document"] = {
        "path": str(filename), "sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
    }
    # Real, readable PDF bytes, but ONLY generic NON-CLINICAL test archives.
    # Never forge RAPPORT_CEPHALO, practitioner signatures or a final A4.
    archives = {}
    for code, patient, practitioner in (
        ("a", source_a, owner), ("b", patient_b, owner), ("x", patient_x, user_x),
    ):
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text(
                (60, 80), f"DC-DOS01 SYNTHETIC TEST PDF {code.upper()} - NOT CLINICAL"
            )
            data = pdf.tobytes(garbage=4, deflate=True)
        doc, _ = ArchiveService(db).archive_document(
            patient_id=patient.id,
            file_content=data,
            filename=f"DC-DOS01-SYNTH-{code.upper()}.pdf",
            doc_type=models.DocumentType.AUTRE,
            uploaded_by_id=practitioner.id,
            title="TEST ONLY - DO NOT SIGN",
        )
        if (doc.patient_id != patient.id
                or doc.document_type != models.DocumentType.AUTRE
                or doc.file_hash != hashlib.sha256(data).hexdigest()):
            raise RuntimeError("DC-DOS-01 synthetic archive provenance mismatch")
        archives[code] = {"id": doc.id, "sha256": doc.file_hash}
    if len({archives[k]["id"] for k in archives}) != 3:
        raise RuntimeError("DC-DOS-01 synthetic archive identities collided")
    fixture = {
        "patient_a": source_a.id, "study_a": source_study.id,
        "patient_b": patient_b.id, "study_b": study_b.id,
        "patient_x": patient_x.id, "tenant_x_user": user_x.id,
        "images": image_paths, "archives": archives,
        "dos02_imports": dos02_imports, "synthetic_only": True,
    }
    print("DC_DOS01_SYNTHETIC_FIXTURE="+json.dumps(fixture), flush=True)
