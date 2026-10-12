"""03B.3c: Two public CC BY-SA cephalograms through REAL authenticated HTTP + SQLite.

Only the ML landmark detector and calibration candidate lookup are stubbed. This
test verifies transport, actual JPEG bytes on disk, audited PUT, database COMMIT,
a freshly opened SQLAlchemy session, and authenticated GET after each edit.
No clinically interpreted landmarks or physical calibration are asserted.
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
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

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


def test_two_real_lateral_xrays_authenticated_upload_save_undo_redo_get(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    # Test data must NEVER be uploaded to a real cabinet or bound to a real patient.
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    assert os.environ.get("ENVIRONMENT") == "test"
    films = list(_radiographs())

    # The real upload route stores the exact pixels; synthetic landmarks avoid
    # using a diagnostic model or misrepresenting an unannotated radiograph.
    from backend.routers import ia
    from backend.services import cephalo_service, calibration_service
    imaging_root = tmp_path / "imaging"
    imaging_root.mkdir()
    monkeypatch.setattr(ia, "get_imaging_root", lambda: imaging_root)
    monkeypatch.setattr(calibration_service.calibration_service, "detect_candidate", lambda _: None)
    current_dimensions = [0, 0]

    def stub_landmarks(_file_path):
        width, height = current_dimensions
        raw = [
            {
                "id": name,
                "x": float(round(width * (0.20 + idx * 0.004), 3)),
                "y": float(round(height * (0.19 + idx * 0.009), 3)),
            }
            for idx, name in SOTA_LANDMARKS_MAPPING.items()
        ]
        return {
            "landmarks": raw,
            "mode_inference": "CI_SYNTHETIC_POINTS_NO_CLINICAL_VALIDATION",
            "warning": "No clinician-confirmed landmarks",
            "processing_time_ms": 0,
        }

    monkeypatch.setattr(cephalo_service.vision_engine, "predict_landmarks", stub_landmarks)
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
        current_dimensions[:] = [meta["width"], meta["height"]]

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

        baseline = authoritative_get()
        original = baseline["landmarks_data"]
        assert isinstance(original, list) and len(original) >= 10
        assert baseline["mm_per_pixel"] is None
        assert baseline["is_calibrated"] is False

        def correction(dx):
            return [
                {**p, "x": p["x"] + dx} if p["id"] == "N" else dict(p)
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
        assert authoritative_get()["landmarks_data"] == correction(11.0)
    assert len(set(ids)) == 2, "Real radiographs must never overwrite each other's analysis"
    print("DC_CEPH03B3C_TWO_REAL_RADIOS_AUTH_SQLITE_PERSISTENCE_PASS")
