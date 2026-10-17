"""Exact-source verifier for the R23-G9 *nonclinical* Atlas33/Aariz snapshot.

No radiographs, individual annotations or protected patient records are loaded.
This verifies descriptive inventory consistency, not reference accuracy.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = "docs/audits/schemas/"
SOURCE = SCHEMAS + "cephalo_r23g9_atlas33_aariz_compatibility_preflight_v1.json"
ATLAS = "backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json"
REGISTRIES = {
    "lot06": SCHEMAS + "cephalo_vnext_lot06_executable_measurement_contract_v1.json",
    "g7": SCHEMAS + "cephalo_r23g7_atlas33_source_dependencies_v1.json",
    "w1": SCHEMAS + "cephalo_r23g8_w1_atlas33_orientation_dependencies_v1.json",
    "w2": SCHEMAS + "cephalo_r23g8_w2_atlas33_dental_manual_dependencies_v1.json",
    "w3": SCHEMAS + "cephalo_r23g8_w3_atlas33_craniomandibular_dependencies_v1.json",
}
COUNTS = {"lot06": 8, "g7": 3, "w1": 4, "w2": 7, "w3": 11}
DOI = "10.6084/m9.figshare.27986417.v1"
FROZEN = "73c742db47686b0cf8b75b599b6373d3fc707d9b25a440c8d81d3d99ced241df"


def read(path: str, root: Path = ROOT) -> dict:
    return json.loads((root / path).read_text(encoding="utf-8"))


def check_guardrails(snapshot: dict) -> None:
    if snapshot.get("clinical_release") is not False:
        raise ValueError("CLINICAL_NO_GO violated")
    if snapshot.get("independent_clinical_review") is not False:
        raise ValueError("Independent review invented")
    if snapshot.get("semantic_aliasing_authorized") is not False:
        raise ValueError("Unapproved semantic substitution")
    rows = snapshot.get("rows", [])
    if len(rows) != 33 or [x["order"] for x in rows] != list(range(1, 34)):
        raise ValueError("Atlas cardinality/order drift")
    if len(set(x["measurement_id"] for x in rows)) != 33:
        raise ValueError("Duplicate Atlas canonical identity")
    if any(x.get("clinical_measurement_validated") is not False
           or x.get("active_focus_authorized") is not False
           or x.get("expert_anatomical_review") is not False for x in rows):
        raise ValueError("Clinical/Focus evidence invented")


def verify(root: Path = ROOT) -> dict:
    report = read(SOURCE, root)
    check_guardrails(report)
    atlas = read(ATLAS, root)
    aariz = read(SCHEMAS + "cephalo_vnext_lot02_aariz_source.json", root)
    qual = read(SCHEMAS + "cephalo_vnext_lot02_aariz_qualification.json", root)
    if (report.get("profile_id") != atlas.get("protocol_id")
            or len(atlas["measurements"]) != 33
            or aariz["source"]["doi"] != DOI
            or aariz["source"]["license"] != "CC BY 4.0"
            or qual["source"]["manifest_v2_sha256"] != FROZEN
            or report["reference_source"] != DOI
            or report["reference_manifest_sha256"] != FROZEN
            or qual["gate_effect"]["clinical_acceptance"] != "NOT_GRANTED_BY_THIS_RECORD"):
        raise ValueError("Atlas/Aariz source identity or clinical status drift")
    registries = {name: read(path, root)["measurements"]
                  for name, path in REGISTRIES.items()}
    upstream = {}
    for entries in registries.values():
        for entry in entries:
            for key in ("construction_upstream_landmarks",
                        "construction_transitive_landmarks"):
                for name, landmarks in entry.get(key, {}).items():
                    if name in upstream and upstream[name] != landmarks:
                        raise ValueError("Contradictory construction: " + name)
                    upstream[name] = landmarks
    candidates = set(report["strict_literal_reference_mapping_not_approved_for_clinical_use"])
    actual = report["rows"]
    for i, atlas_row in enumerate(atlas["measurements"]):
        hits = [(name, r) for name, entries in registries.items()
                for r in entries if r["measurement_id"] == atlas_row["measurement_id"]]
        if len(hits) != 1 or atlas_row["order"] != i + 1:
            raise ValueError("Atlas membership/order drift")
        group, row = hits[0]
        if row.get("source_order", i + 1) != i + 1:
            raise ValueError("Source row order drift")
        points = list(row.get("required_landmarks", [])) + list(row.get("required_manual_landmarks", []))
        for key in ("construction_upstream_landmarks",
                    "construction_transitive_landmarks"):
            for landmarks in row.get(key, {}).values():
                points.extend(landmarks)
        missing_constructions = []
        for name in row.get("required_constructions", []):
            if name not in upstream:
                missing_constructions.append(name)
            else:
                points.extend(upstream[name])
        points = sorted(set(points))
        record = actual[i]
        expected = {
            "order": i + 1, "measurement_id": atlas_row["measurement_id"],
            "source_descriptor_group": group,
            "required_source_landmarks": points,
            "literal_candidate_ids_only": [p for p in points if p in candidates],
            "identities_not_in_strict_aariz_mapping": [p for p in points if p not in candidates],
            "construction_upstream_not_covered_by_these_descriptors": missing_constructions,
        }
        for key, value in expected.items():
            if record.get(key) != value:
                raise ValueError(f"Source descriptor mismatch at factor {i + 1}: {key}")
    counts = {k: sum(r["source_descriptor_group"] == k for r in actual) for k in COUNTS}
    unmatched = sorted(set(p for r in actual for p in r["identities_not_in_strict_aariz_mapping"]))
    if (counts != COUNTS or report["counts"]["groups"] != COUNTS
            or unmatched != report["identities_without_strict_mapping"]
            or len(unmatched) != 21
            or report["counts"]["unique_source_identities_without_strict_aariz_label"] != 21
            or [r["order"] for r in actual if not r["identities_not_in_strict_aariz_mapping"]] != [6]
            or report["counts"]["clinically_validated_atlas_measurements"] != 0):
        raise ValueError("Aggregate source coverage false confidence")
    return report


if __name__ == "__main__":
    result = verify()
    print("G9 VERIFIED SOURCE SNAPSHOT ONLY: 33 factors; 21 unmatched literal IDs; 0 clinical GO")
