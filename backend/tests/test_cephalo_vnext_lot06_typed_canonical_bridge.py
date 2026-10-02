import json
from pathlib import Path

from backend.services import cephalo_downs_evidence as downs
from backend.services import cephalo_mcnamara_evidence as mcnamara
from backend.services import cephalo_measurement_adapter as craniom
from backend.services import cephalo_ricketts_evidence as ricketts
from backend.services import cephalo_steiner_dental_evidence as steiner_dental
from backend.services import cephalo_steiner_evidence_adapter as steiner
from backend.services import cephalo_tweed_merrifield_evidence as tweed
from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS

ROOT=Path(__file__).resolve().parents[2]
BRIDGE=ROOT/"docs"/"audits"/"schemas"/"cephalo_vnext_lot06_typed_canonical_bridge_v1.json"

def load_bridge():
    return json.loads(BRIDGE.read_text(encoding="utf-8"))

def emitted_method_ids():
    ids={x.method_id for x in craniom._CRANIOM_SPECS}
    ids|={x.method_id for x in steiner._STEINER_SPECS}
    ids|={x.method_id for x in steiner_dental._SPECS}
    ids|={x.method_id for x in tweed._R6_SPECS}
    ids|={x.method_id for x in downs._DOWNS_SPECS}
    ids|={x.method_id for x in mcnamara._MCNAMARA_SPECS}
    ids|={x.canonical_id for x in mcnamara._MCNAMARA_NPERP_SPECS}
    ids|={x.method_id for x in ricketts._RICKETTS_ACTIVE_SPECS}
    return ids

def test_lot06_bridge_exhausts_all_current_typed_method_ids():
    data=load_bridge()
    bridge_ids=[x["method_id"] for x in data["methods"]]
    assert len(bridge_ids)==len(set(bridge_ids))
    assert set(bridge_ids)==emitted_method_ids()

def test_lot06_bridge_only_maps_to_existing_unambiguous_canonical_ids():
    for item in load_bridge()["methods"]:
        if item["state"]=="MAPPED":
            cid=item["canonical_measurement_id"]
            assert cid in CANONICAL_MEASUREMENTS
            assert "BLOCKED" not in CANONICAL_MEASUREMENTS[cid].source_status
            assert "CONVENTION_COLLISION" not in CANONICAL_MEASUREMENTS[cid].source_status
        else:
            assert item["canonical_measurement_id"] is None

def test_lot06_bridge_blocks_known_angle_collision_and_identity_debt():
    by_id={x["method_id"]:x for x in load_bridge()["methods"]}
    assert by_id["DOWNS_FACIAL_ANGLE_DEG_V1"]["state"]=="BLOCKED"
    assert by_id["RICKETTS_FACIAL_DEPTH_DEG_V1"]["state"]=="BLOCKED"
    assert by_id["RICKETTS_CONVEXITY_A_NPOG_MM_V1"]["state"]=="BLOCKED"
    assert by_id["RICKETTS_E_LINE_LS_MM_V2"]["state"]=="BLOCKED"
    assert by_id["RICKETTS_E_LINE_LI_MM_V2"]["state"]=="BLOCKED"

def test_lot06_bridge_does_not_invent_missing_canonical_ids():
    by_id={x["method_id"]:x for x in load_bridge()["methods"]}
    assert by_id["DOWNS_Y_AXIS_DEG_V1"]["state"]=="UNMAPPED_CANONICAL_ID"
    assert by_id["MERRIFIELD_Z_ANGLE_DEG_V1"]["state"]=="UNMAPPED_CANONICAL_ID"
