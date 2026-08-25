#!/usr/bin/env python3
"""P6 research-only provenance probe for Mendeley dataset 73n3kz2k4k v3.

Downloads the public file inventory, hashes every downloadable file, and inspects
annotations.json without modifying product code or training a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DATASET_ID = "73n3kz2k4k"
VERSION = 3
API = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files"
USER_AGENT = "DigitalCrown-P6-Provenance-Probe/1.0"


def http_bytes(url: str, attempts: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - probe records upstream failures
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1 + attempt)
    raise RuntimeError(f"GET failed after {attempts} attempts: {url}: {last}")


def listing(folder_id: str = "root") -> tuple[list[dict[str, Any]], str]:
    query = urllib.parse.urlencode({"folder_id": folder_id, "version": VERSION})
    raw = http_bytes(f"{API}?{query}")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Mendeley listing type: {type(payload).__name__}")
    return payload, hashlib.sha256(raw).hexdigest()


def download_hash(url: str, capture: bool = False) -> tuple[str, int, bytes | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.sha256()
    total = 0
    chunks: list[bytes] | None = [] if capture else None
    with urllib.request.urlopen(req, timeout=120) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
            if chunks is not None:
                chunks.append(chunk)
    return h.hexdigest(), total, b"".join(chunks) if chunks is not None else None


def annotation_summary(raw: bytes) -> dict[str, Any]:
    doc = json.loads(raw.decode("utf-8"))
    metadata = doc.get("_via_img_metadata", {})
    if not isinstance(metadata, dict):
        raise RuntimeError("annotations.json has no VIA _via_img_metadata object")

    annotated: list[dict[str, Any]] = []
    all_region_attribute_keys: set[str] = set()
    nonempty_region_attributes = 0
    shape_counts: dict[str, int] = {}
    total_regions = 0

    for item in metadata.values():
        regions = item.get("regions", []) or []
        if regions:
            per_shape: dict[str, int] = {}
            for region in regions:
                total_regions += 1
                shape = (region.get("shape_attributes") or {}).get("name", "UNKNOWN")
                shape_counts[shape] = shape_counts.get(shape, 0) + 1
                per_shape[shape] = per_shape.get(shape, 0) + 1
                attrs = region.get("region_attributes") or {}
                if attrs:
                    nonempty_region_attributes += 1
                    all_region_attribute_keys.update(str(k) for k in attrs.keys())
            annotated.append({
                "filename": item.get("filename"),
                "region_count": len(regions),
                "shape_counts": per_shape,
            })

    annotated.sort(key=lambda x: str(x.get("filename")))
    return {
        "metadata_image_count": len(metadata),
        "annotated_image_count": len(annotated),
        "annotated_images": annotated,
        "total_regions": total_regions,
        "shape_counts": dict(sorted(shape_counts.items())),
        "nonempty_region_attributes_count": nonempty_region_attributes,
        "region_attribute_keys": sorted(all_region_attribute_keys),
        "source_fdi_labels_present": bool(nonempty_region_attributes or all_region_attribute_keys),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    items, root_listing_sha = listing("root")
    files: list[dict[str, Any]] = []
    annotation: dict[str, Any] | None = None

    for item in items:
        name = item.get("filename") or item.get("name")
        details = item.get("content_details") or {}
        url = details.get("download_url")
        if not name or not url:
            continue
        capture = str(name).lower() == "annotations.json"
        sha256, actual_size, raw = download_hash(url, capture=capture)
        declared_size = details.get("size") or item.get("size")
        files.append({
            "filename": name,
            "sha256": sha256,
            "size_bytes": actual_size,
            "declared_size_bytes": declared_size,
            "id": item.get("id"),
        })
        if capture and raw is not None:
            annotation = annotation_summary(raw)

    files.sort(key=lambda x: str(x["filename"]))
    if not files:
        raise RuntimeError("Mendeley listing contained no downloadable files")
    if annotation is None:
        raise RuntimeError("annotations.json was not found/downloaded")

    manifest = {
        "schema_version": 1,
        "dataset": {
            "id": DATASET_ID,
            "version": VERSION,
            "doi": "10.17632/73n3kz2k4k.3",
            "record_url": "https://data.mendeley.com/datasets/73n3kz2k4k/3",
            "api_url": API,
            "expected_record_license": "CC BY 4.0",
        },
        "root_listing_sha256": root_listing_sha,
        "file_count": len(files),
        "total_downloaded_bytes": sum(int(f["size_bytes"]) for f in files),
        "files": files,
        "annotations": annotation,
        "interpretation": {
            "direct_fdi_ground_truth_ready": bool(annotation["source_fdi_labels_present"]),
            "note": "This probe reports source annotation content only; it never synthesizes FDI labels.",
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "file_count": manifest["file_count"],
        "total_downloaded_bytes": manifest["total_downloaded_bytes"],
        "annotations": annotation,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
