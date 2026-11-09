"""CEPH-PREMIUM J2.1-M1 — NONCLINICAL canonical scene serialization contract.

All images and identities are invented. No DB, ONNX weight, API, PDF, patient
file or migration is touched. Scene validation is NOT provenance certification.
"""
from __future__ import annotations

import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_premium_scene_contract import (
    CephaloPremiumSceneDraft, SCENE_VERSION,
)
from backend.services.srpose38_contract import (
    SOTA_LANDMARKS_MAPPING, SRPOSE38_MODEL_SHA256,
)


def _scene():
    landmarks = [
        {"id": point, "x": 20.0 + i * 4, "y": 32.0 + i * 3,
         "origin": "SRPOSE38_AUTO", "confidence": 0.65}
        for i, point in SOTA_LANDMARKS_MAPPING.items()
    ]
    return {
        "schema_version": SCENE_VERSION,
        "identity": {
            "employer_id": 10, "patient_id": 20, "study_id": 30,
            "original_asset_id": 40, "original_sha256": "a" * 64,
            "scientific_revision": 1, "scientific_digest": "b" * 64,
            "scene_revision": 1, "parent_scene_sha256": None,
            "original_width": 640, "original_height": 480,
            "coordinate_system": "SOURCE_IMAGE_PIXELS_TOP_LEFT",
            "detector_model": "srpose38-tta-1024.onnx",
            "detector_sha256": SRPOSE38_MODEL_SHA256,
            "detector_mapping_authority": "LEGACY_LOCAL_UNVERIFIED",
        },
        "calibration": {
            "status": "UNVERIFIED", "mm_per_pixel_candidate": None,
            "evidence_sha256": None,
        },
        "landmarks": landmarks,
        "contours": [],
        "constructions": [
            {"id": "SN", "kind": "LINE", "point_ids": ["S", "N"]},
            {"id": "SNA", "kind": "ANGLE", "point_ids": ["S", "N", "A"]},
        ],
        "measurements": [
            {"id": "SNA", "unit": "DEG", "status": "RAW_NONCLINICAL", "value": 79.2},
            {"id": "Wits", "unit": "MM", "status": "UNAVAILABLE", "value": None},
        ],
        "document_status": "NONCLINICAL_DRAFT", "clinical_release": False,
    }


def _auto_contour(name, *, model_sha="c" * 64):
    return {
        "id": name, "status": "AUTO_PROPOSED",
        "points": [{"x": 200.0, "y": 220.0}, {"x": 205.0, "y": 223.0}],
        "proposal_model_id": "FUTURE_CONTOUR_MODEL_CANDIDATE",
        "proposal_model_sha256": model_sha,
    }


def _reject_change(change):
    raw = _scene()
    change(raw)
    with pytest.raises(ValidationError):
        CephaloPremiumSceneDraft.model_validate(raw)


def test_j21m1_validates_complete_38_pixel_scene_as_nonclinical_only():
    scene = CephaloPremiumSceneDraft.model_validate(_scene())
    assert len(scene.landmarks) == 38
    assert scene.identity.detector_mapping_authority == "LEGACY_LOCAL_UNVERIFIED"
    assert scene.document_status == "NONCLINICAL_DRAFT"
    assert scene.clinical_release is False
    assert scene.calibration.status == "UNVERIFIED"
    assert scene.measurements[1].value is None
    assert scene.sha256() == CephaloPremiumSceneDraft.model_validate_json(
        scene.canonical_bytes()
    ).sha256()
    assert len(scene.canonical_bytes()) > 1500


def test_j21m1_canonical_digest_independent_of_collection_order():
    a = _scene()
    b = deepcopy(a)
    b["landmarks"].reverse()
    b["constructions"].reverse()
    b["measurements"].reverse()
    assert CephaloPremiumSceneDraft.model_validate(a).sha256() == (
        CephaloPremiumSceneDraft.model_validate(b).sha256()
    )


def test_j21m1_same_identity_changed_point_new_revision_changes_digest():
    current = CephaloPremiumSceneDraft.model_validate(_scene())
    changed = _scene()
    changed["identity"]["scene_revision"] = 2
    changed["identity"]["parent_scene_sha256"] = current.sha256()
    changed["landmarks"][3]["x"] += 8
    updated = CephaloPremiumSceneDraft.model_validate(changed)
    assert updated.identity.parent_scene_sha256 == current.sha256()
    assert updated.sha256() != current.sha256()
    assert updated.identity.scientific_revision == current.identity.scientific_revision
    assert updated.clinical_release is False


def test_j21m1_six_contours_auto_require_separate_explicit_model():
    raw = _scene()
    names = (
        "cranial_base", "maxilla", "mandible", "upper_incisor",
        "lower_incisor", "soft_tissue_profile",
    )
    raw["contours"] = [_auto_contour(name) for name in reversed(names)]
    a = CephaloPremiumSceneDraft.model_validate(raw)
    raw["contours"].reverse()
    b = CephaloPremiumSceneDraft.model_validate(raw)
    assert len(a.contours) == 6
    assert a.sha256() == b.sha256()
    assert all(c.status == "AUTO_PROPOSED" for c in a.contours)
    assert a.document_status == "NONCLINICAL_DRAFT"
    assert a.clinical_release is False


@pytest.mark.parametrize("case,change", [
    ("clinical release", lambda s: s.update(clinical_release=True)),
    ("official status", lambda s: s.update(document_status="PRACTITIONER_APPROVED")),
    ("unknown extra field", lambda s: s.update(diagnosis="Class II")),
    ("wrong version", lambda s: s.update(schema_version="CEPH_SCENE_V2")),
    ("forged mapping", lambda s: s["identity"].update(detector_mapping_authority="OFFICIAL")),
    ("wrong model SHA", lambda s: s["identity"].update(detector_sha256="f" * 64)),
    ("wrong model id", lambda s: s["identity"].update(detector_model="unapproved.onnx")),
    ("uppercase source SHA", lambda s: s["identity"].update(original_sha256="A" * 64)),
    ("short source SHA", lambda s: s["identity"].update(original_sha256="a" * 63)),
    ("patient ID bool", lambda s: s["identity"].update(patient_id=True)),
    ("float asset ID", lambda s: s["identity"].update(original_asset_id=5.0)),
    ("negative revision", lambda s: s["identity"].update(scene_revision=0)),
    ("revision 2 without parent", lambda s: s["identity"].update(scene_revision=2)),
    ("revision 1 with parent", lambda s: s["identity"].update(parent_scene_sha256="a" * 64)),
    ("unknown coordinate space", lambda s: s["identity"].update(coordinate_system="SCREEN_PIXELS_ZOOMED")),
    ("zero width", lambda s: s["identity"].update(original_width=0)),
    ("duplicate landmark", lambda s: s["landmarks"].append(deepcopy(s["landmarks"][0]))),
    ("missing confidence", lambda s: s["landmarks"][0].update(confidence=None)),
    ("confidence infinity", lambda s: s["landmarks"][0].update(confidence=float("inf"))),
    ("outside image", lambda s: s["landmarks"][0].update(x=640.0)),
    ("negative landmark", lambda s: s["landmarks"][0].update(x=-1.0)),
    ("unknown onnx point", lambda s: s["landmarks"][0].update(id="MadeUp")),
    ("constructed masquerade", lambda s: s["landmarks"][0].update(id="Occ_Ant")),
    ("bad calibration w/o evidence", lambda s: s["calibration"].update(status="CANDIDATE", mm_per_pixel_candidate=0.15)),
    ("calibration unverified with ratio", lambda s: s["calibration"].update(mm_per_pixel_candidate=0.15)),
    ("millimeter nonclinical numeric", lambda s: s["measurements"][1].update(status="RAW_NONCLINICAL", value=2.5)),
    ("unavailable zero fall back", lambda s: s["measurements"][1].update(value=0.0)),
    ("nan measurement", lambda s: s["measurements"][0].update(value=float("nan"))),
    ("angle referenced point missing", lambda s: s["constructions"][0].update(point_ids=["S", "Missing"])),
    ("line wrong points", lambda s: s["constructions"][0].update(point_ids=["S", "N", "A"])),
    ("new field in landmark", lambda s: s["landmarks"][0].update(doctor_approved=True)),
])
def test_j21m1_rejects_unsafe_scene_claims(case, change):
    _reject_change(change)


@pytest.mark.parametrize("case,change", [
    ("auto no model SHA", lambda s: s["contours"][0].update(proposal_model_sha256=None)),
    ("auto no model id", lambda s: s["contours"][0].update(proposal_model_id=None)),
    ("auto forged approval", lambda s: s["contours"][0].update(status="PRACTITIONER_APPROVED")),
    ("contour outside source", lambda s: s["contours"][0]["points"][1].update(y=480.0)),
    ("contour infinity", lambda s: s["contours"][0]["points"][1].update(y=float("inf"))),
    ("contour wrong type", lambda s: s["contours"][0].update(id="cranial_outline_imagined")),
    ("duplicate contour", lambda s: s["contours"].append(deepcopy(s["contours"][0]))),
])
def test_j21m1_rejects_unsafe_auto_contours(case, change):
    raw = _scene()
    raw["contours"] = [_auto_contour("cranial_base")]
    change(raw)
    with pytest.raises(ValidationError):
        CephaloPremiumSceneDraft.model_validate(raw)


def test_j21m1_model_is_frozen_no_production_or_approval_semantics():
    scene = CephaloPremiumSceneDraft.model_validate(_scene())
    assert isinstance(scene.landmarks, tuple)
    assert isinstance(scene.contours, tuple)
    with pytest.raises(ValidationError):
        scene.clinical_release = True
    with pytest.raises(ValidationError):
        scene.identity.original_asset_id = 999
    assert "PRACTITIONER_APPROVED" not in json.dumps(
        CephaloPremiumSceneDraft.model_json_schema()
    )
