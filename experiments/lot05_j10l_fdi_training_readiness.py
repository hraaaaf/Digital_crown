#!/usr/bin/env python3
"""LOT05/J10L: immutable 32-FDI class contract + dataset provenance gate.

A PASS means ONLY the code recognizes incomplete evidence and refuses
real-image/cloud/commercial training. No local manifest, README or Roboflow
license badge can grant clearance. This module has no network dependencies.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = "digital-crown-fdi-dataset-provenance-v1"
HERE = Path(__file__).resolve().parents[1]
AUDIT = HERE / "docs/research/LOT05_J10L_DATASET_RIGHTS_EVIDENCE.json"
FDI_32 = tuple(q * 10 + i for q in (1, 2, 3, 4) for i in range(1, 9))
PROVENANCE_FIELDS = (
    "publisher_identity_and_rights_verified",
    "patient_deidentification_and_use_verified",
    "cloud_training_processing_rights_verified",
    "complete_32_fdi_labels_confirmed",
    "original_release_splits_verified",
    "secondary_usage_restrictions_cleared",
)
SPECIFIC_DATASET_DENIALS = {
    "roboflow-1577": "HOLD_PROVENANCE",
    "tunisia-brahmi-v3": "HOLD_FDI_LABELS_AND_CLINICAL_RIGHTS",
    "sts-2024": "BLOCK_RESEARCH_ONLY_AND_30_LABELED",
    "tl-pano-zenodo": "BLOCK_NONCOMMERCIAL_RESTRICTED",
    "inredd-pan924": "BLOCK_REQUIRES_INDIVIDUAL_PERMISSION",
    "mendeley-eftimie": "BLOCK_ADDITIONAL_NONCOMMERCIAL_DUA",
    "akudental": "BLOCK_NONCOMMERCIAL",
    "figshare-3000": "HOLD_CLASS_SCHEMA_AND_RIGHTS",
}


class FDITrainingBlock(ValueError):
    pass


def validated_fdi_classes(value: object) -> list[int]:
    """Fixed right/left permanent FDI numbering; never renumber from x-position."""
    if type(value) is not list or value != list(FDI_32):
        raise FDITrainingBlock("fdi_class_order_or_count_mismatch")
    return value


def audit_dataset_manifest(payload: object) -> dict:
    """Check evidence completeness and refuse all clinical/cloud model training.

    A later *separate* signed legal/clinical gate is needed to enable use of
    real radiographs; editable JSON alone cannot promote a candidate.
    """
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise FDITrainingBlock("missing_or_malformed_audit")
    if payload.get("decision") != "REAL_PANORAMIC_TRAINING_BLOCKED":
        raise FDITrainingBlock("dataset_cannot_self_certify_release")
    for flag in ("cloud_processing_approval", "commercial_dataset_go",
                 "independent_patient_rights_review"):
        if payload.get(flag) is not False:
            raise FDITrainingBlock("unaudited_global_rights_override:" + flag)
    if payload.get("synthetic_geometry_only_allowed") is not True:
        raise FDITrainingBlock("not_synthetic_only")
    validated_fdi_classes(payload.get("expected_permanent_fdi_classes"))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(SPECIFIC_DATASET_DENIALS):
        raise FDITrainingBlock("dataset_manifest_incomplete")
    seen: set[str] = set()
    for item in candidates:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise FDITrainingBlock("bad_dataset_candidate")
        dataset_id = item["id"]
        if dataset_id in seen or dataset_id not in SPECIFIC_DATASET_DENIALS:
            raise FDITrainingBlock("unknown_or_duplicate_dataset")
        seen.add(dataset_id)
        if item.get("decision") != SPECIFIC_DATASET_DENIALS[dataset_id]:
            raise FDITrainingBlock("invalid_dataset_license_status:" + dataset_id)
        for prop in PROVENANCE_FIELDS:
            if type(item.get(prop)) is not bool:
                raise FDITrainingBlock("missing_credible_provenance_field:" + prop)
        if (
            item["publisher_identity_and_rights_verified"]
            and item["patient_deidentification_and_use_verified"]
            and item["cloud_training_processing_rights_verified"]
            and item["complete_32_fdi_labels_confirmed"]
            and item["original_release_splits_verified"]
            and item["secondary_usage_restrictions_cleared"]
        ):
            raise FDITrainingBlock("externally_audited_candidate_must_be_separately_authorized")
        if not isinstance(item.get("published_license"), str) or not item["published_license"].strip():
            raise FDITrainingBlock("unknown_license_label")
        if not isinstance(item.get("evidence"), str) or len(item["evidence"]) < 80:
            raise FDITrainingBlock("evidence_not_recorded")
        url = item.get("url")
        if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
            raise FDITrainingBlock("dataset_source_not_https")
    if seen != set(SPECIFIC_DATASET_DENIALS):
        raise FDITrainingBlock("dataset_list_not_exhaustive")
    return {
        "schema": "digital-crown-fdi-j10l-dataset-decision-v1",
        "status": "REAL_DATA_TRAINING_BLOCKED_SYNTHETIC_ONLY",
        "dataset_candidates": len(seen),
        "permanent_fdi_classes": list(FDI_32),
        "external_radiographs_fetched": False,
        "commercial_dataset_go": False,
        "clinical_use_go": False,
        "cloud_image_processing_go": False,
    }


def check_research_only_mode(mode: str, dataset_path: str | None = None) -> None:
    if mode != "synthetic_geometry" or dataset_path:
        raise FDITrainingBlock("no_real_xrays_or_training_dataset_approved")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", type=Path, default=AUDIT)
    ap.add_argument("--mode", type=str, default="synthetic_geometry")
    ap.add_argument("--dataset-path", type=str, default="")
    args = ap.parse_args()
    try:
        check_research_only_mode(args.mode, args.dataset_path)
        verdict = audit_dataset_manifest(json.loads(args.audit.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(verdict, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
