import json
from pathlib import Path

from scripts.validate_cephalo_vnext_lot05_migration import migrate_v1_to_v2, roundtrip_v2_to_v1

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/"docs"/"audits"/"fixtures"/"cephalo_vnext_lot02_g3_legacy_v1.json"
MIGRATED_AT="2026-10-02T00:00:00+00:00"

def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

def test_g3_fixture_roundtrip_preserves_full_legacy_surface_exactly():
    source=load_fixture()
    v2=migrate_v1_to_v2(source,patient_id=7001,width=1935,height=2400,migrated_at=MIGRATED_AT)
    restored=roundtrip_v2_to_v1(v2)
    assert restored==source

def test_g3_fixture_contains_required_compatibility_surfaces():
    source=load_fixture()
    u=source["unknown_legacy"]
    assert u["tracing"]["visible"] is True
    assert u["report_pdf"]["semantic_values"]["SNA"]==81.2
    assert u["superimposition"]["serial_study_id"]=="serial:synthetic:01"
    assert any(m["status"]=="NOT_COMPUTABLE" for m in source["measurements"])
    assert any(m["status"]=="BLOCKED" for m in source["measurements"])
    assert source["current_landmark_refs"]==["lm:r7:A"]

def test_g3_migration_does_not_recompute_historical_measurements():
    source=load_fixture()
    v2=migrate_v1_to_v2(source,patient_id=7001,width=1935,height=2400,migrated_at=MIGRATED_AT)
    restored=roundtrip_v2_to_v1(v2)
    assert restored["measurements"]==source["measurements"]
    assert restored["calibration_status"]==source["calibration_status"]
    assert restored["unknown_legacy"]["report_pdf"]==source["unknown_legacy"]["report_pdf"]
