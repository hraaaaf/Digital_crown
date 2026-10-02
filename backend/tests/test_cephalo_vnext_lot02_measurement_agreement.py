import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REC=ROOT/"docs"/"audits"/"schemas"/"cephalo_vnext_lot02_sentinel_measurement_agreement.json"

def test_measurement_agreement_record_is_complete_and_nonclinical():
    r=json.loads(REC.read_text(encoding="utf-8"))
    assert r["cases"]==1000
    assert r["bad_cases"]==0
    assert set(r["measurements"])=={"SNA","SNB","ANB","FMA","IMPA","FMIA","SN-GoGn","Co-A","Co-Gn"}
    assert r["policy"]["clinical_acceptance"] is False
    assert r["policy"]["no_threshold_retuning_to_candidate_model"] is True

def test_intra_observer_repeatability_source_is_locked():
    r=json.loads(REC.read_text(encoding="utf-8"))
    src=r["intra_observer_source"]
    assert src["doi"]=="10.1038/s41597-025-05542-3"
    assert src["published_intra_observer_mre_mm"]==["1.473 ± 1.829","1.651 ± 2.003"]
    assert src["published_inter_observer_mre_mm"]=="0.329 ± 0.663"
