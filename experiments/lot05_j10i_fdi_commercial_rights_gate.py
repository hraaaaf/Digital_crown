#!/usr/bin/env python3
"""LOT05/J10I: deny-by-default rights/provenance gate for FDI research selection.

This is an integrity check on a documented audit, NOT legal clearance, a
clinical certificate or an authorization to ship model weights. The audited
candidates are deliberately all BLOCKED or RESEARCH-ONLY. Manual external
rights review is needed for any future separate release gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/research/LOT05_J10I_FDI_COMMERCIAL_CANDIDATES.json"
)
ALLOWED_KINDS = frozenset(
    {"trained_fdi", "claimed_trained_fdi", "unadapted_base", "training_dataset"}
)
ALLOWED_DECISIONS = frozenset(
    {
        "BLOCKED_NONCOMMERCIAL", "HOLD_AGPL_AND_PROVENANCE",
        "BLOCKED_NONFUNCTIONAL_AND_RIGHTS", "RESEARCH_BASE_ONLY",
        "RESEARCH_DATASET_PROVENANCE_PENDING", "HOLD_LICENSE_AMBIGUOUS",
        "BLOCKED_PROJECT_APPROVAL", "BLOCKED_DATA_AND_RUNTIME",
    }
)
REQUIRED_FIELDS = frozenset({
    "id", "kind", "upstream", "declared_weights_license",
    "base_runtime_license", "fdi_classes",
    "rights_to_commercially_distribute", "training_dataset_provenance_verified",
    "usable_fd_i_model", "independent_clinical_validated",
    "commercial_release_approval", "decision", "evidence",
})


class RightsGateError(ValueError):
    pass


def _nonblank(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def review_catalog(data: object) -> dict:
    """Require every candidate to remain explicitly non-shippable.

    It is intentional that this tool cannot grant production clearance.
    Separate external rights & clinical signoffs cannot be represented by
    editing the research catalogue.
    """
    if not isinstance(data, dict):
        raise RightsGateError("audit_not_object")
    if data.get("schema") != "digital-crown-fdi-rights-audit-v1":
        raise RightsGateError("unsupported_audit_schema")
    if data.get("commercial_go") is not False or data.get("clinical_go") is not False:
        raise RightsGateError("audit_cannot_authorize_release")
    if data.get("authorization_source") != "None":
        raise RightsGateError("fabricated_authorization_source")
    if data.get("purpose") != "commercial_proprietary_windows_release":
        raise RightsGateError("wrong_audit_purpose")

    items = data.get("candidates")
    if not isinstance(items, list) or not items or len(items) > 32:
        raise RightsGateError("invalid_candidate_count")
    ids: set[str] = set()
    counts = {"trained_fdi": 0, "claimed_trained_fdi": 0,
              "unadapted_base": 0, "training_dataset": 0}
    for idx, item in enumerate(items):
        if not isinstance(item, dict) or not REQUIRED_FIELDS.issubset(item):
            raise RightsGateError(f"candidate_{idx}_missing_required_fields")
        item_id = item["id"]
        if not _nonblank(item_id) or item_id in ids:
            raise RightsGateError(f"candidate_{idx}_invalid_or_duplicate_id")
        ids.add(item_id)
        kind = item["kind"]
        if kind not in ALLOWED_KINDS:
            raise RightsGateError(f"{item_id}_kind_unrecognized")
        counts[kind] += 1
        url = item["upstream"]
        if not _nonblank(url) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
            raise RightsGateError(f"{item_id}_source_must_be_https")
        if item["decision"] not in ALLOWED_DECISIONS:
            raise RightsGateError(f"{item_id}_unknown_rights_decision")
        if not _nonblank(item["evidence"]) or len(item["evidence"]) < 60:
            raise RightsGateError(f"{item_id}_source_evidence_missing")
        if not _nonblank(item["declared_weights_license"]):
            raise RightsGateError(f"{item_id}_weights_license_missing")
        if not _nonblank(item["base_runtime_license"]):
            raise RightsGateError(f"{item_id}_runtime_license_missing")
        if (
            item["rights_to_commercially_distribute"] is not False
            or item["commercial_release_approval"] is not False
            or item["independent_clinical_validated"] is not False
        ):
            raise RightsGateError(f"{item_id}_release_clearance_not_audit_proven")
        if item["training_dataset_provenance_verified"] not in (True, False):
            raise RightsGateError(f"{item_id}_invalid_provenance_verdict")
        if item["usable_fd_i_model"] not in (True, False, None):
            raise RightsGateError(f"{item_id}_invalid_functional_verdict")
        if type(item["fdi_classes"]) is not int or item["fdi_classes"] not in (0, 32):
            raise RightsGateError(f"{item_id}_fdi_class_contract_error")
        if kind == "unadapted_base" and (
            item["fdi_classes"] != 0 or item["usable_fd_i_model"] is not False
        ):
            raise RightsGateError(f"{item_id}_base_cannot_be_called_fdi_trained")
        if kind == "training_dataset" and item["usable_fd_i_model"] is not False:
            raise RightsGateError(f"{item_id}_dataset_cannot_be_model")

    return {
        "schema": "digital-crown-fdi-rights-gate-v1",
        "status": "COMMERCIAL_AND_CLINICAL_RELEASE_BLOCKED",
        "candidate_count": len(items),
        "kinds": counts,
        "clinically_authorized_models": 0,
        "commercially_cleared_fdi_checkpoints": 0,
        "research_priority": "Apache-2.0 D-FINE Nano COCO foundation + provenance-vetted 32-FDI dataset",
        "none_of_the_models_has_been_selected_for_commercial_bundle": True,
    }


def check_no_research_weights_bundled(repo_root: Path) -> None:
    """Protect direct FDI packaging paths; do not scan entire medical repo."""
    roots = (
        repo_root / "frontend/public",
        repo_root / "backend/ai_models",
        repo_root / "backend/static/models",
    )
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (
                path.is_file() and path.suffix.lower()
                in {".pt", ".onnx", ".safetensors", ".pth", ".ckpt"}
                and ("fdi" in path.name.lower() or "tooth" in path.name.lower())
            ):
                raise RightsGateError(
                    "forbidden_fdi_model_in_product_assets:" + path.relative_to(repo_root).as_posix()
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        data = json.loads(args.catalog.read_text(encoding="utf-8"))
        report = review_catalog(data)
        check_no_research_weights_bundled(args.repo_root)
    except (OSError, ValueError) as e:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
