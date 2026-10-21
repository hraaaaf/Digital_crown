"""LOT05 05.7-J10D: manual 38-point cephalo is explicit and clinically fail-closed."""
import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from backend.services.cephalo_service import CephaloService
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING


def _service():
    service = CephaloService(MagicMock())
    existing = SimpleNamespace(
        id=42, patient_id=7, patient=None,
        image_original_path="api/static/uploads/radios/manual.png",
        angles_data={"analysis_status": "MANUAL_DRAFT", "calibration_status": "unverified"},
        is_calibrated=False, mm_per_pixel=None,
    )
    service.repo = MagicMock()
    service.repo.get_by_id.return_value = existing
    service.repo.create.return_value = SimpleNamespace(id=42)
    service.repo.update.return_value = SimpleNamespace(id=42, mm_per_pixel=None, is_calibrated=False)
    return service


def _manual_landmarks():
    coords = {
        name: (float(100 + index * 2), float(120 + index * 3))
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    }
    coords.update({
        "S": (10.0, 10.0), "N": (20.0, 10.0), "Po": (0.0, 20.0),
        "Or": (20.0, 20.0), "A": (24.0, 28.0), "B": (22.0, 38.0),
        "Go": (5.0, 50.0), "Me": (25.0, 55.0),
        "U1_apex": (20.0, 25.0), "U1_incisal": (24.0, 35.0),
        "L1_apex": (20.0, 48.0), "L1_incisal": (23.0, 38.0),
    })
    return [{"id": name, "x": x, "y": y} for name, (x, y) in coords.items()]


def _image_upload(contents=b"synthetic-image-bytes", mime="image/png"):
    return UploadFile(
        filename="manual.png",
        file=BytesIO(contents),
        headers=Headers({"content-type": mime}),
    )


def test_create_manual_draft_never_fabricates_clinical_results(monkeypatch):
    import backend.services.cephalo_service as module
    service = _service()
    monkeypatch.setattr(module.cv2, "imread", lambda *_args, **_kwargs: np.zeros((30, 20), dtype=np.uint8))

    result = service.create_manual_draft(7, "manual.png", "api/static/uploads/radios/manual.png")

    assert result["status"] == "manual_required"
    assert result["landmarks"] == []
    assert result["results"]["analysis_status"] == "MANUAL_DRAFT"
    assert "metrics" not in result["results"]
    assert EVIDENCE_GRAPH_KEY not in result["results"]
    assert result["is_calibrated"] is False
    service.repo.create.assert_called_once()


def test_manual_draft_rejects_invalid_radiograph(monkeypatch):
    import backend.services.cephalo_service as module
    service = _service()
    monkeypatch.setattr(module.cv2, "imread", lambda *_args, **_kwargs: None)
    with pytest.raises(ValueError, match="illisible"):
        service.create_manual_draft(7, "missing.png", "api/static/uploads/radios/missing.png")
    service.repo.create.assert_not_called()


def test_partial_manual_points_remain_draft_without_metrics_or_evidence(monkeypatch):
    service = _service()
    metrics = MagicMock()
    monkeypatch.setattr(
        "backend.services.cephalo_service.cephalo_engine.calculate_metrics", metrics,
    )
    result = service.refine_analysis(
        42,
        [{"id": "S", "x": 12.0, "y": 22.0}],
        clinician_id="7",
    )

    assert result["status"] == "manual_draft"
    assert result["results"]["analysis_status"] == "MANUAL_DRAFT"
    assert EVIDENCE_GRAPH_KEY not in result["results"]
    metrics.assert_not_called()
    persisted = service.repo.update.call_args.args[2]
    assert "metrics" not in persisted
    assert persisted["calibration_status"] == "unverified"


@pytest.mark.parametrize("points", [
    [{"id": "unknown", "x": 10, "y": 15}],
    [{"id": "S", "x": float("nan"), "y": 15}],
    [{"id": "S", "x": 10, "y": float("inf")}],
])
def test_manual_draft_rejects_unknown_or_nonfinite_points(points):
    service = _service()
    with pytest.raises(ValueError):
        service.refine_analysis(42, points, clinician_id="7")
    service.repo.update.assert_not_called()


def test_manual_draft_rejects_missing_clinician_identity():
    service = _service()
    with pytest.raises(ValueError, match="Identité du praticien"):
        service.refine_analysis(42, [{"id": "S", "x": 1, "y": 2}])
    service.repo.update.assert_not_called()


def test_complete_38_manual_points_create_only_manual_evidence():
    service = _service()

    result = service.refine_analysis(
        42, _manual_landmarks(), clinician_id="7",
    )
    assert result["status"] == "manual_review_required"
    assert result["results"]["analysis_status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["results"]["vision_metadata"]["mode_inference"] == "MANUAL"
    assert result["is_calibrated"] is False
    persisted = service.repo.update.call_args.args[2]
    assert EVIDENCE_GRAPH_KEY in persisted
    graph = persisted[EVIDENCE_GRAPH_KEY]
    assert len(graph["current_landmark_refs"]) == 38
    manual_items = [p for p in graph["landmarks"] if p["landmark_id"] in set(SOTA_LANDMARKS_MAPPING.values())]
    assert len(manual_items) == 38
    assert all(p["origin"] == "MANUAL" for p in manual_items)
    assert all(p.get("model_id") is None for p in manual_items)


def test_manual_endpoint_denies_unauthorized_patient_before_storage(monkeypatch, tmp_path):
    from backend.routers import ia

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    def denied(*_args):
        raise HTTPException(status_code=403, detail="Denied")
    monkeypatch.setattr(ia, "assert_patient_access", denied)
    service = MagicMock()
    monkeypatch.setattr(ia, "CephaloService", lambda _db: service)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(ia.upload_radio_manual(
            7, _image_upload(), MagicMock(), SimpleNamespace(id=7),
        ))

    assert exc.value.status_code == 403
    service.create_manual_draft.assert_not_called()
    assert not (tmp_path / "media").exists()


def test_manual_endpoint_creates_only_explicit_image_bound_draft(monkeypatch, tmp_path):
    from backend.routers import ia
    from backend.core.media_paths import get_imaging_root

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    guard = MagicMock()
    monkeypatch.setattr(ia, "assert_patient_access", guard)
    service = MagicMock()
    service.create_manual_draft.return_value = {
        "status": "manual_required",
        "analysis_id": 42,
        "landmarks": [],
        "results": {"analysis_status": "MANUAL_DRAFT"},
    }
    monkeypatch.setattr(ia, "CephaloService", lambda _db: service)
    user = SimpleNamespace(id=7)
    db = MagicMock()

    result = asyncio.run(ia.upload_radio_manual(7, _image_upload(), db, user))

    guard.assert_called_once_with(7, user, db)
    assert result["status"] == "manual_required"
    source_path = service.create_manual_draft.call_args.args[1]
    assert source_path.startswith(str(get_imaging_root() / "radios"))
    assert result["image_path"].startswith("api/static/uploads/radios/")
    assert result["landmarks"] == []


def test_manual_upload_invalid_type_does_not_touch_storage(monkeypatch, tmp_path):
    from backend.routers import ia
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setattr(ia, "assert_patient_access", MagicMock())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ia.upload_radio_manual(
            7, _image_upload(mime="application/octet-stream"), MagicMock(), SimpleNamespace(id=7),
        ))
    assert exc.value.status_code == 415
    assert not (tmp_path / "media").exists()


@pytest.mark.parametrize("status", ["MANUAL_DRAFT", "MANUAL_REVIEW_REQUIRED"])
def test_manual_cephalo_never_generates_pdf_without_clinician_attestation(
    monkeypatch, status,
):
    from backend.routers import patients
    tenant = MagicMock()
    monkeypatch.setattr(patients, "assert_patient_access", tenant)
    db, user = MagicMock(), SimpleNamespace(id=7)
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        id=42, patient_id=7,
        angles_data={"analysis_status": status, EVIDENCE_GRAPH_KEY: {"revision": 1}},
    )
    with pytest.raises(HTTPException) as blocked:
        patients._bound_cephalo_study(7, 42, 1, db, user)
    assert blocked.value.status_code == 409
    assert "manuel non validé" in str(blocked.value.detail)
    tenant.assert_called_once_with(7, user, db)


@pytest.mark.parametrize("previous_status", ["MANUAL_DRAFT", "MANUAL_REVIEW_REQUIRED"])
def test_other_saves_cannot_clear_manual_report_blocker(previous_status):
    from backend.repositories.cephalo_repository import _merge_calibration_projection

    previous = {
        "analysis_status": previous_status,
        "vision_metadata": {"mode_inference": "MANUAL_DRAFT"},
        "calibration_status": "unverified",
    }
    saved = _merge_calibration_projection(previous, {"metrics": {"SNA": 82}})

    assert saved["analysis_status"] == previous_status
    assert saved["vision_metadata"]["mode_inference"] == "MANUAL_DRAFT"


def test_complete_manual_draft_can_only_transition_to_review_required():
    from backend.repositories.cephalo_repository import _merge_calibration_projection

    previous = {"analysis_status": "MANUAL_DRAFT"}
    completed = _merge_calibration_projection(
        previous,
        {"analysis_status": "MANUAL_REVIEW_REQUIRED"},
    )
    assert completed["analysis_status"] == "MANUAL_REVIEW_REQUIRED"

    # Editing a completed manual case must not automatically approve it.
    updated = _merge_calibration_projection(
        completed,
        {"metrics": {"SNA": 83}, "analysis_status": "APPROVED"},
    )
    assert updated["analysis_status"] == "MANUAL_REVIEW_REQUIRED"
