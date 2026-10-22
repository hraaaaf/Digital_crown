#!/usr/bin/env python3
"""LOT05/J10M: public LICENSING METADATA ONLY, no x-rays or patient images.

Read two official publication metadata endpoints (GitHub DENTEX README and
Hugging Face dataset metadata); cross-check explicit NC source declarations
against the immutable commercial HOLD. No downloads of dataset contents,
radiographs, pretrained model weights or private patient data.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/research/LOT05_J10M_PUBLIC_FDI_SOURCE_LICENSE_MATRIX.json"
SCHEMA = "digital-crown-fdi-j10m-primary-license-probe-v1"
GITHUB_API = "https://api.github.com/repos/ibrahimethemhamamci/DENTEX/contents/README.md?ref=main"
HF_API = "https://huggingface.co/api/datasets/ibrahimhamamci/DENTEX"
EXPECTED_GITHUB_README_BLOB_SHA = "812f949007be799b72bba131b13bef1fe6cae751"
EXPECTED_NONCOMMERCIAL_LICENSE = "cc-by-nc-sa-4.0"
REQUIRED_IDS = {
    "dentex-official", "aku-250", "dual-labeled-kaggle",
    "roboflow-dentalxray-1577", "roboflow-dentalwork-623",
    "tunisia-brahmi-v3", "figshare-3000",
}


class LicenseEvidenceError(ValueError):
    pass


def load_public_json(url: str) -> dict:
    """Only pinned API URLs; prohibit arbitrary data-server fetches."""
    if url not in {GITHUB_API, HF_API}:
        raise LicenseEvidenceError("disallowed_metadata_endpoint")
    request = Request(
        url, headers={"User-Agent": "DigitalCrown-FDI-Metadata-Only/1.0",
                      "Accept": "application/json"}
    )
    with urlopen(request, timeout=18) as resp:
        if resp.status != 200:
            raise LicenseEvidenceError("metadata_http_error")
        final = urlparse(resp.geturl())
        if final.scheme != "https" or final.netloc not in {
            "api.github.com", "huggingface.co"
        }:
            raise LicenseEvidenceError("metadata_redirect_domain_untrusted")
        raw = resp.read(350_001)
    if len(raw) > 350_000:
        raise LicenseEvidenceError("metadata_exceeds_limit")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise LicenseEvidenceError("metadata_not_json_object")
    return parsed


def verify_github_owner_license(obj: dict) -> dict:
    if obj.get("path") != "README.md" or obj.get("encoding") != "base64":
        raise LicenseEvidenceError("unexpected_github_file_type")
    if obj.get("sha") != EXPECTED_GITHUB_README_BLOB_SHA:
        raise LicenseEvidenceError("publisher_README_changed_review_required")
    raw = obj.get("content")
    if not isinstance(raw, str):
        raise LicenseEvidenceError("missing_first_party_license_content")
    try:
        document = base64.b64decode(raw, validate=False).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as e:
        raise LicenseEvidenceError("invalid_official_readme") from e
    # Scope match to exact license heading and first sentence; the repository
    # states MIT for CODE, but NONCOMMERCIAL for the DATA separately.
    section = re.search(r"(?mi)^## License[ \t]*\n([\s\S]{1,1000})", document)
    if section is None:
        raise LicenseEvidenceError("no_official_dataset_license_statement")
    text = section.group(1)
    if not re.search(
        r"The data is provided under the \[CC BY-NC-SA 4\.0 License\]",
        text,
        re.I,
    ):
        raise LicenseEvidenceError("data_license_not_explicitly_noncommercial")
    if not re.search(
        r"The rest of this repository is under the \[MIT License\]", text, re.I
    ):
        raise LicenseEvidenceError("data_versus_code_license_distinction_lost")
    return {
        "github_readme_blob_sha": obj["sha"],
        "github_readme_bytes": len(document.encode("utf-8")),
        "github_readme_sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        "publisher_declared_data_license": EXPECTED_NONCOMMERCIAL_LICENSE,
        "publisher_declared_non_data_code_license": "MIT",
    }


def verify_hf_dataset_license(obj: dict) -> dict:
    if obj.get("id") != "ibrahimhamamci/DENTEX":
        raise LicenseEvidenceError("wrong_huggingface_dataset_id")
    card_data = obj.get("cardData") or {}
    declared = card_data.get("license") if isinstance(card_data, dict) else None
    tags = obj.get("tags") or []
    if declared != EXPECTED_NONCOMMERCIAL_LICENSE:
        raise LicenseEvidenceError("huggingface_card_license_conflict_or_missing")
    if f"license:{EXPECTED_NONCOMMERCIAL_LICENSE}" not in tags:
        raise LicenseEvidenceError("huggingface_license_tag_conflict_or_missing")
    return {
        "huggingface_repo_id": obj["id"],
        "huggingface_declared_data_license": declared,
        "huggingface_revision": obj.get("sha") if isinstance(obj.get("sha"), str) else "",
    }


def review_matrix(obj: object) -> dict:
    if not isinstance(obj, dict) or obj.get("schema") != "digital-crown-fdi-j10m-public-licensing-review-v1":
        raise LicenseEvidenceError("bad_j10m_matrix_schema")
    for field in ("commercial_training_approval", "real_patient_radiographs_cloud_approved"):
        if obj.get(field) is not False:
            raise LicenseEvidenceError("dataset_training_authorization_cannot_be_self_asserted")
    rows = obj.get("candidates")
    if not isinstance(rows, list) or len(rows) != len(REQUIRED_IDS):
        raise LicenseEvidenceError("incomplete_dataset_license_review")
    if {row.get("id") for row in rows if isinstance(row, dict)} != REQUIRED_IDS:
        raise LicenseEvidenceError("review_candidate_names_changed")
    for row in rows:
        if row.get("commercial_use_approved") is not False or row.get("image_rights_verified_for_commercial_cloud") is not False:
            raise LicenseEvidenceError("candidate_commercial_release_not_approved")
        if not isinstance(row.get("source"), str) or urlparse(row["source"]).scheme != "https":
            raise LicenseEvidenceError("bad_source_uri")
        if not isinstance(row.get("evidence"), str) or len(row["evidence"]) < 85:
            raise LicenseEvidenceError("source_evidence_incomplete")
        if not isinstance(row.get("first_party_evidence"), list) or not row["first_party_evidence"]:
            raise LicenseEvidenceError("missing_source_evidence_urls")
        if not all(isinstance(x, str) and urlparse(x).scheme == "https" for x in row["first_party_evidence"]):
            raise LicenseEvidenceError("bad_source_evidence_uri")
        if not isinstance(row.get("commercial_decision"), str) or not row["commercial_decision"].startswith(("HOLD_", "BLOCK_")):
            raise LicenseEvidenceError("dataset_decision_must_block_commercial_training")
    dentex = next(x for x in rows if x["id"] == "dentex-official")
    if dentex.get("explicit_dataset_license") != "CC BY-NC-SA 4.0" or dentex.get("code_license") != "MIT (different material)":
        raise LicenseEvidenceError("data_code_license_differentiation_missing")
    return {"candidate_count": len(rows), "commercial_approvals": 0}


def probe() -> dict:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    inventory = review_matrix(matrix)
    github = verify_github_owner_license(load_public_json(GITHUB_API))
    hf = verify_hf_dataset_license(load_public_json(HF_API))
    if github["publisher_declared_data_license"] != hf["huggingface_declared_data_license"]:
        raise LicenseEvidenceError("source_license_disagreement")
    return {
        "schema": SCHEMA,
        "status": "PUBLIC_METADATA_CONFIRMS_FDI_COMMERCIAL_HOLD",
        "live_official_sources_read": 2,
        "data_images_downloaded": 0,
        "radiograph_licenses_approved_for_commercial_training": 0,
        "real_data_training_authorized": False,
        "clinical_use_authorized": False,
        "cloud_patient_radiographs_authorized": False,
        **inventory,
        **github,
        **hf,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = probe()
    except Exception as exc:
        report = {
            "schema": SCHEMA,
            "status": "PUBLIC_METADATA_FAIL_CLOSED",
            "error": f"{type(exc).__name__}: {str(exc)[:240]}",
            "real_data_training_authorized": False,
            "clinical_use_authorized": False,
        }
        args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
        return 1
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
