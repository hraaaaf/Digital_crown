"""03B.3d experimental: real pinned SRPose38 through auth upload + SQLite.

True ONNX inference drives CephaloService.process_new_radio through its
normal HTTP upload route. Ruler candidate and background task are isolated.
No anatomical ground truth or valid patient-facing measurement claimed.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session

from backend import models
from backend.services.sota_vision_service import sota_vision_engine

MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "frontend/scripts/fixtures/dc-ceph03b3c-public-cephalograms.json"
)
STAGED = "DC_CEPH03B3C_RADIO_DIR"


def _radiographs():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "CC BY-SA" in manifest["attribution_notice"]
    assert len(manifest["images"]) == 2
    source_dir = os.environ.get(STAGED)
    assert source_dir, f"{STAGED} must point to isolated, verified public media"
    for meta in manifest["images"]:
        file = Path(source_dir) / meta["file_name"]
        raw = file.read_bytes()
        assert len(raw) == meta["size_bytes"], meta["id"]
        assert hashlib.sha1(raw).hexdigest() == meta["sha1"], meta["id"]
        with Image.open(file) as opened:
            assert opened.format == "JPEG", meta["id"]
            assert opened.size == (meta["width"], meta["height"]), meta["id"]
            opened.verify()
        yield meta, file, raw


def test_real_srpose38_two_lateral_xrays_authenticated_upload_edit_sqlite_reload(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    # Test data must NEVER be uploaded to a real cabinet or bound to a real patient.
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    assert os.environ.get("ENVIRONMENT") == "test"
    films = list(_radiographs())

    # Actual ONNX landmarks are sent through the upload route, not compared
    # against any independently verified anatomical reference.
    from backend.routers import ia
    from backend.services import cephalo_service, calibration_service
    imaging_root = tmp_path / "imaging"
    imaging_root.mkdir()
    monkeypatch.setattr(ia, "get_imaging_root", lambda: imaging_root)
    monkeypatch.setattr(calibration_service.calibration_service, "detect_candidate", lambda _: None)
    assert sota_vision_engine.is_ready, "Pinned SRPose38 not loaded"
    expected_model_sha = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
    model = Path(__file__).resolve().parents[1] / "ai_models/srpose38-tta-1024.onnx"
    assert hashlib.sha256(model.read_bytes()).hexdigest() == expected_model_sha
    # IMPORTANT: exercise the production VisionEngine.predict_landmarks path
    # unmodified. It chooses the ready SRPose38 primary engine itself; the
    # response mode assertion below fails if it ever falls back to legacy ML.
    assert cephalo_service.vision_engine is not None
    export_dir = Path(os.environ["DC_CEPH03B3D_PREDICTIONS_DIR"])
    export_dir.mkdir(parents=True, exist_ok=True)
    import backend.services.cmo_agent_service as cmo_module
    monkeypatch.setattr(cmo_module.cmo_agent, "generate_global_synthesis", lambda *_: None)

    ids = []
    for idx, (meta, _path, raw_bytes) in enumerate(films):
        patient = models.Patient(
            nom="E2E-TEST", prenom=f"PUBLIC-FILM-{meta['id']}",
            date_naissance=datetime(2000, 1, 1),
            sexe="M", employer_id=dentiste.id,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Real multipart request, real API security, real file write, real SQLite.
        upload = client.post(
            f"/api/ia/upload-radio?patient_id={patient.id}",
            files={"file": (meta["file_name"], raw_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert upload.status_code == 200, (meta["id"], upload.text[:800])
        result = upload.json()
        assert result["status"] == "success"
        analysis_id = result["analysis_id"]
        ids.append(analysis_id)
        stored_images = list((imaging_root / "radios").glob("*"))
        assert len(stored_images) == idx + 1
        assert any(hashlib.sha1(p.read_bytes()).hexdigest() == meta["sha1"] for p in stored_images)
        assert result["mm_per_pixel"] is None
        assert result["is_calibrated"] is False

        def authoritative_get():
            response = client.get(f"/api/ia/analyses/{analysis_id}", headers=auth_headers)
            assert response.status_code == 200, response.text[:800]
            return response.json()

        # Never leak real-model radiographic analysis across the auth boundary.
        unauthenticated_read = client.get(f"/api/ia/analyses/{analysis_id}")
        assert unauthenticated_read.status_code in (401, 403)
        unauthenticated_write = client.put(
            f"/api/ia/analyses/{analysis_id}",
            json={"landmarks": result["landmarks"], "mm_per_pixel": None},
        )
        assert unauthenticated_write.status_code in (401, 403)
        baseline = authoritative_get()
        original = baseline["landmarks_data"]
        assert isinstance(original, list) and len(original) == 38
        assert len({p["id"] for p in original}) == 38
        assert original == result["landmarks"]
        assert result["results"]["vision_metadata"]["mode_inference"] == "SOTA_ONNX_38"
        assert all(
            isinstance(p["x"], (float, int)) and isinstance(p["y"], (float, int))
            and __import__("math").isfinite(p["x"]) and __import__("math").isfinite(p["y"])
            for p in original
        )
        assert baseline["mm_per_pixel"] is None
        assert baseline["is_calibrated"] is False
        initial_graph = baseline["angles_data"]["_evidence_graph_v1"]
        revision = initial_graph["revision"]
        assert revision == 1
        auto_n = next(
            p for p in initial_graph["landmarks"]
            if p["landmark_id"] == "N" and p["origin"] == "SRPOSE38_AUTO"
        )
        original_auto_x = auto_n["x"]
        original_auto_y = auto_n["y"]

        def correction(dx):
            # ONNX output has an inference-only confidence field. The strict
            # PUT AnalysisUpdate/LandmarkItem schema intentionally persists
            # only the canonical id/x/y coordinates, not model confidence.
            return [
                {"id": p["id"], "x": p["x"] + (dx if p["id"] == "N" else 0), "y": p["y"]}
                for p in original
            ]

        assert any(p["id"] == "N" for p in original)
        steps = [
            ("key-1", correction(1.0)),
            ("key-shift-10", correction(11.0)),
            ("undo", correction(1.0)),
            ("redo", correction(11.0)),
        ]
        for step, landmarks in steps:
            saved = client.put(
                f"/api/ia/analyses/{analysis_id}",
                headers=auth_headers,
                json={"landmarks": landmarks, "mm_per_pixel": None},
            )
            assert saved.status_code == 200, (meta["id"], step, saved.text[:800])
            # A NEW DB session must observe the durable SQLite commit before
            # asking the authenticated API to re-read the same authoritative state.
            with Session(bind=db.get_bind()) as separate:
                reloaded = separate.get(models.CephaloAnalysis, analysis_id)
                assert reloaded is not None
                assert reloaded.landmarks_data == landmarks, (meta["id"], step, "sqlite")
                assert reloaded.mm_per_pixel is None
            after = authoritative_get()
            assert after["landmarks_data"] == landmarks, (meta["id"], step, "GET")
            assert after["mm_per_pixel"] is None
            assert after["is_calibrated"] is False
            graph = after["angles_data"]["_evidence_graph_v1"]
            assert graph["revision"] == revision + 1, (meta["id"], step, "revision")
            assert graph["revision_reason"] == "LANDMARK_EDIT"
            revision += 1
            corrected = next(
                p for p in graph["landmarks"]
                if p["landmark_id"] == "N" and p["origin"] == "MANUAL_CORRECTED"
            )
            assert corrected["validated_by"] == str(dentiste.id)
            assert corrected["evidence_status"] == "CLINICIAN_VALIDATED"
            assert corrected["evidence_id"] in graph["current_landmark_refs"]
            assert corrected["original_auto_x"] == original_auto_x
            assert corrected["original_auto_y"] == original_auto_y
            assert next(
                p for p in graph["landmarks"]
                if p["landmark_id"] == "N" and p["origin"] == "SRPOSE38_AUTO"
            )["evidence_id"] not in graph["current_landmark_refs"]
        final_read = authoritative_get()
        assert final_read["landmarks_data"] == correction(11.0)
        # Independent visual fixture reads ACTUAL API-derived point snapshots.
        # This is not a live workstation login or clinical provenance verdict.
        bridge = {
            "source": "AUTHENTICATED_SQLITE_API_READ_AFTER_REAL_SRPOSE38_UPLOAD",
            "model_sha256": expected_model_sha,
            "source_image_sha1": meta["sha1"],
            "radio": meta["id"],
            "inference_mode": "SOTA_ONNX_38",
            "clinical_accuracy_evaluated": False,
            "baseline": original,
            "after_redo": final_read["landmarks_data"],
            "is_calibrated": final_read["is_calibrated"],
            "mm_per_pixel": final_read["mm_per_pixel"],
        }
        (export_dir / ("cephalo-" + meta["id"] + "-predictions.json")).write_text(
            json.dumps(bridge, indent=2), encoding="utf-8"
        )
        print("DC_CEPH03B3D_REAL_SRPOSE_AUTH_API_READ", meta["id"], len(original))
    assert len(set(ids)) == 2, "Real radiographs must never overwrite each other's analysis"
    print("DC_CEPH03B3D_REAL_ONNX_TWO_RADIOS_AUTH_SQLITE_READ_AFTER_WRITE_PASS")
