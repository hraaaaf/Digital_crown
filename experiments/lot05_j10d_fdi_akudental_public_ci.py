#!/usr/bin/env python3
"""GitHub Actions research-only benchmark on publisher-released AKUDENTAL radiographs.

IMPORTANT: downloads only already-public non-commercial research films on ephemeral
no-secret runner; never reads private data or uploads images/COCO/case manifests.
Output is aggregate-only JSON. Does not grant commercial rights or clinical GO.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from lot05_j10d_fdi_akudental_coco_adapter import coco_to_manifest
from lot05_j10d_fdi_local_benchmark import BenchmarkError, evaluate, _run_local_model
from lot05_j10d_fdi_tooth_model_probe import (
    MODEL_REPO, MODEL_REVISION, MODEL_WEIGHTS_FILE, MODEL_WEIGHTS_SHA256,
)

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"})
SAFE_ERROR_CLASSES = ("BenchmarkError", "FileNotFoundError", "RuntimeError", "ValueError", "KeyError", "OSError")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_filename_resolution(coco: dict, images_root: Path, sample_size: int) -> dict:
    """Map source COCO source-filenames to actual public image paths, fail on collisions.

    Avoids source-specific folder naming assumptions while enforcing private root.
    Returns only in-memory edited annotations, never the image filenames in logs.
    """
    if sample_size < 1 or sample_size > 100:
        raise BenchmarkError("invalid_fixed_research_sample_size")
    images = coco.get("images")
    if not isinstance(images, list) or not images:
        raise BenchmarkError("missing_original_coco_images")
    sample_ids = {x.get("id") for x in sorted(images, key=lambda z: z["id"])[:sample_size]}
    if len(sample_ids) < min(sample_size, len(images)):
        raise BenchmarkError("duplicate_source_image_ids")
    root = images_root.resolve(strict=True)
    files = {}
    for candidate in root.rglob("*"):
        if candidate.is_symlink() or not candidate.is_file() or candidate.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        relative = candidate.resolve().relative_to(root)
        if candidate.name in files:
            # duplicate basename is unsafe even if not selected, since source
            # COCO file_name may give basenames with ambiguous references.
            raise BenchmarkError("ambiguous_public_image_basename")
        files[candidate.name] = relative.as_posix()
    if not files:
        raise BenchmarkError("public_image_files_missing")
    normalized = dict(coco)
    normalized["images"] = []
    for img in images:
        if img["id"] not in sample_ids:
            normalized["images"].append(img)
            continue
        basename = Path(img["file_name"]).name
        relative = files.get(basename)
        if relative is None:
            raise BenchmarkError("sample_image_missing_on_publisher_repo")
        clone = dict(img)
        clone["file_name"] = relative
        normalized["images"].append(clone)
    return normalized


def execute(source: Path, sample_size: int = 40) -> dict:
    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO
    # Source is a pinned reference to a public publisher, not private patient data.
    dataset = source / "AKUDENTAL"
    annotation_file = dataset / "akudental_instances.json"
    images_root = dataset / "images"
    if not annotation_file.is_file() or not images_root.is_dir():
        raise BenchmarkError("public_akudental_files_missing")
    original = json.loads(annotation_file.read_text(encoding="utf-8"))
    if not isinstance(original, dict):
        raise BenchmarkError("invalid_public_coco_root")
    cleaned = _safe_filename_resolution(original, images_root, sample_size)
    manifest, audit = coco_to_manifest(cleaned, images_root=images_root, max_images=sample_size)
    cases = manifest["cases"]
    if len(cases) < 5 or audit["ground_truth_teeth_selected"] < 20:
        raise BenchmarkError("insufficient_real_annotated_sample")
    downloaded = Path(hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_WEIGHTS_FILE,
                                      revision=MODEL_REVISION))
    if not downloaded.is_file() or sha256(downloaded) != MODEL_WEIGHTS_SHA256:
        raise BenchmarkError("untrusted_pinned_weights")
    # Real model inference entirely in ephemeral job. Never log individual film
    # identifiers, filenames, film pixels or nonaggregated model predictions.
    predictions = _run_local_model(cases, images_root, downloaded, .25)
    summary = evaluate(cases, predictions, .50, independence_audited=False)
    # Controls ensure only aggregates leave runner.
    return {
        "mission": "LOT05/05.7-J10D",
        "status": "PUBLIC_RESEARCH_FILMS_EVALUATED_UNVALIDATED",
        "purpose": "FDI tooth localization and numbering, not pathology",
        "data_source": "AKUDENTAL, public publisher dataset, noncommercial research",
        "data_source_training_overlap_audited": False,
        "data_source_labels_expert_revalidated_by_digital_crown": False,
        "cohort_selection": "first image_ids numerically sorted, fixed pre-inference",
        "source_images_in_original_coco": audit["images_total_in_coco"],
        "source_film_count": len(cases),
        "source_annotations_excluding_non_tooth": audit["ground_truth_teeth_selected"],
        "ignored_non_tooth_annotations_total": audit["ignored_non_tooth_annotations_total"],
        "source_images_with_no_FDI_annotation": audit["image_with_no_fdi_annotation"],
        "source_duplicate_GT_FDI_images": audit["selected_images_with_duplicate_gt_fdi"],
        "model": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "model_weight_sha256": MODEL_WEIGHTS_SHA256,
        "parameters": {"confidence_threshold": .25, "nms_iou": .50, "evaluation_iou": .50,
                       "inference_imgsz": 1024},
        "scores": summary["overall"],
        "bootstrap_film_level_ci": summary["bootstrap_95_percent_ci_fdi_recall_by_film"],
        "limitations": [
            "dataset independently sourced but overlap with model training not verified",
            "fixed research sample not a patient-level clinical validation",
            "permanents only; mixed and primary dentition not verified",
            "manufacturer and patient-subgroup generalization not independently verified",
            "model commercial redistribution and clinical-use authorization NOT demonstrated",
            "no diagnostic claims, no deployment GO",
        ],
        "clinical_approved": False,
        "commercial_redistribution_cleared": False,
        "research_only": True,
        "images_and_patient_ids_in_report": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publisher-repo", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = execute(args.publisher_repo, args.sample_size)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Do not print raw cases or per-image content to GitHub Actions console.
        print(json.dumps({
            "status": report["status"],
            "real_films": report["source_film_count"],
            "gt_teeth": report["scores"]["ground_truth_teeth"],
            "fdi_correct_recall": report["scores"]["fdi_correct_recall"],
            "localization_recall": report["scores"]["localization_recall"],
            "adjacent_fdi_swaps": report["scores"]["adjacent_fdi_swaps"],
            "clinical_approved": False,
        }, sort_keys=True))
    except Exception as exc:
        # Error details may contain patient/file paths or upstream private text:
        # only log a fixed error type, not exception text or traceback.
        reason = type(exc).__name__
        if reason not in SAFE_ERROR_CLASSES:
            reason = "UnexpectedResearchError"
        print(json.dumps({"status": "FAILED_RESEARCH_BENCHMARK",
                          "error_class": reason, "clinical_approved": False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
