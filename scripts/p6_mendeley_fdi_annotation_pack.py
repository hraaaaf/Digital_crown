#!/usr/bin/env python3
"""Build a clinician-annotation pack from the exact first-party Mendeley V3 source.

This script preserves source geometry only as annotation proposals. It never
creates FDI labels, infers left/right orientation, or promotes geometry/order to
ground truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

DATASET_ID = "73n3kz2k4k"
VERSION = 3
DOI = "10.17632/73n3kz2k4k.3"
LICENSE = "CC BY 4.0"
API = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files"
USER_AGENT = "DigitalCrown-P6-FDI-Annotation-Pack/1.0"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# Pinned by semantic provenance run 32910743873.
EXPECTED_FILE_COUNT = 111
EXPECTED_TOTAL_BYTES = 84_254_649
EXPECTED_METADATA_IMAGES = 107
EXPECTED_ANNOTATED_IMAGES = 25
EXPECTED_REGIONS = 772
EXPECTED_ANNOTATIONS_SHA256 = "b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd"


def http_open(url: str, attempts: int = 3):
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            return urllib.request.urlopen(req, timeout=120)
        except Exception as exc:  # noqa: BLE001 - upstream probe must report failures
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1 + attempt)
    raise RuntimeError(f"GET failed after {attempts} attempts: {url}: {last}")


def listing(folder_id: str = "root") -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"folder_id": folder_id, "version": VERSION})
    with http_open(f"{API}?{query}") as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Mendeley listing type: {type(payload).__name__}")
    return payload


def safe_name(name: str) -> str:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or len(p.parts) != 1:
        raise RuntimeError(f"Unsafe source filename: {name}")
    return p.name


def download(url: str, dest: Path) -> tuple[str, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    size = 0
    with http_open(url) as response, dest.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            size += len(chunk)
            out.write(chunk)
    return h.hexdigest(), size


def scalar_tokens(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, bool):
        return [str(value).lower()]
    if isinstance(value, (str, int, float)):
        token = str(value).strip()
        return [token] if token else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(scalar_tokens(item))
        return result
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            if item is True or item == 1 or str(item).strip().lower() == "true":
                token = str(key).strip()
                if token:
                    result.append(token)
            else:
                result.extend(scalar_tokens(item))
        return result
    token = str(value).strip()
    return [token] if token else []


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    images_dir = out / "images"
    images_dir.mkdir(parents=True)
    source_dir = out / "source"
    source_dir.mkdir(parents=True)

    items = listing("root")
    files: list[dict[str, Any]] = []
    total_bytes = 0
    annotations_path: Path | None = None

    for item in items:
        name = item.get("filename") or item.get("name")
        details = item.get("content_details") or {}
        url = details.get("download_url")
        if not name or not url:
            continue
        name = safe_name(str(name))
        target_dir = images_dir if Path(name).suffix.lower() in IMAGE_SUFFIXES else source_dir
        target = target_dir / name
        digest, actual_size = download(str(url), target)
        declared_size = details.get("size") or item.get("size")
        if declared_size is not None and int(declared_size) != actual_size:
            raise RuntimeError(
                f"Declared-size mismatch for {name}: declared={declared_size} actual={actual_size}"
            )
        files.append(
            {
                "filename": name,
                "source_file_id": item.get("id"),
                "sha256": digest,
                "size_bytes": actual_size,
                "kind": "image" if target_dir == images_dir else "source_metadata",
            }
        )
        total_bytes += actual_size
        if name.lower() == "annotations.json":
            annotations_path = target

    files.sort(key=lambda row: str(row["filename"]))
    if len(files) != EXPECTED_FILE_COUNT:
        raise RuntimeError(f"Pinned file count changed: {len(files)} != {EXPECTED_FILE_COUNT}")
    if total_bytes != EXPECTED_TOTAL_BYTES:
        raise RuntimeError(f"Pinned byte total changed: {total_bytes} != {EXPECTED_TOTAL_BYTES}")
    if annotations_path is None:
        raise RuntimeError("annotations.json missing")
    if sha256(annotations_path) != EXPECTED_ANNOTATIONS_SHA256:
        raise RuntimeError("annotations.json SHA256 changed from the pinned provenance result")

    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    metadata = annotations.get("_via_img_metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("annotations.json has no VIA _via_img_metadata object")
    if len(metadata) != EXPECTED_METADATA_IMAGES:
        raise RuntimeError(
            f"Pinned metadata image count changed: {len(metadata)} != {EXPECTED_METADATA_IMAGES}"
        )

    file_by_name = {str(row["filename"]): row for row in files}
    ledger_images: list[dict[str, Any]] = []
    annotated_image_count = 0
    region_count = 0

    for item in metadata.values():
        filename = safe_name(str(item.get("filename") or ""))
        if filename not in file_by_name or file_by_name[filename]["kind"] != "image":
            raise RuntimeError(f"VIA metadata image not found in first-party file inventory: {filename}")
        regions = item.get("regions", []) or []
        if regions:
            annotated_image_count += 1

        proposals: list[dict[str, Any]] = []
        for index, region in enumerate(regions):
            region_count += 1
            shape_attributes = region.get("shape_attributes") or {}
            region_attributes = region.get("region_attributes") or {}
            teeth_value = region_attributes.get("Teeth") if "Teeth" in region_attributes else None
            tokens = scalar_tokens(teeth_value)
            if tokens:
                raise RuntimeError(
                    f"Unexpected non-empty source Teeth token(s) in {filename} region {index}: {tokens}"
                )
            proposals.append(
                {
                    "proposal_id": f"{filename}#source-region-{index}",
                    "geometry_status": "SOURCE_PROPOSAL_ONLY",
                    "source_shape_attributes": shape_attributes,
                    "source_region_attribute_keys": sorted(str(k) for k in region_attributes.keys()),
                    "source_teeth_value": teeth_value,
                    "fdi": None,
                    "fdi_status": "UNASSIGNED_CLINICIAN_REQUIRED",
                    "visibility": "uncertain",
                    "eruption_state": "uncertain",
                    "annotator_status": "needs_review",
                    "comment": None,
                }
            )

        source_file = file_by_name[filename]
        ledger_images.append(
            {
                "image_id": f"mendeley-v3:{filename}",
                "source_id": f"mendeley:{DATASET_ID}:v{VERSION}",
                "source_filename": filename,
                "source_file_id": source_file["source_file_id"],
                "source_sha256": source_file["sha256"],
                "source_size_bytes": source_file["size_bytes"],
                "source_doi": DOI,
                "source_license": LICENSE,
                "rights_status": "CC_BY_4_0_FIRST_PARTY_PINNED",
                "redistribution_requires_attribution": True,
                "orientation": None,
                "orientation_status": "UNREVIEWED_CLINICIAN_REQUIRED",
                "dentition": "uncertain",
                "duplicate_group_id": None,
                "split": None,
                "image_status": "NOT_GROUND_TRUTH",
                "source_geometry_proposals": proposals,
                "clinician_instances": [],
            }
        )

    if annotated_image_count != EXPECTED_ANNOTATED_IMAGES:
        raise RuntimeError(
            f"Pinned annotated image count changed: {annotated_image_count} != {EXPECTED_ANNOTATED_IMAGES}"
        )
    if region_count != EXPECTED_REGIONS:
        raise RuntimeError(f"Pinned region count changed: {region_count} != {EXPECTED_REGIONS}")

    ledger_images.sort(key=lambda row: str(row["source_filename"]))
    source_manifest = {
        "schema_version": 1,
        "dataset": {
            "id": DATASET_ID,
            "version": VERSION,
            "doi": DOI,
            "record_url": f"https://data.mendeley.com/datasets/{DATASET_ID}/{VERSION}",
            "record_license": LICENSE,
            "provenance_run": 32910743873,
            "provenance_commit": "89521f94070b404bd09c4f0cb5e4ee5e55316b71",
        },
        "file_count": len(files),
        "total_downloaded_bytes": total_bytes,
        "files": files,
    }
    ledger = {
        "schema_version": 1,
        "status": "CLINICIAN_GROUND_TRUTH_REQUIRED",
        "contract": {
            "source_geometry_is_ground_truth": False,
            "source_fdi_labels_present": False,
            "geometry_to_fdi_inference_allowed": False,
            "orientation_required_before_fdi": True,
            "automatic_pathology_labels_in_scope": False,
        },
        "summary": {
            "image_count": len(ledger_images),
            "source_geometry_image_count": annotated_image_count,
            "source_geometry_region_count": region_count,
            "clinician_fdi_assigned_count": 0,
            "orientation_confirmed_count": 0,
            "split_assigned_count": 0,
        },
        "images": ledger_images,
    }

    (out / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "annotation_ledger.json").write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        "# Digital Crown P6 FDI clinician annotation pack\n\n"
        "Source: Mendeley `73n3kz2k4k` V3, DOI `10.17632/73n3kz2k4k.3`, record licence CC BY 4.0.\n\n"
        "This pack contains the exact public source images plus a clinician ledger. Existing VIA regions are retained only as geometry proposals. They are **not FDI ground truth**. The first-party `Teeth` attributes are empty and no FDI label is imported or inferred.\n\n"
        "Before any FDI assignment, a qualified dental clinician must confirm patient-right/patient-left orientation. Final FDI and geometry truth must be clinician-controlled under `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.\n\n"
        "No automatic pathology annotation belongs to this Phase-A pack.\n",
        encoding="utf-8",
    )

    pack_summary = {
        "status": "PASS_READY_FOR_CLINICIAN_ANNOTATION",
        "source_image_count": len(ledger_images),
        "source_geometry_image_count": annotated_image_count,
        "source_geometry_region_count": region_count,
        "clinician_fdi_assigned_count": 0,
        "orientation_confirmed_count": 0,
        "source_annotations_sha256": sha256(annotations_path),
        "ledger_sha256": sha256(out / "annotation_ledger.json"),
        "source_manifest_sha256": sha256(out / "source_manifest.json"),
    }
    (out / "PACK_SUMMARY.json").write_text(
        json.dumps(pack_summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(pack_summary, indent=2))


if __name__ == "__main__":
    main()
