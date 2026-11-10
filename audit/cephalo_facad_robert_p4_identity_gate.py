"""P4: six FACAD landmark terms vs actual Digital Crown canonical identity gate.

This audit executes the checked-out production *landmark identity projector*
before the canonical V2 typed adapter. The FACAD demo provides operator
MANUAL points, not certified SRPose observations. The projector must NOT turn
unproven FACAD Pog into the clinically canonical Pog_hard.

Definitional terminology matches are NOT patient-specific point-placement,
tooth-selection, source-image reference-frame or clinical-parity validation.
No false SRPose metadata, anatomical Frankfort references or mm/px scale.
"""
from __future__ import annotations

import importlib
import json
import math
from pathlib import Path

from audit import cephalo_facad_robert_public_ci as demo
from audit import cephalo_facad_robert_p3_canonical_adapter_probe as p3

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "audit/fixtures/facad_robert_p4_six_landmark_definition_crosswalk_v1.json"
SRPOSE_CONTRACT = ROOT / "docs/SRPOSE38_LANDMARK_CONTRACT.md"
CANONICAL_IDENTITY_DOC = ROOT / "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md"
DENTAL_SOURCE_DOC = ROOT / "docs/audits/CEPHALO_LOT08_RICKETTS32_FACAD_DENTAL_CLUSTER_RESOLUTION.md"

# Research vocabulary only. Actual clinical aliases come from the real
# backend.services.cephalo_landmark_identity_bridge, not this mapping.
NAMED_PAIRS = (
    ("Ii", "L1_incisal"), ("Iia", "L1_apex"),
    ("Is", "U1_incisal"), ("Isa", "U1_apex"),
    ("A", "A"), ("Pog", "Pog_hard"),
)
EXPECTED_METHODS = frozenset(p3.REQUIRED_CANONICAL_METHODS.values())


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_source_contract(contract: dict, docs: tuple[str, str, str]) -> None:
    require(contract.get("schema_version") ==
            "FACAD_ROBERT_P4_DEFINITIONAL_LANDMARK_CROSSWALK_V1",
            "wrong P4 definitional schema")
    require(contract.get("clinical_authority") is False and
            contract.get("robert_case_landmarks_image_placement_independently_verified") is False
            and contract.get("facad_to_dc_canonical_identity_bridge_authorized") is False
            and contract.get("frankfort_anatomical_landmarks_present") is False
            and contract.get("quantized_coordinate_step_mm") == 0.1,
            "unsubstantiated anatomical or clinical promotion")
    vendor = contract.get("vendor_manual", {})
    require(vendor.get("url") ==
            "https://www.facad.com/dox/dox38/FacadTracingUsersGuide_ENG.pdf"
            and vendor.get("page_printed") == 2
            and vendor.get("publication_date") == "2014-05-07"
            and "not independent verification" in vendor.get("warning", ""),
            "FACAD older manual/version boundary modified")
    rows = contract.get("records", [])
    require(type(rows) is list and len(rows) == 6 and
            [(x.get("facad_landmark"), x.get("dc_research_target")) for x in rows] ==
            list(NAMED_PAIRS), "crosswalk identity or ordering changed")
    srpose, identity_doc, dental_doc = docs
    require("only when the point is produced by the exact certified SRPose38" in identity_doc
            and "Pog → Pog_hard" in identity_doc
            and "soft-tissue Pog" in identity_doc,
            "DC canonical hard-tissue identity contract changed")
    require("ILi/A-Pog = Angle4p(Pog,A,Iia,Ii)" in dental_doc
            and "ILs/A-Pog = Angle4p(Isa,Is,A,Pog)" in dental_doc,
            "FACAD source dental axis definitions drifted")
    for row in rows:
        require(row.get("shared_anatomical_role_hypothesis") is True
                and row.get("robert_marker_placement_independently_verified") is False
                and row.get("authorized_to_promote_to_dc_canonical_identity") is False,
                "crosswalk row falsely claims anatomical/clinical verification")
        target = row["dc_research_target"]
        phrase = row["dc_corpus_definition_phrase"]
        vendor_label = row.get("facad_3_8_definition", "")
        require(type(phrase) is str and phrase and
                type(vendor_label) is str and vendor_label,
                "empty landmark term definitions")
        if target == "Pog_hard":
            require(phrase in identity_doc and
                    "Pog" in vendor_label, "bony/soft Pog scope changed")
        else:
            require(phrase in srpose, "DC incisor/A anatomy changed")


def assess(fixture: dict, contract: dict, docs: tuple[str, str, str]) -> dict:
    validate_source_contract(contract, docs)
    source = demo.validate_fixture(fixture)
    require(source["clinical_no_go"] is True
            and source["clinical_numeric_parities_verified"] == 0,
            "FACAD demo incorrectly certified")
    require(not ({"P", "Or", "Po"} & set(fixture["points_mm"])),
            "new Frankfort coordinates need independent review; never fake")
    require(set(x for x, _ in NAMED_PAIRS).issubset(fixture["points_mm"]),
            "P4 must have all six observed FACAD landmarks")
    ev, canonical, method_bridge = p3._real_typed_adapter()
    bridge = importlib.import_module("backend.services.cephalo_landmark_identity_bridge")
    construction = importlib.import_module("backend.services.cephalo_construction_evidence_adapter")
    require(bridge.CANONICAL_LANDMARK_ALIASES.get("Pog") == "Pog_hard",
            "production identity bridge no longer recognizes Pog hard mapping")
    landmarks = {}
    for source_label, target in NAMED_PAIRS:
        # Deliberately preserve untrusted legacy "Pog" rather than creating
        # "Pog_hard" directly as P3's exploratory geometry does.
        dc_id = source_label if source_label == "Pog" else target
        x, y = fixture["points_mm"][source_label]
        require(type(x) in (int, float) and type(y) in (int, float)
                and math.isfinite(x) and math.isfinite(y),
                "nonfinite or nonnumeric FACAD point")
        landmarks[dc_id] = ev.LandmarkEvidence(
            evidence_id="facad_p4_legacy_manual_" + dc_id,
            landmark_id=dc_id, x=x, y=y, source_image_ref=p3.STUDY_REF,
            origin=ev.LandmarkOrigin.MANUAL,
            evidence_status=ev.EvidenceStatus.OBSERVED,
            evidence_refs=[p3.STUDY_REF],
        )
    projected = bridge.project_canonical_landmark_identities(
        landmarks, previous_auto_landmarks=()
    )
    require("Pog" in projected and "Pog_hard" not in projected,
            "UNSAFE: operator/manual FACAD Pog was promoted to certified Pog_hard")
    measurements = canonical.materialize_canonical_analysis_v2_measurements(
        measurement_namespace="FACAD_P4_UNCERTIFIED_MANUAL_GEOMETRY",
        landmarks=projected, mm_per_pixel=None, calibration_ref=None,
        constructions={}, image_orientation=None,
    )
    blocked = []
    for method in sorted(EXPECTED_METHODS):
        matching = [item for item in measurements if item.method_id == method]
        require(len(matching) == 1, "typed canonical Ricketts measurement missing/duplicate")
        item = matching[0]
        require(item.availability_status == ev.AvailabilityStatus.NOT_COMPUTABLE
                and item.value is None and item.unit == "deg"
                and item.analysis_id == "RICKETTS" and not item.requires_calibration,
                "UNSAFE: canonical Ricketts angle produced despite uncertified Pog")
        blocked.append(method)
    craniom = construction.materialize_craniom_constructions(
        projected, construction_namespace="FACAD_P4_UNCERTIFIED_DENTAL_GEOMETRY")
    inter = craniom["CRANIOM_U1_L1_INTERINCISAL_V1"]
    require(inter.availability_status == ev.AvailabilityStatus.AVAILABLE
            and isinstance(inter.geometry.get("computed_angle_deg"), (int, float))
            and math.isfinite(float(inter.geometry["computed_angle_deg"])),
            "typed interincisal geometric construction failed without Pog")
    require(method_bridge.canonical_measurement_id_for_method(
        "CRANIOM_INTERINCISAL_DEG_V1") == "M_INTERINCISAL_DEG_V1",
        "CRANIOM method bridge changed")
    return {
        "status": "P4_SOURCE_TERMINOLOGY_RECONCILED_RUNTIME_CANONICAL_PROMOTION_BLOCKED",
        "source_manual_version": "FACAD_3_8_VOCABULARY_ONLY",
        "facad_observed_demo_version": "FACAD_3_14_1_1111_OPERATOR_EXPORT",
        "source_terminology_pairs_reviewed": 6,
        "landmark_placement_on_ceph_image_independently_verified": 0,
        "facad_pog_projected_to_dc_pog_hard": False,
        "typed_canonical_v2_angles_blocked_by_unverified_identity": blocked,
        "typed_craniom_interincisal_geometry_available": True,
        "full_clinical_runtime_executed": False,
        "cross_vendor_clinical_parities": 0,
        "clinical_no_go": True,
    }


def main() -> int:
    try:
        demo.read_checked_fixture(demo.FIXTURE)
        fixture = json.loads(demo.FIXTURE.read_text(encoding="utf-8"))
        contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
        docs = (
            SRPOSE_CONTRACT.read_text(encoding="utf-8"),
            CANONICAL_IDENTITY_DOC.read_text(encoding="utf-8"),
            DENTAL_SOURCE_DOC.read_text(encoding="utf-8"),
        )
        result = assess(fixture, contract, docs)
    except (OSError, ValueError, KeyError, TypeError, ImportError,
            AttributeError, json.JSONDecodeError) as exc:
        print("FACAD_P4=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    print("FACAD_P4=REAL_DC_LANDMARK_IDENTITY_BRIDGE_EXECUTED")
    print("FACAD_P4_DEFINITIONAL_PAIRS=6")
    print("FACAD_P4_IMAGE_PLACEMENTS_INDEPENDENTLY_VERIFIED=0")
    print("FACAD_P4_UNCERTIFIED_POG_TO_POG_HARD=BLOCKED")
    print("FACAD_P4_CANONICAL_V2_RICKETTS_ANGLES_NOT_COMPUTABLE=2")
    print("FACAD_P4_CRANIOM_INTERINCISAL_TYPED_GEOMETRY=AVAILABLE_EDUCATIONAL_ONLY")
    print("FACAD_P4_CLINICAL_PARITIES=0")
    print("CLINICAL_NO_GO=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
