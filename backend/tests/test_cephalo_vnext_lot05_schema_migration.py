import copy
import pytest

from scripts.validate_cephalo_vnext_lot05_migration import (
    Lot05MigrationError,
    migrate_v1_to_v2,
    roundtrip_v2_to_v1,
)


MIGRATED_AT = "2026-10-01T00:00:00+00:00"


def v1():
    common_source = {
        "patient_id": 7,
        "source_record_id": "img:1",
        "recorded_at": "2026-09-10T15:00:00+00:00",
        "evidence_status": "OBSERVED",
        "availability_status": "AVAILABLE",
        "metadata": {},
    }
    auto_common = {
        "source_image_ref": "source:image",
        "origin": "SRPOSE38_AUTO",
        "model_id": "srpose38",
        "model_sha256": "a" * 64,
        "pipeline_version": "SRPOSE38_V1",
        "evidence_refs": ["source:image"],
        "evidence_status": "OBSERVED",
        "availability_status": "AVAILABLE",
    }
    return {
        "schema_version": "CEPHALO_EVIDENCE_V1",
        "case_id": "case:1",
        "revision": 3,
        "sources": [
            {"evidence_id": "source:image", "kind": "lateral_ceph", **common_source},
            {"evidence_id": "cal:1", "kind": "calibration", "ratio": 0.1, **common_source},
        ],
        "landmarks": [
            {"evidence_id": "lm:auto:A", "landmark_id": "A", "x": 10.0, "y": 20.0, **auto_common},
            {"evidence_id": "lm:auto:B", "landmark_id": "B", "x": 30.0, "y": 40.0, **auto_common},
            {
                "evidence_id": "lm:r3:A",
                "landmark_id": "A",
                "x": 11.0,
                "y": 21.0,
                "source_image_ref": "source:image",
                "origin": "MANUAL_CORRECTED",
                "original_auto_x": 10.0,
                "original_auto_y": 20.0,
                "validated_by": "99",
                "validated_at": "2026-09-10T15:35:00+00:00",
                "evidence_refs": ["source:image"],
                "evidence_status": "CLINICIAN_VALIDATED",
                "availability_status": "AVAILABLE",
            },
        ],
        "current_landmark_refs": ["lm:r3:A"],
        "measurements": [{"measurement_id": "SNA", "value": 81.0}],
        "calibration_status": "clinician_confirmed",
        "unknown_legacy": {"keep": True},
    }


def migrate(source=None, **kwargs):
    return migrate_v1_to_v2(
        v1() if source is None else source,
        patient_id=kwargs.pop("patient_id", 7),
        width=kwargs.pop("width", 1935),
        height=kwargs.pop("height", 2400),
        migrated_at=kwargs.pop("migrated_at", MIGRATED_AT),
        **kwargs,
    )


def test_lossless_roundtrip_preserves_exact_v1_and_unknown_legacy_data():
    source = v1()
    restored = roundtrip_v2_to_v1(migrate(source))
    assert restored == source
    assert restored["unknown_legacy"] == {"keep": True}


def test_active_correction_lineage_is_explicit_and_bound():
    v2 = migrate()
    assert v2["active_landmarks"] == [{
        "evidence_ref": "lm:r3:A",
        "canonical_id": "A",
        "origin": "MANUAL_CORRECTED",
        "x": 11.0,
        "y": 21.0,
        "model_id": None,
        "model_sha256": None,
        "pipeline_version": None,
        "original_auto_x": 10.0,
        "original_auto_y": 20.0,
        "validated_by": "99",
        "validated_at": "2026-09-10T15:35:00+00:00",
    }]
    v2["active_landmarks"][0]["origin"] = "SRPOSE38_AUTO"
    with pytest.raises(Lot05MigrationError):
        roundtrip_v2_to_v1(v2)


def test_omitted_landmark_does_not_resurrect():
    v2 = migrate()
    assert v2["current_landmark_refs"] == ["lm:r3:A"]
    assert all(item["canonical_id"] != "B" for item in v2["active_landmarks"])
    assert roundtrip_v2_to_v1(v2)["current_landmark_refs"] == ["lm:r3:A"]


def test_calibration_and_measurements_are_not_recomputed():
    source = v1()
    v2 = migrate(source)
    assert v2["coordinate_space"]["calibration_ref"] == "cal:1"
    restored = roundtrip_v2_to_v1(v2)
    assert restored["measurements"] == source["measurements"]
    assert restored["calibration_status"] == source["calibration_status"]


@pytest.mark.parametrize("field", ["model_id", "model_sha256", "pipeline_version"])
def test_auto_landmark_requires_model_provenance(field):
    source = v1()
    source["landmarks"][0].pop(field)
    with pytest.raises(Lot05MigrationError):
        migrate(source)


@pytest.mark.parametrize("field", ["original_auto_x", "original_auto_y", "validated_by", "validated_at"])
def test_corrected_landmark_requires_lineage_and_audit(field):
    source = v1()
    source["landmarks"][2].pop(field)
    with pytest.raises(Lot05MigrationError):
        migrate(source)


@pytest.mark.parametrize("x,y", [
    (float("nan"), 1.0),
    (float("inf"), 1.0),
    (1.0, float("-inf")),
    (True, 1.0),
    ("10", 1.0),
])
def test_invalid_landmark_coordinates_fail_closed(x, y):
    source = v1()
    source["landmarks"][0]["x"] = x
    source["landmarks"][0]["y"] = y
    with pytest.raises(Lot05MigrationError):
        migrate(source)


def test_missing_unknown_or_duplicate_current_refs_fail_closed():
    source = v1()
    source.pop("current_landmark_refs")
    with pytest.raises(Lot05MigrationError):
        migrate(source)
    source = v1()
    source["current_landmark_refs"] = ["missing"]
    with pytest.raises(Lot05MigrationError):
        migrate(source)
    source = v1()
    source["current_landmark_refs"] = ["lm:r3:A", "lm:r3:A"]
    with pytest.raises(Lot05MigrationError):
        migrate(source)


def test_multiple_current_refs_for_same_landmark_fail_closed():
    source = v1()
    source["current_landmark_refs"] = ["lm:auto:A", "lm:r3:A"]
    with pytest.raises(Lot05MigrationError):
        migrate(source)


def test_source_patient_and_calibration_ambiguity_fail_closed():
    source = v1()
    source["sources"][0]["patient_id"] = 8
    with pytest.raises(Lot05MigrationError):
        migrate(source)
    source = v1()
    source["sources"].append({**copy.deepcopy(source["sources"][1]), "evidence_id": "cal:2"})
    with pytest.raises(Lot05MigrationError):
        migrate(source)


@pytest.mark.parametrize("width,height", [(0, 2400), (1935, 0), (-1, 2400)])
def test_invalid_dimensions_fail_closed(width, height):
    with pytest.raises(Lot05MigrationError):
        migrate(width=width, height=height)


def test_migration_timestamp_must_be_explicit_timezone_aware():
    assert migrate(migrated_at="2026-10-01T17:00:00+00:00")["migration"]["migrated_at"] == "2026-10-01T17:00:00+00:00"
    with pytest.raises(Lot05MigrationError):
        migrate(migrated_at="2026-10-01T17:00:00")


@pytest.mark.parametrize("mutation", ["snapshot", "case", "registry", "semantic_status", "calibration", "patient", "width", "height", "unit", "quality"])
def test_roundtrip_rejects_tampering_and_context_drift(mutation):
    v2 = migrate()
    if mutation == "snapshot":
        v2["migration"]["opaque_legacy_payload"]["revision"] = 999
    elif mutation == "case":
        v2["case_id"] = "case:other"
    elif mutation == "registry":
        v2["landmark_registry"][0]["canonical_id"] = "WRONG"
    elif mutation == "calibration":
        v2["coordinate_space"]["calibration_ref"] = "cal:other"
    elif mutation == "patient":
        v2["patient_id"] = 8
    elif mutation == "width":
        v2["coordinate_space"]["source_width_px"] = 999
    else:
        v2["coordinate_space"]["source_height_px"] = 999
    with pytest.raises(Lot05MigrationError):
        roundtrip_v2_to_v1(v2)


def test_aliases_cannot_shadow_or_duplicate_canonical_identity():
    v2 = migrate()
    v2["landmark_registry"][0]["aliases"] = [v2["landmark_registry"][1]["canonical_id"]]
    with pytest.raises(Lot05MigrationError):
        roundtrip_v2_to_v1(v2)
    v2 = migrate()
    v2["landmark_registry"][0]["aliases"] = ["legacy-x"]
    v2["landmark_registry"][1]["aliases"] = ["legacy-x"]
    with pytest.raises(Lot05MigrationError):
        roundtrip_v2_to_v1(v2)


def test_semantic_domains_do_not_flatten_soft_dental_or_occlusal_points():
    source = v1()
    manual = {
        "source_image_ref": "source:image",
        "origin": "MANUAL",
        "evidence_refs": ["source:image"],
        "evidence_status": "CLINICIAN_VALIDATED",
        "availability_status": "AVAILABLE",
    }
    source["landmarks"].extend([
        {"evidence_id": "lm:soft", "landmark_id": "Pog_soft", "x": 1.0, "y": 2.0, **manual},
        {"evidence_id": "lm:dental", "landmark_id": "U1_apex", "x": 3.0, "y": 4.0, **manual},
        {"evidence_id": "lm:occ", "landmark_id": "Occ_Ant", "x": 5.0, "y": 6.0, **manual},
    ])
    registry = {item["canonical_id"]: item for item in migrate(source)["landmark_registry"]}
    assert registry["Pog_soft"]["tissue_domain"] == "SOFT"
    assert registry["U1_apex"]["tissue_domain"] == "DENTAL"
    assert registry["Occ_Ant"]["tissue_domain"] == "CONSTRUCTION_ANCHOR"


def test_fixture_is_accepted_by_real_v1_typed_evidence_models():
    source = v1()
    for item in source["sources"]:
        SourceEvidence.model_validate(item)
    for item in source["landmarks"]:
        LandmarkEvidence.model_validate(item)


def test_machine_readable_v2_schema_contains_gate_invariants():
    schema_path = Path("docs/audits/schemas/cephalo_vnext_lot05_canonical_v2.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {"landmark_registry", "current_landmark_refs", "active_landmarks", "coordinate_space", "quality_metadata", "migration"} <= required
    migration_required = set(schema["properties"]["migration"]["required"])
    assert {"source_sha256", "migration_context_sha256", "migrated_at", "compatibility_class"} <= migration_required
    assert schema["properties"]["coordinate_space"]["properties"]["unit"]["const"] == "px"
    assert schema["properties"]["evidence_graph_version"]["const"] == "_evidence_graph_v1"
