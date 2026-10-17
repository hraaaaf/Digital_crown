"""R23-G10 local-only expert annotation *assignment* intake, never clinical truth.

No images, anatomical coordinates or patient records are exported or admitted.
Optional protected LOT02 manifest verifies frozen byte hash and source/split binding.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "CEPHALO_R23G10_ATLAS33_EXPERT_ANNOTATION_INTAKE_V1"
PROFILE = "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1"
DOI = "10.6084/m9.figshare.27986417.v1"
FROZEN_LOT02_SHA = "73c742db47686b0cf8b75b599b6373d3fc707d9b25a440c8d81d3d99ced241df"
G9_REL = "docs/audits/schemas/cephalo_r23g9_atlas33_aariz_compatibility_preflight_v1.json"
TEMPLATE_REL = "docs/audits/schemas/cephalo_r23g10_atlas33_annotation_intake_template_v1.json"
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{3,48}\Z")
CASE_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
TOP_KEYS = {"schema_version", "profile_id", "lot02", "source_profile", "scope",
            "clinical_release", "expert_reference_verified", "privacy", "protocol", "cases"}
CASE_KEYS = {"case_token", "lot02_case_id", "split", "source_image_sha256",
             "required_annotation_ids", "assigned_blinded_experts",
             "calibration_status", "orientation_status", "annotation_status"}

def demand(test, message):
    if not test:
        raise ValueError(message)

def exact(obj, keys, name):
    demand(isinstance(obj, dict) and set(obj) == keys,
           name + " unexpected/missing fields (possible unsafe payload)")
    return obj

def valid_sha(value):
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))

def safe_token(value, pattern=TOKEN_RE):
    return isinstance(value, str) and bool(pattern.fullmatch(value))

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()

def verify_intake(intake, matrix, *, source_manifest=None, source_manifest_sha=None):
    """Source/assignment structural check; always returns clinical NO-GO."""
    exact(intake, TOP_KEYS, "G10 intake")
    demand(intake["schema_version"] == SCHEMA and
           intake["profile_id"] == PROFILE == matrix.get("profile_id"),
           "G10/Atlas scientific identity drift")
    demand(intake["scope"] == "LOCAL_ASSIGNMENT_METADATA_ONLY__NO_LANDMARK_COORDINATES",
           "G10 scope cannot become a patient-value record")
    demand(intake["clinical_release"] is False and
           intake["expert_reference_verified"] is False,
           "Unproven clinical reference/release must remain false")
    demand(matrix.get("clinical_release") is False and
           matrix.get("independent_clinical_review") is False and
           matrix.get("semantic_aliasing_authorized") is False,
           "G9 authority drift")
    demand(matrix.get("counts", {}).get("atlas_rows") == 33 and
           matrix.get("counts", {}).get("clinically_validated_atlas_measurements") == 0,
           "G9 cardinality/clinical authority drift")
    upstream = exact(intake["lot02"],
                     {"source_doi", "frozen_manifest_sha256", "local_source_manifest_verified"}, "lot02")
    demand(upstream["source_doi"] == DOI == matrix.get("reference_source") and
           upstream["frozen_manifest_sha256"] == FROZEN_LOT02_SHA ==
           matrix.get("reference_manifest_sha256") and
           upstream["local_source_manifest_verified"] is False,
           "Self-asserted or drifting LOT02 source evidence")
    profile = exact(intake["source_profile"],
                    {"source_edition", "atlas_profile_id", "atlas_factor_count"}, "source_profile")
    demand(profile["source_edition"] == "Atlas2009" and
           profile["atlas_profile_id"] == PROFILE and
           type(profile["atlas_factor_count"]) is int and
           profile["atlas_factor_count"] == 33,
           "Atlas edition/cardinality drift")
    privacy = exact(intake["privacy"],
                    {"contains_real_patient_data", "contains_coordinates",
                     "contains_images_or_paths", "upload_allowed"}, "privacy")
    demand(all(privacy[key] is False for key in privacy),
           "Protected data, coordinates, paths and upload are forbidden")
    policy = exact(intake["protocol"],
                   {"annotation_mode", "blind_independent_experts",
                    "minimum_independent_experts", "intraobserver_repeat_required",
                    "same_image_required", "adjudication_policy", "allowed_splits",
                    "untouched_test_reserved",
                    "calibration_and_orientation_require_external_review"}, "protocol")
    demand(policy == {
        "annotation_mode": "MANUAL_SOURCE_SPECIFIC_ATLAS33",
        "blind_independent_experts": True, "minimum_independent_experts": 2,
        "intraobserver_repeat_required": True, "same_image_required": True,
        "adjudication_policy": "PREDECLARED_BEFORE_REFERENCE_UNBLINDING",
        "allowed_splits": ["train", "valid"], "untouched_test_reserved": True,
        "calibration_and_orientation_require_external_review": True,
    }, "Human protocol, blinding or held-out cohort altered")
    demand(isinstance(intake["cases"], list) and len(intake["cases"]) <= 1000,
           "Unbounded or invalid case list")
    ids = matrix.get("identities_without_strict_mapping")
    demand(isinstance(ids, list) and len(ids) == 21 and len(set(ids)) == 21 and
           ids == sorted(ids) and
           {"Pt_Ricketts", "PR_Ricketts_PTV", "Po_anatomic",
            "Pog_hard", "Pm_Ricketts", "PNS_Ricketts"}.issubset(set(ids)),
           "Exact missing source identities drift")

    originals = {}
    if source_manifest is not None:
        demand(source_manifest_sha == FROZEN_LOT02_SHA and
               source_manifest.get("schema") == "CEPHALO_LOT02_AARIZ_MANIFEST_V2" and
               source_manifest.get("source", {}).get("doi") == DOI,
               "Actual protected LOT02 manifest bytes/schema/DOI mismatch")
        for item in source_manifest.get("cases", []):
            key = item.get("case_id")
            demand(isinstance(key, str) and key not in originals,
                   "Invalid/duplicate LOT02 case")
            originals[key] = item
        demand(len(originals) == 1000 and source_manifest.get("counts") ==
               {"train": 700, "valid": 150, "test": 150},
               "LOT02 frozen corpus size or splits drift")
    else:
        demand(source_manifest_sha is None, "Unbacked LOT02 manifest hash")

    seen_tokens, seen_source_cases = set(), set()
    for case in intake["cases"]:
        exact(case, CASE_KEYS, "case")
        demand(safe_token(case["case_token"]) and
               safe_token(case["lot02_case_id"], CASE_ID_RE),
               "Case identity must be opaque pseudonym, no names/paths")
        demand(case["case_token"] not in seen_tokens and
               case["lot02_case_id"] not in seen_source_cases,
               "Duplicate case assignment")
        seen_tokens.add(case["case_token"])
        seen_source_cases.add(case["lot02_case_id"])
        demand(case["split"] in ("train", "valid"),
               "Untouched test split must not be exposed for G10 development")
        demand(valid_sha(case["source_image_sha256"]), "Invalid image SHA256")
        demand(case["required_annotation_ids"] == ids,
               "Source-specific 21 IDs missing, reordered or aliased")
        reviewers = case["assigned_blinded_experts"]
        demand(isinstance(reviewers, list) and len(reviewers) == 2 and
               all(safe_token(x) for x in reviewers) and reviewers[0] != reviewers[1],
               "Two distinct blinded pseudonymous expert assignments required")
        demand(case["calibration_status"] == "PENDING_INDEPENDENT_VERIFICATION" and
               case["orientation_status"] == "PENDING_INDEPENDENT_VERIFICATION" and
               case["annotation_status"] == "UNANNOTATED",
               "Unproven human anatomy, scale or orientation cannot be verified")
        if source_manifest is not None:
            original = originals.get(case["lot02_case_id"])
            demand(original is not None and original.get("split") == case["split"] and
                   original.get("image", {}).get("sha256") == case["source_image_sha256"],
                   "Wrong case/split/image hash for frozen LOT02 manifest")

    return {
        "schema_version": "CEPHALO_R23G10_INTAKE_QA_REPORT_V1",
        "source_inventory_consistent": True,
        "case_assignment_count": len(seen_tokens),
        "source_manifest_frozen_bytes_checked": source_manifest is not None,
        "ready_for_anatomical_measurement_validation": False,
        "goldset_clinically_verified": False,
        "clinical_release": False,
        "status": "ASSIGNMENT_METADATA_STRUCTURALLY_VERIFIED__HUMAN_GOLDSET_NOT_ESTABLISHED",
        "caveat": "No raw image/coordinate or human signature checked; never clinical GO.",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--source-manifest", type=Path,
                    help="Protected local LOT02 manifest only; never upload this file")
    args = ap.parse_args()
    result = verify_intake(
        load(args.intake), load(args.repo_root / G9_REL),
        source_manifest=load(args.source_manifest) if args.source_manifest else None,
        source_manifest_sha=sha_file(args.source_manifest) if args.source_manifest else None)
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
