import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"recompute_cephalo_vnext_lot04_acceptance_from_predictions.py"
spec=importlib.util.spec_from_file_location("lot04_recompute",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

def test_measure_one_uses_only_required_landmarks_for_sna():
    pts={"S":(0.0,0.0),"N":(1.0,0.0),"A":(1.0,1.0)}
    value=mod.measure_one("SNA",pts,1.0)
    assert value==90.0

def test_measure_requirements_are_endpoint_specific():
    assert mod.REQ["SNA"]=={"S","N","A"}
    assert mod.REQ["Co-A"]=={"Co","A"}
    assert mod.REQ["FMA"]=={"Po","Or","Go","Me"}
    assert len({frozenset(v) for v in mod.REQ.values()})>1
