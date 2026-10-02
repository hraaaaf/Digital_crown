import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"classify_cephalo_vnext_lot02_aariz_qc.py"
spec=importlib.util.spec_from_file_location("lot02_qc",SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_consensus_candidate_at_or_below_2mm():
    status,d=m.classify_pair(100,100,110,100,1000,1000,0.1)
    assert status=="CONSENSUS_CANDIDATE"
    assert d==1.0
    status,d=m.classify_pair(100,100,120,100,1000,1000,0.1)
    assert status=="CONSENSUS_CANDIDATE"
    assert d==2.0

def test_review_and_adjudication_bands_are_fail_closed():
    assert m.classify_pair(100,100,130,100,1000,1000,0.1)[0]=="REVIEW_REQUIRED"
    assert m.classify_pair(100,100,140,100,1000,1000,0.1)[0]=="REVIEW_REQUIRED"
    assert m.classify_pair(100,100,141,100,1000,1000,0.1)[0]=="ADJUDICATION_REQUIRED"

def test_invalid_zero_nonfinite_or_out_of_bounds_never_get_reference():
    cases=[
        (0,100,110,100,1000,1000,0.1),
        (100,100,110,100,0,1000,0.1),
        (100,100,110,100,1000,1000,0),
        (1001,100,110,100,1000,1000,0.1),
        (100,100,float("nan"),100,1000,1000,0.1),
    ]
    for args in cases:
        status,d=m.classify_pair(*args)
        assert status=="STRUCTURAL_INVALID"
        assert d is None
