"""D5-1: McNamara signed effective-length difference source-bound FUE-0.

No FACAD landmark alias, universal norm, diagnosis, or patient interpretation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from backend.schemas.cephalo_evidence import (
    EvidenceStatus, LandmarkEvidence, LandmarkOrigin, AvailabilityStatus,
)
from backend.services.cephalo_canonical_analysis_v2 import (
    CANONICAL_V2_METHOD_IDS, materialize_canonical_analysis_v2_measurements,
)
from backend.services.cephalo_canonical_method_bridge import (
    canonical_measurement_id_for_method,
    project_canonical_measurements,
)
from backend.services.cephalo_dependency_graph import build_analysis_pack_dependency_graph
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_co_gn_minus_co_a_mm_v1,
)

ROOT = Path(__file__).resolve().parents[2]
CID = "M_CO_GN_MINUS_CO_A_MM_V1"
METHOD = "MCNAMARA_CO_GN_MINUS_CO_A_CANONICAL_MM_V2"


def _landmark(k, xy, source="source:ceph:one"):
    return LandmarkEvidence(
        evidence_id=f"lm:{k}:{source}", landmark_id=k, x=float(xy[0]), y=float(xy[1]),
        source_image_ref=source, origin=LandmarkOrigin.MANUAL,
        evidence_status=EvidenceStatus.OBSERVED, evidence_refs=[source],
    )


def _measure(points, mm_per_pixel=0.2, calibration_ref="calibration:one", sources=None):
    sources = sources or {}
    landmarks = {
        k: _landmark(k, xy, sources.get(k, "source:ceph:one"))
        for k, xy in points.items()
    }
    return materialize_canonical_analysis_v2_measurements(
        measurement_namespace="ceph:d5", landmarks=landmarks,
        mm_per_pixel=mm_per_pixel, calibration_ref=calibration_ref,
    )


def _by_method(items):
    return {item.method_id: item for item in items}


def _points():
    return {"Co_anatomic": (0, 0), "A": (3, 4), "Gn_anatomic": (6, 8)}


def test_d5_primitive_is_signed_without_early_component_rounding():
    assert mcnamara_co_gn_minus_co_a_mm_v1(2.0, 1.0) == pytest.approx(1.0)
    assert mcnamara_co_gn_minus_co_a_mm_v1(1.0, 2.0) == pytest.approx(-1.0)
    assert mcnamara_co_gn_minus_co_a_mm_v1(1.0, 1.0) == 0.0
    assert mcnamara_co_gn_minus_co_a_mm_v1(3.499, 1.001) == pytest.approx(2.498)


@pytest.mark.parametrize("left,right", [
    (None, 2.0), (1.0, None), (float("nan"), 1.0),
    (1.0, float("inf")), (float("-inf"), 1.0), (0.0, 1.0),
    (1.0, 0.0), (True, 1.0), (1.0, False),
])
def test_d5_primitive_rejects_unusable_calibrated_inputs(left, right):
    assert mcnamara_co_gn_minus_co_a_mm_v1(left, right) is None


@pytest.mark.parametrize("points,expected", [
    ({"Co_anatomic": (0, 0), "A": (3, 4), "Gn_anatomic": (6, 8)}, 1.0),
    ({"Co_anatomic": (0, 0), "A": (6, 8), "Gn_anatomic": (3, 4)}, -1.0),
    ({"Co_anatomic": (0, 0), "A": (3, 4), "Gn_anatomic": (-3, 4)}, 0.0),
    ({"Co_anatomic": (10, 0), "A": (7, 4), "Gn_anatomic": (4, 8)}, 1.0),
])
def test_d5_typed_diff_uses_same_calibrated_components_and_provenance(points, expected):
    out = _by_method(_measure(points))
    value = out[METHOD]
    assert value.availability_status == AvailabilityStatus.AVAILABLE
    assert value.value == pytest.approx(expected)
    assert value.unit == "mm"
    assert value.calibration_ref == "calibration:one"
    assert value.requires_calibration is True
    assert value.analysis_id == "MCNAMARA"
    assert value.method_version == "2"
    assert out["MCNAMARA_CO_GN_CANONICAL_MM_V2"].measurement_id in value.evidence_refs
    assert out["MCNAMARA_CO_A_CANONICAL_MM_V2"].measurement_id in value.evidence_refs
    assert {"lm:Co_anatomic:source:ceph:one", "lm:Gn_anatomic:source:ceph:one",
            "lm:A:source:ceph:one"} <= set(value.landmark_refs)
    assert "calibration:one" in value.evidence_refs
    projected = project_canonical_measurements(list(out.values()))
    canonical = next(x for x in projected["measurements"]
                     if x["canonical_measurement_id"] == CID)
    assert canonical["value"] == pytest.approx(expected)
    assert canonical["value_authority_method_id"] == METHOD


@pytest.mark.parametrize("ratio,ref", [
    (None, None), (0.0, "cal:one"), (-0.2, "cal:one"),
    (float("nan"), "cal:one"), (float("inf"), "cal:one"),
    (0.2, None),
])
def test_d5_no_differential_without_valid_ratio_and_evidence(ratio, ref):
    assert METHOD not in _by_method(_measure(_points(), ratio, ref))


@pytest.mark.parametrize("missing", ["Co_anatomic", "A", "Gn_anatomic"])
def test_d5_missing_required_identity_fails_closed(missing):
    points = _points()
    points.pop(missing)
    assert METHOD not in _by_method(_measure(points))


def test_d5_same_label_vendor_co_and_generic_gn_cannot_substitute_anatomy():
    vendor_points = {"Co": (0, 0), "Gn": (6, 8), "A": (3, 4)}
    assert METHOD not in _by_method(_measure(vendor_points))


def test_d5_cross_image_component_rejected_without_partial_result():
    points = _points()
    out = _by_method(_measure(points, sources={"Gn_anatomic": "source:other"}))
    assert METHOD not in out
    assert out["MCNAMARA_CO_GN_CANONICAL_MM_V2"].value is None


def test_d5_provisional_source_and_bridge_membership_remain_locked():
    contract = json.loads((ROOT / "docs/audits/schemas/"
                           "cephalo_vnext_lot06_executable_measurement_contract_v1.json")
                          .read_text(encoding="utf-8"))
    row = next(r for r in contract["measurements"] if r["measurement_id"] == CID)
    assert row["required_landmarks"] == ["Co_anatomic", "Gn_anatomic", "A"]
    assert row["unit"] == "mm" and row["requires_calibration"] is True
    assert "SAME_IMAGE_AND_CALIBRATION_REF" in row["availability_gate"]
    assert canonical_measurement_id_for_method(METHOD) == CID
    assert METHOD in CANONICAL_V2_METHOD_IDS
    graph = build_analysis_pack_dependency_graph("MCNAMARA_V1")
    assert CID in graph["measurement_ids"]
    assert len(graph["measurement_ids"]) == 8
    assert graph["scientific_state"] == "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"


def test_d5_all_packs_and_normative_authority_remain_fail_closed():
    packs = json.loads((ROOT / "docs/audits/schemas/"
                        "cephalo_vnext_lot06_analysis_pack_registry_v1.json")
                       .read_text(encoding="utf-8"))["analysis_packs"]
    assert len(packs) == 7
    assert all(p["composition_state"] == "PROVISIONAL_MEMBERSHIP"
               and p["membership_evidence_refs"] == [] for p in packs)
