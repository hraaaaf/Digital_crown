"""R23-G2: source-profile completeness is a presentation contract, not a calculation."""
import importlib.util
import json
from pathlib import Path

import pytest

# This isolated contract test imports the stdlib-only projector directly.
# Importing backend/__init__.py would initialize the entire clinical app and
# require unrelated SQLAlchemy/runtime dependencies in this focused CI gate.
ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "r23g2_protocol_projection", ROOT / "backend/services/cephalo_protocol_projection.py"
)
assert _spec and _spec.loader
_projection = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_projection)
project_mcnamara_reference_protocol = _projection.project_mcnamara_reference_protocol
project_com_reference_protocol = _projection.project_com_reference_protocol
project_ricketts_atlas2009_protocol = _projection.project_ricketts_atlas2009_protocol
project_ricketts_gregoret13_protocol = _projection.project_ricketts_gregoret13_protocol
AUDIT = ROOT / "docs/audits/schemas"
RUNTIME = ROOT / "backend/data/cephalometry"


def _canonical(identifier, value, status="AVAILABLE"):
    return {
        "canonical_measurement_id": identifier,
        "value": value if status == "AVAILABLE" else None,
        "unit": "mm",
        "availability_status": status,
        "measurement_refs": ["m:one"],
        "value_authority_method_id": "SOURCE_LOCKED_METHOD_V1",
    }


@pytest.mark.parametrize(
    ("name", "function", "expected_count"),
    [
        ("ricketts_atlas2009", project_ricketts_atlas2009_protocol, 33),
        ("ricketts_gregoret13", project_ricketts_gregoret13_protocol, 13),
        ("mcnamara", project_mcnamara_reference_protocol, 13),
        ("com", project_com_reference_protocol, 10),
    ],
)
def test_full_profiles_keep_all_rows_without_evidence(name, function, expected_count):
    result = function([])
    assert len(result["rows"]) == expected_count, name
    assert len({row["canonical_measurement_id"] for row in result["rows"]}) == expected_count
    assert all(row["availability_status"] == "NOT_COMPUTABLE" for row in result["rows"])
    assert all(row["value"] is None for row in result["rows"])
    assert all(row["classification_authority"] is False for row in result["rows"])


def test_atlas_and_gregoret_rows_have_executable_contracts_but_no_fake_values():
    atlas = project_ricketts_atlas2009_protocol([])
    gregoret = project_ricketts_gregoret13_protocol([])
    assert sum(row["contract_state"] == "EXECUTABLE" for row in atlas["rows"]) == 10
    assert sum(row["contract_state"] == "CONDITIONAL_EXECUTABLE" for row in atlas["rows"]) == 23
    assert sum(row["contract_state"] == "EXECUTABLE" for row in gregoret["rows"]) == 7
    assert sum(row["contract_state"] == "CONDITIONAL_EXECUTABLE" for row in gregoret["rows"]) == 6
    assert all("source_contract" in row for row in atlas["rows"])
    assert all("source_contract" in row for row in gregoret["rows"])
    assert {row["canonical_measurement_id"] for row in gregoret["rows"]}.issubset(
        {row["canonical_measurement_id"] for row in atlas["rows"]}
    )


def test_available_canonical_evidence_can_fill_only_identical_protocol_measurement():
    profile = project_ricketts_atlas2009_protocol([
        _canonical("M_LI_EPLANE_MM_V1", -2.4),
        _canonical("M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1", None, "INVALID"),
    ])
    by_id = {row["canonical_measurement_id"]: row for row in profile["rows"]}
    assert by_id["M_LI_EPLANE_MM_V1"]["value"] == -2.4
    assert by_id["M_LI_EPLANE_MM_V1"]["availability_status"] == "AVAILABLE"
    assert by_id["M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1"]["value"] is None
    assert by_id["M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1"]["availability_status"] == "INVALID"
    assert by_id["M_RICKETTS_MOLAR_RELATION_FOP_MM_V1"]["value"] is None


def test_com_candidate_equivalence_must_not_promote_mcnamara_nperp():
    profile = project_com_reference_protocol([_canonical("M_A_NPERP_MM_V1", 4.1)])
    row = next(item for item in profile["rows"] if item["canonical_measurement_id"] == "M_A_NPERP_MM_V1")
    assert row["value"] is None
    assert row["availability_status"] == "NOT_COMPUTABLE"
    assert row["contract_state"].startswith("PENDING_EQUIVALENCE")


def test_ricketts_runtime_copies_equal_the_source_locked_audit_bytes():
    for name in (
        "ortho_lot08_ricketts_atlas2009_complete33_protocol_profile_v1.json",
        "ortho_lot08_ricketts_gregoret13_protocol_profile_v1.json",
    ):
        runtime = RUNTIME / name.replace("ortho_lot08_", "")
        assert runtime.read_bytes() == (AUDIT / name).read_bytes()


def test_non_authoritative_historical_ledger_keeps_mcnamara_and_com_cardinality():
    ledger = json.loads((RUNTIME / "clinical_reference_profiles_v1.json").read_text(encoding="utf-8"))
    assert ledger["status"] == "WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL"
    assert len(ledger["profiles"]["mcnamara"]["rows"]) == 13
    assert len(ledger["profiles"]["com"]["rows"]) == 10
    assert ledger["profiles"]["com"]["rows"][7]["contract_state"].startswith("PENDING_EQUIVALENCE")
