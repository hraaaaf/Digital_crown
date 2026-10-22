#!/usr/bin/env python3
"""LOT05/J10O: public Roboflow FDI dataset METADATA quality gate only.

Live first-party published pages. No images, no downloads of annotations,
no private API keys and never any release/commercial model approval.
The publisher-reported CC BY 4.0 label does NOT establish image-level
clinical rights or processing permission for future commercial training.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.parse import urlparse

PROJECT = "https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi"
VERSION = PROJECT + "/dataset/1"
FDI = tuple(q * 10 + i for q in (1, 2, 3, 4) for i in range(1, 9))
SCHEMA = "digital-crown-j10o-roboflow-32-fdi-public-metadata-v1"


class DatasetMetadataError(ValueError):
    pass


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag in {"script","style","noscript"}:
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script","style","noscript"} and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())
    def result(self):
        return re.sub(r"\s+", " ", " ".join(self.text))


def public_text(url: str) -> str:
    if url not in (PROJECT, VERSION):
        raise DatasetMetadataError("external_page_not_allowlisted")
    req = Request(url, headers={
        "User-Agent": "DigitalCrown-J10O-Public-Research-Metadata/1.0",
        "Accept": "text/html",
    })
    with urlopen(req, timeout=20) as resp:
        parsed = urlparse(resp.geturl())
        if parsed.scheme != "https" or parsed.netloc != "universe.roboflow.com":
            raise DatasetMetadataError("untrusted_redirect")
        if resp.status != 200:
            raise DatasetMetadataError("metadata_http_not_success")
        raw = resp.read(1_500_001)
    if len(raw) > 1_500_000:
        raise DatasetMetadataError("public_project_page_too_large")
    if not raw.strip():
        raise DatasetMetadataError("empty_html_page")
    text = VisibleText()
    text.feed(raw.decode("utf-8", errors="replace"))
    return text.result()


def parse_pages(project_text: str, version_text: str) -> dict:
    proj = re.sub(r"\s+", " ", project_text)
    ver = re.sub(r"\s+", " ", version_text)
    if "Panoramic-Dental-Xray-FDI" not in proj:
        raise DatasetMetadataError("wrong_publisher_project")
    if not re.search(r"License\s*:?\s*CC BY 4\.0", proj, re.I):
        raise DatasetMetadataError("source_CC_BY_license_claim_missing_or_changed")
    if not re.search(r"(?:Images\s*\|\s*1\.6k|Images\s+1,577)", proj, re.I):
        raise DatasetMetadataError("source_image_count_changed")
    match = re.search(r"Classes\s*\(\s*32\s*\)(.*?)(?:Tags|Updated|About|Cite)", proj, re.I)
    if not match:
        raise DatasetMetadataError("fdi_class_section_unavailable")
    classes = [int(x) for x in re.findall(r"(?<!\d)(?:[1-4][1-8])(?!\d)", match.group(1))]
    if classes != list(FDI):
        raise DatasetMetadataError("missing_extra_or_reordered_fdi_classes")
    if "A description for this project has not been published yet" not in proj:
        raise DatasetMetadataError("provenance_description_status_changed_review_required")
    if "Stretch & Rotate" not in ver or not re.search(r"3503\s+(?:Total\s+)?Images", ver, re.I):
        raise DatasetMetadataError("public_augmentation_dataset_version_changed")
    if not re.search(r"3032\s+Images", ver) or not re.search(r"315\s+Images", ver) or not re.search(r"156\s+Images", ver):
        raise DatasetMetadataError("published_split_counts_changed")
    if not re.search(r"90°\s*Rotate", ver):
        raise DatasetMetadataError("rotation_augmentation_not_disclosed")
    return {
        "schema": SCHEMA,
        "status": "PUBLIC_FDI32_METADATA_CONFIRMED_RIGHTS_UNVERIFIED",
        "publisher": "dentalxray",
        "source_image_count_reported": 1577,
        "public_version_augmented_count": 3503,
        "train_augmented_examples": 3032,
        "validation_augmented_examples": 315,
        "test_augmented_examples": 156,
        "class_labels": list(FDI),
        "fdi_class_count": 32,
        "disclosed_augmentation": "stretch_1280_and_90_degree_rotation",
        "published_license_label": "CC BY 4.0 (unverified underlying image rights)",
        "original_clinical_provenance_verified": False,
        "patient_group_leakage_audited": False,
        "image_data_downloaded": False,
        "trained_fdi_weights_generated": False,
        "cloud_commercial_training_authorized": False,
        "clinical_use_authorized": False,
    }


def run() -> dict:
    return parse_pages(public_text(PROJECT), public_text(VERSION))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-json", type=Path, required=True)
    args = ap.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run()
    except Exception as exc:
        result = {"schema": SCHEMA, "status":"METADATA_FAIL_CLOSED",
                  "reason":type(exc).__name__ + ": " + str(exc)[:180],
                  "cloud_commercial_training_authorized":False,
                  "clinical_use_authorized":False}
        args.output_json.write_text(json.dumps(result, indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,sort_keys=True))
        return 1
    args.output_json.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
