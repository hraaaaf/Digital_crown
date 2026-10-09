#!/usr/bin/env python3
"""FAC-01 F01.13: verify 65 Facad profiles against observed source material.

This validator deliberately never certifies numeric, normative or geometric parity.
Use --self-test for fail-closed regression scenarios. No Facad runtime or patient data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "docs/audits/data/FACAD_314_D1C_EDITOR_DEFINITIONS_LEDGER_2026-10-09.csv"
CROSSWALK = "docs/audits/data/FACAD_314_F01_13_SOURCE_CROSSWALK_2026-10-09.csv"
MAP = "docs/audits/schemas/ortho_lot08_facad_dc_existing_protocol_mapping_v1.json"
PACKS = "docs/audits/schemas/cephalo_vnext_lot06_analysis_pack_registry_v1.json"
RICKETTS = "docs/audits/CEPHALO_LOT08_RICKETTS_32_13_SOURCE_LOCK_MATRIX.md"
DETAILS = "docs/audits/data/FACAD_314_F01_13_MEASUREMENT_CANDIDATES_2026-10-09.csv"
LOT06 = "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"

MATCHED_PACKS = {
    "Steiner": "STEINER_V1",
    "Tweed": "TWEED_DC_V1",
    "McNamara": "MCNAMARA_V1",
    "Downs": "DOWNS_V1",
    "Ricketts": "RICKETTS_V1",
}
VARIANTS = {
    "Ricketts (13 F)", "Ricketts (32 F)",
    "Ricketts acc G. Samson", "Ricketts Summary",
}
ALLOWED_MAPPING = {
    "NO_REPO_MAPPING",
    "EXACT_NAMED_MAPPING_UNVERIFIED",
    "NAME_ONLY_PROVISIONAL_PACK",
    "RICKETTS_VENDOR_VARIANT_UNRESOLVED",
}
FIELDS = (
    "ordinal", "facad_analysis_name", "facad_run_id",
    "facad_editor_state", "facad_measurements_extraction",
    "facad_patient_calculation", "facad_clinical_parity",
    "dc_candidate_pack_id", "dc_candidate_contract_refs",
    "existing_facad_dc_mapping_profile", "existing_mapping_label_count",
    "evidence_document_path", "evidence_document_blob_sha", "mapping_class",
    "facad_exact_composition", "geometry_equivalence",
    "normative_equivalence", "scientific_acceptance", "review_note",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != FIELDS and path.name == Path(CROSSWALK).name:
            raise ValueError("Unexpected crosswalk schema")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("Malformed CSV row")
    return rows


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


DETAIL_FIELDS = (
    "facad_profile", "facad_label", "source_mapping_status",
    "candidate_dc_measurement_id", "candidate_dc_relationship_id",
    "required_identity", "forbidden_aliases", "dc_id_registered_in_lot06",
    "geometry_equivalence", "numerical_parity", "source_map_path",
    "source_map_git_blob_sha", "source_mapping_caveat",
)


def validate_measurement_details(
    details_path: Path = ROOT / DETAILS, root: Path = ROOT
) -> dict[str, int]:
    with details_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != DETAIL_FIELDS:
            raise ValueError("Unexpected measurement candidate schema")
        rows = list(reader)
    source = json.loads((root / MAP).read_text(encoding="utf-8"))
    contract = json.loads((root / LOT06).read_text(encoding="utf-8"))
    valid_ids = {m["measurement_id"] for m in contract["measurements"]}
    expected = [
        (profile, label, meta)
        for profile, cfg in source["profiles"].items()
        for label, meta in cfg["mappings"].items()
    ]
    if len(rows) != len(expected) or len(rows) != 36:
        raise ValueError("Measurement candidates must cover exactly 36 explicit source labels")
    counts: Counter[str] = Counter()
    for idx, (row, (profile, label, src)) in enumerate(zip(rows, expected, strict=True), 1):
        status = src["status"]
        intended_id = src.get("dc_id", "")
        if intended_id and intended_id not in valid_ids:
            raise ValueError(f"Source candidate {idx}: ID missing from LOT06 registry")
        checks = {
            "facad_profile": profile,
            "facad_label": label,
            "source_mapping_status": status,
            "candidate_dc_measurement_id": intended_id,
            "candidate_dc_relationship_id": src.get("dc_relationship_id", ""),
            "required_identity": src.get("required_identity", ""),
            "forbidden_aliases": ";".join(src.get("forbidden_aliases", [])),
            "dc_id_registered_in_lot06": "TRUE" if intended_id else "NA",
            "geometry_equivalence": "UNVERIFIED",
            "numerical_parity": "NOT_TESTED",
            "source_map_path": MAP,
            "source_map_git_blob_sha": git_blob_sha(root / MAP),
        }
        for field, target in checks.items():
            if row.get(field) != target:
                raise ValueError(f"Candidate {idx} {profile}/{label}: {field} mismatch")
        if not row["source_mapping_caveat"]:
            raise ValueError(f"Candidate {idx}: evidence caveat omitted")
        if row.get(None) is not None:
            raise ValueError("Unexpected extra fields in candidate row")
        counts[status] += 1
    if dict(counts) != {
        "CANONICAL_LABEL_MATCH": 16,
        "CANDIDATE_GEOMETRY_REVIEW": 17,
        "EXISTING_DERIVED_RELATIONSHIP": 1,
        "BLOCKED_EXACT_LANDMARK": 2,
    }:
        raise ValueError("Unexpected mapping status distribution")
    return dict(counts)


def validate(crosswalk_path: Path, root: Path = ROOT) -> dict[str, int]:
    ledger = read_csv(root / LEDGER)
    crosswalk = read_csv(crosswalk_path)
    mapping = json.loads((root / MAP).read_text(encoding="utf-8"))
    registry = json.loads((root / PACKS).read_text(encoding="utf-8"))
    packs = {p["analysis_id"]: p for p in registry["analysis_packs"]}
    if len(ledger) != 65 or len(crosswalk) != 65:
        raise ValueError(f"Not exactly 65 profiles: ledger={len(ledger)} crosswalk={len(crosswalk)}")
    if len({r["analysis_name"] for r in ledger}) != 65:
        raise ValueError("Duplicate analysis names in ledger")
    if any(r["patient_calculation"] != "NOT_TESTED" or
           r["clinical_parity"] != "NOT_TESTED" for r in ledger):
        raise ValueError("Ledger clinical state changed: manual re-review required")
    counts: Counter[str] = Counter()
    for index, (source, row) in enumerate(zip(ledger, crosswalk, strict=True), 1):
        profile = source["analysis_name"]
        prefix = f"row {index} ({profile})"
        for key, value in (
            ("ordinal", source["ordinal"]),
            ("facad_analysis_name", profile),
            ("facad_run_id", source["github_run_id"]),
            ("facad_editor_state", source["editor_definition_state"]),
            ("facad_measurements_extraction", source["measurements_extraction"]),
            ("facad_patient_calculation", source["patient_calculation"]),
            ("facad_clinical_parity", source["clinical_parity"]),
            ("facad_exact_composition", "UNVERIFIED"),
            ("geometry_equivalence", "UNVERIFIED"),
            ("normative_equivalence", "NOT_ACTIVATED"),
            ("scientific_acceptance", "NOT_CERTIFIED"),
        ):
            if row[key] != value:
                raise ValueError(f"{prefix}: invalid {key}: {row[key]!r}")
        if int(row["ordinal"]) != index or not row["facad_run_id"].isdigit():
            raise ValueError(f"{prefix}: ordinal or run invalid")
        if not row["review_note"].strip():
            raise ValueError(f"{prefix}: missing human-readable limitation")
        mapped = profile if profile in mapping["profiles"] else ""
        if row["existing_facad_dc_mapping_profile"] != mapped:
            raise ValueError(f"{prefix}: mapping identity differs from exact source key")
        n = len(mapping["profiles"][mapped]["mappings"]) if mapped else 0
        if row["existing_mapping_label_count"] != str(n):
            raise ValueError(f"{prefix}: mapped-label count mismatch")
        candidate = MATCHED_PACKS.get(profile, "")
        if row["dc_candidate_pack_id"] != candidate:
            raise ValueError(f"{prefix}: unapproved pack candidate or alias")
        if candidate:
            p = packs[candidate]
            if p["composition_state"] != "PROVISIONAL_MEMBERSHIP" or p["membership_evidence_refs"]:
                raise ValueError(f"{prefix}: pack no longer provisional; audit update required")
            expected_refs = ";".join(p["scientific_contract_refs"])
        else:
            expected_refs = ""
        if row["dc_candidate_contract_refs"] != expected_refs:
            raise ValueError(f"{prefix}: source contract refs mismatch")
        if profile in VARIANTS:
            cls, doc = "RICKETTS_VENDOR_VARIANT_UNRESOLVED", RICKETTS
        elif profile == "Ricketts":
            cls, doc = "NAME_ONLY_PROVISIONAL_PACK", PACKS
        elif mapped:
            cls, doc = "EXACT_NAMED_MAPPING_UNVERIFIED", MAP
        else:
            cls, doc = "NO_REPO_MAPPING", ""
        if row["mapping_class"] != cls or cls not in ALLOWED_MAPPING:
            raise ValueError(f"{prefix}: mapping classification fail-open")
        if row["evidence_document_path"] != doc:
            raise ValueError(f"{prefix}: evidence document not explicit/incorrect")
        if doc:
            evidence = root / doc
            if not evidence.is_file() or row["evidence_document_blob_sha"] != git_blob_sha(evidence):
                raise ValueError(f"{prefix}: source evidence missing or SHA does not match")
        elif row["evidence_document_blob_sha"]:
            raise ValueError(f"{prefix}: unreferenced evidence hash")
        if profile == "Airway (McNamara)" and (candidate or mapped):
            raise ValueError("Airway (McNamara) incorrectly aliased to McNamara")
        if profile == "Ricketts (32 F)" and candidate:
            raise ValueError("Ricketts 32F incorrectly promoted to Ricketts canonical pack")
        counts[cls] += 1
    if dict(counts) != {
        "NO_REPO_MAPPING": 56,
        "EXACT_NAMED_MAPPING_UNVERIFIED": 4,
        "NAME_ONLY_PROVISIONAL_PACK": 1,
        "RICKETTS_VENDOR_VARIANT_UNRESOLVED": 4,
    }:
        raise ValueError(f"Unexpected class distribution: {dict(counts)}")
    validate_measurement_details(root=root)
    return dict(counts)


def self_test() -> None:
    source = ROOT / CROSSWALK
    assert sum(validate(source).values()) == 65
    original = read_csv(source)
    cases = [
        ("missing_profile", lambda r: r.pop()),
        ("promoted_approval", lambda r: r[0].update(scientific_acceptance="SOURCE_LOCKED")),
        ("silently_mapped_airway", lambda r: r[2].update(dc_candidate_pack_id="MCNAMARA_V1")),
        ("conflated_ricketts", lambda r: r[52].update(dc_candidate_pack_id="RICKETTS_V1")),
        ("invented_mapping", lambda r: r[0].update(existing_facad_dc_mapping_profile="Steiner")),
        ("false_provenance", lambda r: r[58].update(evidence_document_blob_sha="0" * 40)),
        ("numeric_claim", lambda r: r[10].update(facad_clinical_parity="PASS")),
        ("row_reordering", lambda r: r.reverse()),
        ("version_claim", lambda r: r[61].update(dc_candidate_contract_refs="RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1")),
    ]
    for label, corrupt in cases:
        rows = [r.copy() for r in original]
        corrupt(rows)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / Path(CROSSWALK).name
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(rows)
            try:
                validate(p)
            except (ValueError, KeyError):
                print(f"NEGATIVE_PASS={label}")
            else:
                raise AssertionError(f"Fail-open validation: {label}")
    detail_src = ROOT / DETAILS
    with detail_src.open(newline="", encoding="utf-8") as f:
        candidate_rows = list(csv.DictReader(f))
    negatives = [
        ("geometry_promotion", 0, "geometry_equivalence", "CERTIFIED"),
        ("fake_LOT06_id", 0, "candidate_dc_measurement_id", "M_FAKE_ID"),
        ("wrong_32F_profile", 29, "facad_profile", "Ricketts (13 F)"),
        ("forbidden_alias_erasure", 12, "forbidden_aliases", ""),
        ("status_promotion", 0, "source_mapping_status", "SOURCE_LOCKED"),
    ]
    for label, idx, field, modified in negatives:
        altered = [x.copy() for x in candidate_rows]
        altered[idx][field] = modified
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / Path(DETAILS).name
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=DETAIL_FIELDS)
                w.writeheader()
                w.writerows(altered)
            try:
                validate_measurement_details(p)
            except (ValueError, KeyError):
                print(f"NEGATIVE_PASS={label}")
            else:
                raise AssertionError(f"Measurement fail-open: {label}")
    print("SELF_TEST_PASS=14")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    result = validate(ROOT / CROSSWALK)
    detail_counts = validate_measurement_details()
    print("F01_13_ROWS=65")
    for k in sorted(result):
        print(f"{k}={result[k]}")
    print("F01_13_MEASUREMENT_CANDIDATES=36")
    for k in sorted(detail_counts):
        print(f"{k}={detail_counts[k]}")
    print("FACAD_PROFILE_COMPOSITION_CERTIFIED=false")
    print("FACAD_NUMERICAL_PARITY_CERTIFIED=false")
    print("CEPH08_GATE_OPEN=true")
    if args.self_test:
        self_test()
