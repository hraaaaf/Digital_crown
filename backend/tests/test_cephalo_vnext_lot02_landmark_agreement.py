import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REC=ROOT/"docs"/"audits"/"schemas"/"cephalo_vnext_lot02_landmark_agreement.json"

REQUIRED={
    "n","mean_mm","median_mm","sd_mm","p90_mm","p95_mm","max_mm",
    "mean_dx_mm","mean_dy_mm","sd_dx_mm","sd_dy_mm",
    "mean_px","median_px","sd_px","p90_px","p95_px","max_px",
    "mean_dx_px","mean_dy_px","sd_dx_px","sd_dy_px",
}

def test_landmark_agreement_record_is_complete_for_all_29_landmarks():
    r=json.loads(REC.read_text(encoding="utf-8"))
    assert r["schema"]=="CEPHALO_LOT02_AARIZ_AGREEMENT_V3"
    assert r["cases"]==1000
    assert r["calibration"]=={
        "rows":1000,
        "source":"cephalogram_machine_mappings.csv",
        "unit":"mm_per_pixel",
    }
    assert len(r["landmarks"])==29
    for data in r["landmarks"].values():
        assert data["n"]==1000
        assert REQUIRED <= set(data)

def test_landmark_agreement_keeps_known_outliers_visible():
    r=json.loads(REC.read_text(encoding="utf-8"))
    assert r["landmarks"]["UIT"]["max_mm"] > 100
    assert r["landmarks"]["LPM"]["max_mm"] > 100
    assert r["landmarks"]["Go"]["p95_mm"] > 4
    assert r["landmarks"]["Po"]["p95_mm"] > 4
