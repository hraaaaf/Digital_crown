"""DC-CEPH-02D: separate source-locked identity gates from invalid geometry.

Synthetic-only backend test. It preserves explicit scientific NO-GO conditions:
4 legacy CRANIOM methods must not become canonical identities by name, and the
Ricketts convexity computation must never invent a numeric result on bad geometry.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from backend.repositories.cephalo_repository import _canonicalize_evidence_projection
from backend.services.cephalo_canonical_method_bridge import (
    binding_for_method, canonical_measurement_id_for_method,
)
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_ricketts_geometry import (
    ricketts_convexity_signed_distance_px_v1,
)
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.test_cephalo_runtime_chain import _initial_graph, _points, _raw
from backend.tests.test_dc_ceph02b_runtime_matrix import _matrix, _read
from backend.tests.test_dc_ceph02c_steiner_calibration import _calibrate

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
GATED_LEGACY = {
    # Diagnostic correspondence only, never a promotion or geometry-equivalence claim.
    "M_AB_PRIME_FH_MM_V1": "CRANIOM_AB_PRIME_MM_V1",
    "M_B_NPERP_MM_V1": "CRANIOM_SITUATION_B_MM_V1",
    "M_COM_S_NPERP_DEPTH_MM_V1": "CRANIOM_FACIAL_DEPTH_MM_V1",
    "M_U1_FH_DEG_V1": "CRANIOM_U1_FRANKFORT_DEG_V1",
}
CONVEXITY = "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1"
CONVEXITY_METHOD = "RICKETTS_CONVEXITY_CANONICAL_MM_V2"


def _calibrated_read(raw):
    original = _initial_graph(raw)
    graph = _canonicalize_evidence_projection({
        EVIDENCE_GRAPH_KEY: original
    })[EVIDENCE_GRAPH_KEY]
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    after = _calibrate(graph, raw, result)
    path = _read(after, result)
    statuses, counts = _matrix(path)
    return after, path, statuses, counts


def test_four_declared_contracts_are_source_blocked_not_missing_geometry():
    contracts = json.loads(CONTRACT.read_text(encoding="utf-8"))
    registered = {x["measurement_id"]: x for x in contracts["measurements"]}
    assert len(registered) == 38
    assert set(GATED_LEGACY).issubset(registered)
    graph, path, statuses, counts = _calibrated_read(_raw())
    assert len(graph["measurements"]) > 0
    blocked = set(path["scientific_read_path"]["blocked_method_ids"])
    assert len(statuses) == 38 and counts["NOT_EXPOSED"] == 4
    assert {mid for mid,status in statuses.items() if status == "NOT_EXPOSED"} == set(GATED_LEGACY)
    for canonical, method in GATED_LEGACY.items():
        binding = binding_for_method(method)
        assert binding.state == "BLOCKED"
        assert binding.canonical_measurement_id is None
        assert binding.reason == "LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"
        assert method in blocked, "The historical method must not silently disappear from diagnostics"
        assert statuses[canonical] == "NOT_EXPOSED"
        assert registered[canonical]["implementation"] and registered[canonical]["source_contracts"]
        with pytest.raises(ValueError, match="no promotable canonical identity"):
            canonical_measurement_id_for_method(method)
    assert not any(
        p["canonical_measurement_id"] in GATED_LEGACY
        for p in path["scientific_read_path"]["canonical_measurements"]
    )


def test_convexity_invalid_fixture_stays_value_free_with_distinct_mapped_authority():
    raw = _raw()
    graph, path, statuses, _ = _calibrated_read(raw)
    assert statuses[CONVEXITY] == "INVALID"
    bridge = binding_for_method(CONVEXITY_METHOD)
    assert bridge.state == "MAPPED"
    assert bridge.canonical_measurement_id == CONVEXITY
    row = next(row for row in path["scientific_read_path"]["canonical_measurements"]
               if row["canonical_measurement_id"] == CONVEXITY)
    assert row["availability_status"] == "INVALID"
    assert row["value"] is None
    native = next(row for row in graph["measurements"] if row["method_id"] == CONVEXITY_METHOD)
    assert native["value"] is None
    assert native["availability_status"] == "INVALID"
    assert native["requires_calibration"] is True


def test_source_locked_convexity_geometry_sign_and_ambiguous_orientation():
    fn = ricketts_convexity_signed_distance_px_v1
    n, pog, po, or_ = (0.,0.), (0.,10.), (0.,0.), (10.,0.)
    assert math.isclose(fn((3.,4.),n,pog,po,or_), 3., abs_tol=1e-9)
    assert math.isclose(fn((-3.,4.),n,pog,po,or_), -3., abs_tol=1e-9)
    assert math.isclose(fn((3.,4.),n,pog,po,or_) or 0., 3., abs_tol=1e-9)
    assert fn((3.,4.),n,n,po,or_) is None, "Zero N-Pog axis must fail closed"
    assert fn((3.,4.),n,pog,po,(0.,10.)) is None, "Ambiguous anterior direction must fail closed"
    assert fn((3.,4.),n,pog,po,po) is None, "Zero Frankfort axis must fail closed"
    assert fn((math.nan,4.),n,pog,po,or_) is None, "Nonfinite landmark must fail closed"


def test_corrected_synthetic_geometry_can_unblock_invalid_convexity_without_faking_source():
    # Perturb one existing *synthetic* Pog point; original default fixture is
    # deliberately collinear, not a clinical gold standard.
    original = _raw()
    corrected = [dict(v) for v in original]
    pog = next((p for p in corrected if p["id"] == "Pog"), None)
    assert pog is not None
    pog["x"] += 11.
    _, path, statuses, counts = _calibrated_read(corrected)
    assert counts["NOT_EXPOSED"] == 4
    assert all(statuses[name] == "NOT_EXPOSED" for name in GATED_LEGACY)
    assert statuses[CONVEXITY] == "AVAILABLE", "Correct geometry must remain computable"
    row = next(row for row in path["scientific_read_path"]["canonical_measurements"]
               if row["canonical_measurement_id"] == CONVEXITY)
    assert row["value"] is not None and math.isfinite(row["value"])


def test_only_non_identifying_diagnostic_summary():
    _, path, statuses, counts = _calibrated_read(_raw())
    result = {
        "schema": "DC_CEPH02D_SOURCE_GATES_V1",
        "verdict": "FOUR_IDENTITY_GATES_RETAINED_INVALID_GEOMETRY_NOT_PROMOTED",
        "synthetic_contract_count": 38,
        "identity_blocked": sorted(GATED_LEGACY),
        "identity_block_reason": "LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED",
        "invalid_canonical_id": CONVEXITY,
        "invalid_has_no_numeric_value": True,
        "baseline_counts": counts,
        "numeric_parity_facad_certified": False,
        "clinical_activation_allowed": False,
        "real_patient_data_used": False,
        "production_runtime_modified": False,
        "vendor_software_executed": False,
    }
    assert statuses[CONVEXITY] == "INVALID"
    assert len(result["identity_blocked"]) == 4
    assert sum(counts.values()) == 38
    print("DC_CEPH02D_SAFE=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
