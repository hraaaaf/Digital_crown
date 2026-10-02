import json
from pathlib import Path

from backend.services.cephalo_dependency_graph import compose_measurement_dependency_graph

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot06_goldset_sentinel_bindings_v1.json"
)
LOT02 = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot02_sentinel_measurement_agreement.json"
)
EXECUTABLE = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot06_executable_measurement_contract_v1.json"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_lot06_bindings_exhaust_exact_lot02_sentinel_set_without_clinical_claim():
    upstream = _load(LOT02)
    bindings = _load(BINDINGS)
    expected = set(upstream["measurements_all_source"])
    actual = {item["lot02_sentinel"] for item in bindings["bindings"]}
    assert actual == expected
    assert bindings["clinical_acceptance"] is False
    assert upstream["policy"]["clinical_acceptance"] is False


def test_lot06_every_lot02_sentinel_maps_to_one_executable_canonical_measurement():
    bindings = _load(BINDINGS)
    executable = {
        item["measurement_id"]: item
        for item in _load(EXECUTABLE)["measurements"]
    }
    canonical_ids = [item["canonical_measurement_id"] for item in bindings["bindings"]]
    assert len(canonical_ids) == len(set(canonical_ids))
    assert all(measurement_id in executable for measurement_id in canonical_ids)

    graph = compose_measurement_dependency_graph(canonical_ids)
    assert set(graph["measurement_ids"]) == set(canonical_ids)


def test_lot06_sentinel_identity_sensitive_bindings_are_explicit():
    by_sentinel = {
        item["lot02_sentinel"]: item
        for item in _load(BINDINGS)["bindings"]
    }
    assert "Po_anatomic" in by_sentinel["FMA"]["note"]
    assert "Po_anatomic" in by_sentinel["FMIA"]["note"]
    assert "Gn_anatomic" in by_sentinel["SN-GoGn"]["note"]
    assert "Co_anatomic" in by_sentinel["Co-A"]["note"]
    assert "Gn_anatomic" in by_sentinel["Co-Gn"]["note"]
