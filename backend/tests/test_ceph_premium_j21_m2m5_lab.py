"""J2.1 M2/M3/M4/M5 isolated gates, all generated patients are fictitious.

M2 transform roundtrips across 8 EXIF orientations and cropped viewports.
M3 draft append-only CAS/replay in :memory: SQLite only; no prod migration.
M4 byte-level original image attestation; a mocked binding is NOT clinical auth.
M5 refuses wrong patient/tenant/study, SHA/bytes/revisions and stale writes.
"""
from __future__ import annotations

import hashlib
import io
import math
import sqlite3

import pytest
from PIL import Image
from pydantic import ValidationError

from backend.services.srpose38_contract import (
    SOTA_LANDMARKS_MAPPING, SRPOSE38_MODEL_SHA256,
)
from backend.schemas.cephalo_premium_scene_contract import (
    CephaloPremiumSceneDraft,
)
from backend.services.ceph_premium_pixel_transform_lab import (
    PixelTransformError, SourceView,
)
from backend.services.ceph_premium_scene_ledger_lab import (
    SceneCasError, SceneLabLedger,
)
from backend.services.ceph_premium_scene_source_lab import (
    SceneSourceRejected, verify_original_pixels,
)


def _png(*, width=640, height=480):
    out = io.BytesIO()
    Image.new("RGB", (width, height), (29, 56, 92)).save(out, "PNG")
    return out.getvalue()


def make_scene(*, sha=None, width=640, height=480):
    return {
        "schema_version": "CEPH_PREMIUM_SCENE_V1_DRAFT",
        "identity": {
            "employer_id": 11, "patient_id": 22, "study_id": 33,
            "original_asset_id": 44,
            "original_sha256": sha or hashlib.sha256(_png(width=width, height=height)).hexdigest(),
            "original_width": width, "original_height": height,
            "scientific_revision": 1, "scientific_digest": "b" * 64,
            "scene_revision": 1, "parent_scene_sha256": None,
            "coordinate_system": "SOURCE_IMAGE_PIXELS_TOP_LEFT",
            "detector_model": "srpose38-tta-1024.onnx",
            "detector_sha256": SRPOSE38_MODEL_SHA256,
            "detector_mapping_authority": "LEGACY_LOCAL_UNVERIFIED",
        },
        "calibration": {"status": "UNVERIFIED"},
        "landmarks": [
            {"id": name, "x": float(12+i*5), "y": float(18+i*4),
             "origin": "SRPOSE38_AUTO", "confidence": 0.72, "score_status": "AVAILABLE"}
            for i, name in SOTA_LANDMARKS_MAPPING.items()
        ],
        "contours": [],
        "constructions": [{"id": "SN", "kind": "LINE", "point_ids": ["S", "N"]}],
        "measurements": [
            {"id": "SNA", "unit": "DEG", "status": "RAW_NONCLINICAL", "value": 80.4}
        ],
        "document_status": "NONCLINICAL_DRAFT",
        "clinical_release": False,
    }


def binding(scene):
    i = scene.identity
    return {
        "binding_state": "EXPLICIT_VERIFIED_ORIGINALS",
        "study_id": i.study_id, "patient_id": i.patient_id,
        "revision": i.scientific_revision, "clinical_release": False,
        "items": [
            {"role": "RADIO_SOURCE", "asset_id": i.original_asset_id,
             "sha256": i.original_sha256, "revision": i.scientific_revision},
        ],
    }


@pytest.mark.parametrize("orientation", range(1, 9))
@pytest.mark.parametrize("viewport", [(1280, 900), (1600, 1000)])
def test_m2_every_exif_transform_roundtrip_with_zoom_and_pan(orientation, viewport):
    v = SourceView(
        width=640, height=480, orientation=orientation,
        viewport_width=viewport[0], viewport_height=viewport[1],
        zoom=1.4, pan_x=31, pan_y=-43,
    )
    for orig in ((0, 0), (15, 30), (320, 240), (638, 479)):
        screen = v.to_screen(*orig)
        inverse = v.to_original(*screen)
        assert inverse == pytest.approx(orig, abs=1e-9)
        assert v.point_in_crop(*orig)
    assert v.oriented_size == ((480, 640) if orientation in (5, 6, 7, 8)
                               else (640, 480))


@pytest.mark.parametrize("orientation", range(1, 9))
def test_m2_crop_in_oriented_image_then_reverse(orientation):
    v = SourceView(
        width=640, height=480, orientation=orientation,
        crop_x=15, crop_y=10, crop_width=300, crop_height=250,
        viewport_width=800, viewport_height=650, zoom=2.3,
        pan_x=-29, pan_y=77,
    )
    # All points are internally mapped in original source coordinates.
    first=v.deorient(150,120)
    assert v.point_in_crop(*first)
    assert v.to_original(*v.to_screen(*first)) == pytest.approx(first, abs=1e-9)
    last=v.deorient(400,400)
    assert not v.point_in_crop(*last)


@pytest.mark.parametrize("change", [
    {"orientation": 0}, {"orientation": 9}, {"orientation": True},
    {"zoom": 0}, {"zoom": math.inf}, {"pan_x": float("nan")},
    {"crop_x": -1}, {"crop_y": 480}, {"crop_width": 10000},
    {"viewport_width": 0}, {"width": True},
])
def test_m2_invalid_crop_orientation_or_zoom_denied(change):
    options = {"width": 640, "height": 480}
    options.update(change)
    with pytest.raises(PixelTransformError):
        SourceView(**options)


def test_m2_viewport_inverse_denies_outside_original():
    v = SourceView(width=640, height=480)
    with pytest.raises(PixelTransformError):
        v.to_original(-100, -100)
    with pytest.raises(PixelTransformError):
        v.to_screen(640, 20)


def _next_scene(previous, *, change_landmark=False):
    raw=previous.canonical_dict()
    raw["identity"]["scene_revision"] += 1
    raw["identity"]["parent_scene_sha256"] = previous.sha256()
    if change_landmark:
        raw["landmarks"][0]["x"] += 1
        for m in raw["measurements"]:
            m["status"]="UNAVAILABLE"
            m["value"]=None
    return CephaloPremiumSceneDraft.model_validate(raw)


def test_m3_cas_roundtrip_appends_immutable_revisions_and_invalidates_geometry():
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    sha=ledger.append(a,expected_parent_sha256=None, actor_employer_id=11,
                      actor_patient_id=22,actor_study_id=33)
    assert sha==a.sha256()
    assert ledger.latest(employer_id=11,patient_id=22,study_id=33).sha256()==sha
    b=_next_scene(a,change_landmark=True)
    second=ledger.append(b,expected_parent_sha256=sha, actor_employer_id=11,
                          actor_patient_id=22,actor_study_id=33)
    assert second!=sha
    assert ledger.latest(employer_id=11,patient_id=22,study_id=33).sha256()==second
    rows=c.execute("SELECT count(*) FROM ephemeral_scene_snapshots").fetchone()[0]
    assert rows==2


def test_m3_parallel_editor_stale_rev_and_parent_denied():
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    sha=ledger.append(a,expected_parent_sha256=None, actor_employer_id=11,
                      actor_patient_id=22,actor_study_id=33)
    b=_next_scene(a,change_landmark=True)
    ledger.append(b,expected_parent_sha256=sha, actor_employer_id=11,
                  actor_patient_id=22,actor_study_id=33)
    with pytest.raises(SceneCasError, match="Stale"):
        ledger.append(b,expected_parent_sha256=sha, actor_employer_id=11,
                      actor_patient_id=22,actor_study_id=33)
    assert c.execute("SELECT count(*) FROM ephemeral_scene_snapshots").fetchone()[0]==2


def test_m3_edit_with_unrecomputed_measurement_is_refused():
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    ledger.append(a,expected_parent_sha256=None,actor_employer_id=11,
                  actor_patient_id=22,actor_study_id=33)
    raw=_next_scene(a,change_landmark=True).canonical_dict()
    raw["measurements"][0].update(status="RAW_NONCLINICAL",value=80.4)
    unsafe=CephaloPremiumSceneDraft.model_validate(raw)
    with pytest.raises(SceneCasError, match="invalidates"):
        ledger.append(unsafe,expected_parent_sha256=a.sha256(),
                      actor_employer_id=11,actor_patient_id=22,actor_study_id=33)
    assert ledger.latest(employer_id=11,patient_id=22,study_id=33).sha256()==a.sha256()


@pytest.mark.parametrize("forged", ["original_sha256", "scientific_revision",
                                   "original_asset_id", "detector_mapping_authority"])
def test_m3_identity_and_model_cannot_change_during_revision(forged):
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    ledger.append(a,expected_parent_sha256=None,actor_employer_id=11,
                  actor_patient_id=22,actor_study_id=33)
    raw=_next_scene(a).canonical_dict()
    if forged=="original_sha256":
        raw["identity"][forged]="e"*64
    elif forged=="scientific_revision":
        raw["identity"][forged]=2
    elif forged=="original_asset_id":
        raw["identity"][forged]=55
    else:
        # The schema itself prohibits fabricated official mapping authority.
        raw["identity"][forged]="OFFICIAL_CERTIFIED"
        with pytest.raises(ValidationError):
            CephaloPremiumSceneDraft.model_validate(raw)
        return
    scene=CephaloPremiumSceneDraft.model_validate(raw)
    with pytest.raises(SceneCasError, match="identity"):
        ledger.append(scene,expected_parent_sha256=a.sha256(),
                      actor_employer_id=11,actor_patient_id=22,actor_study_id=33)


def test_m3_corrupted_saved_bytes_fail_closed():
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    ledger.append(a,expected_parent_sha256=None,actor_employer_id=11,
                  actor_patient_id=22,actor_study_id=33)
    c.execute("UPDATE ephemeral_scene_snapshots SET payload='{}' WHERE scene_revision=1")
    c.commit()
    with pytest.raises(SceneCasError, match="digest corrupted"):
        ledger.latest(employer_id=11,patient_id=22,study_id=33)


def test_m3_rejects_disk_storage_even_temporary(tmp_path):
    c=sqlite3.connect(str(tmp_path/"no-clinic-write.sqlite"))
    try:
        with pytest.raises(SceneCasError, match="disk or production"):
            SceneLabLedger(c)
    finally:
        c.close()


def test_m4_verified_bytes_and_original_pixels_from_synthetic_media():
    original=_png()
    scene=CephaloPremiumSceneDraft.model_validate(make_scene(
        sha=hashlib.sha256(original).hexdigest()))
    result=verify_original_pixels(
        scene,verified_media=binding(scene),original_bytes=original)
    assert result["source_width"]==640
    assert result["source_height"]==480
    assert result["exif_orientation"]==1
    assert result["clinical_release"] is False
    assert result["image_used_by_srpose38_inference_verified"] is False


@pytest.mark.parametrize("forgery", [
    "no_binding", "wrong_patient", "wrong_study", "wrong_revision",
    "wrong_original_asset", "wrong_original_sha", "two_radio_sources",
    "clinical_true", "tampered_bytes", "dimension_swap", "bad_format",
    "unsupported_role",
])
def test_m5_original_source_attack_vectors_rejected(forgery):
    data=_png()
    scene=CephaloPremiumSceneDraft.model_validate(make_scene(
        sha=hashlib.sha256(data).hexdigest()))
    trusted=binding(scene)
    if forgery=="no_binding":trusted["items"]=[]
    elif forgery=="wrong_patient":trusted["patient_id"]=900
    elif forgery=="wrong_study":trusted["study_id"]=901
    elif forgery=="wrong_revision":trusted["revision"]=9
    elif forgery=="wrong_original_asset":trusted["items"][0]["asset_id"]=9
    elif forgery=="wrong_original_sha":trusted["items"][0]["sha256"]="f"*64
    elif forgery=="two_radio_sources":trusted["items"].append(dict(trusted["items"][0]))
    elif forgery=="clinical_true":trusted["clinical_release"]=True
    elif forgery=="tampered_bytes":data+=b"tampered"
    elif forgery=="dimension_swap":data=_png(width=480,height=640)
    elif forgery=="bad_format":data=b"not an image"
    elif forgery=="unsupported_role":trusted["items"][0]["role"]="PHOTO_CONTEXT"
    with pytest.raises(SceneSourceRejected):
        verify_original_pixels(scene,verified_media=trusted,original_bytes=data)


@pytest.mark.parametrize("forged_scope", [(10,22,33), (11,21,33), (11,22,31)])
def test_m5_cas_actor_scope_is_exact(forged_scope):
    c=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(c)
    a=CephaloPremiumSceneDraft.model_validate(make_scene())
    with pytest.raises(SceneCasError, match="Cross-tenant"):
        ledger.append(a,expected_parent_sha256=None,
                      actor_employer_id=forged_scope[0],
                      actor_patient_id=forged_scope[1],actor_study_id=forged_scope[2])
    assert c.execute("SELECT count(*) FROM ephemeral_scene_snapshots").fetchone()[0]==0
