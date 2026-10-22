#!/usr/bin/env python3
"""J10L: REAL fine-tuning code-path dry-run on synthetic geometry ONLY.

This is NOT a trained dental FDI model. The 32-class head is newly initialized
and an optimizer step is exercised on rectangles drawn in memory. No real
dental image or dataset may be supplied, and no weights/artifacts are saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
from pathlib import Path
import tempfile
import time

from lot05_j10l_fdi_training_readiness import (
    AUDIT, FDI_32, FDITrainingBlock,
    audit_dataset_manifest, check_research_only_mode,
)
from lot05_j10j_dfine_coco_actions_smoke import (
    FILES, MODEL_REPO, MODEL_REVISION, MODEL_WEIGHTS_SHA256,
    verify_downloaded_snapshot,
)

REPORT_SCHEMA = "digital-crown-lot05-j10l-synthetic-fdi-training-dry-run-v1"
SYNTHETIC_SEED = 20261022


def make_synthetic_fdi_grid():
    """Return in-memory RGB geometry + 32 corresponding FDI boxes.

    No image is ever persisted to disk or transferred as an artifact.
    Labels are artificial and do not teach radiographic tooth morphology.
    """
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (640, 320), (239, 241, 243))
    pen = ImageDraw.Draw(image)
    rows: list[dict] = []
    for index, fdi in enumerate(FDI_32):
        col = index % 8
        row = index // 8
        left = 9 + col * 80
        top = 9 + row * 80
        width, height = 53, 51
        pen.rectangle(
            (left, top, left + width, top + height),
            outline=(32 + row * 18, 44 + col * 6, 63),
            width=4,
        )
        rows.append(
            {"class_index": index, "fdi": fdi,
             "bbox_cxcywh": [
                 (left + width / 2) / image.width,
                 (top + height / 2) / image.height,
                 width / image.width,
                 height / image.height,
             ]}
        )
    if len(rows) != 32 or len({row["fdi"] for row in rows}) != 32:
        raise FDITrainingBlock("synthetic_fdi_class_count_wrong")
    return image, rows


def validate_synthetic_rows(rows) -> None:
    if not isinstance(rows, list) or len(rows) != 32:
        raise FDITrainingBlock("exactly_32_synthetic_boxes_required")
    if [r.get("fdi") for r in rows] != list(FDI_32):
        raise FDITrainingBlock("synthetic_fdi_permutation_or_duplicate")
    if [r.get("class_index") for r in rows] != list(range(32)):
        raise FDITrainingBlock("synthetic_model_class_mapping_wrong")
    for r in rows:
        box = r.get("bbox_cxcywh")
        if not isinstance(box, list) or len(box) != 4:
            raise FDITrainingBlock("missing_synthetic_bbox")
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in box):
            raise FDITrainingBlock("nonfinite_synthetic_bbox")
        cx, cy, w, h = box
        if not (0 < w <= 1 and 0 < h <= 1 and w/2 <= cx <= 1-w/2 and h/2 <= cy <= 1-h/2):
            raise FDITrainingBlock("out_of_bounds_synthetic_bbox")


def run_synthetic_gradient_step() -> dict:
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoImageProcessor, DFineConfig, DFineForObjectDetection

    # Recheck J10I upstream weights/packaging rights and J10L dataset gate
    # BEFORE any checkpoint is fetched.
    with AUDIT.open("r", encoding="utf-8") as f:
        verdict = audit_dataset_manifest(json.load(f))
    if verdict["status"] != "REAL_DATA_TRAINING_BLOCKED_SYNTHETIC_ONLY":
        raise FDITrainingBlock("unexpected_legal_training_status")
    torch.manual_seed(SYNTHETIC_SEED)
    torch.set_num_threads(min(2, max(1, os.cpu_count() or 1)))
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"

    image, rows = make_synthetic_fdi_grid()
    validate_synthetic_rows(rows)

    with tempfile.TemporaryDirectory(prefix="dc_j10l_coco_foundation_") as tmp:
        snapshot = Path(snapshot_download(
            repo_id=MODEL_REPO,
            revision=MODEL_REVISION,
            allow_patterns=list(FILES),
            local_dir=tmp,
            max_workers=2,
        ))
        integrity = verify_downloaded_snapshot(snapshot)
        config = DFineConfig.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False
        )
        # The class names are the fixed FDI 11..48 adult-permanent set.
        config.id2label = {i: str(fdi) for i, fdi in enumerate(FDI_32)}
        config.label2id = {str(fdi): i for i, fdi in enumerate(FDI_32)}
        if config.num_labels != 32:
            raise FDITrainingBlock("model_classifier_must_have_32_classes")

        # The 80-class COCO head CANNOT be used to infer FDI positions.
        # Any mismatched classification parameters are freshly initialized.
        model = DFineForObjectDetection.from_pretrained(
            str(snapshot),
            config=config,
            ignore_mismatched_sizes=True,
            local_files_only=True,
            trust_remote_code=False,
        ).train().cpu()
        if model.config.num_labels != 32:
            raise FDITrainingBlock("reloaded_head_not_32_classes")
        proc = AutoImageProcessor.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False
        )
        pixel_values = proc(images=image, return_tensors="pt")["pixel_values"]
        targets = [{
            "class_labels": torch.tensor([r["class_index"] for r in rows], dtype=torch.int64),
            "boxes": torch.tensor([r["bbox_cxcywh"] for r in rows], dtype=torch.float32),
        }]
        if tuple(pixel_values.shape) != (1, 3, 640, 640):
            raise FDITrainingBlock("synthetic_input_shape_not_valid")
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.0)

        # Training/gradient path exercised on generated drawings only.
        optimizer.zero_grad(set_to_none=True)
        begin = time.perf_counter()
        outputs = model(pixel_values=pixel_values, labels=targets)
        if outputs.loss is None or not torch.isfinite(outputs.loss).item():
            raise FDITrainingBlock("synthetic_detection_loss_missing_or_nonfinite")
        before = float(outputs.loss.detach().cpu().item())
        outputs.loss.backward()
        nonzero_gradients = sum(
            1 for p in model.parameters()
            if p.grad is not None and torch.isfinite(p.grad).all().item()
            and torch.count_nonzero(p.grad).item() > 0
        )
        if nonzero_gradients < 1:
            raise FDITrainingBlock("no_trainable_parameter_received_gradient")
        train_logits_shape = tuple(outputs.logits.shape)
        if (outputs.logits.ndim != 3 or train_logits_shape[0] != 1
                or train_logits_shape[1] < 1 or train_logits_shape[2] != 32
                or not torch.isfinite(outputs.logits).all().item()):
            raise FDITrainingBlock(
                "synthetic_fdi_head_output_invalid:"
                f" shape={train_logits_shape}"
                f" finite={bool(torch.isfinite(outputs.logits).all().item())}"
            )
        optimizer.step()
        elapsed = round(time.perf_counter() - begin, 4)
        # DO NOT save the model or its gradients.
        del model, optimizer, outputs, targets, image, pixel_values

    return {
        "schema": REPORT_SCHEMA,
        "status": "SYNTHETIC_32_CLASS_TRAINING_PLUMBING_PASS",
        "model_base_repo": MODEL_REPO,
        "model_base_revision": MODEL_REVISION,
        "model_base_sha256": MODEL_WEIGHTS_SHA256,
        "verified_source_model_bytes": integrity["checkpoint_bytes"],
        "target_fdi_label_count": len(FDI_32),
        "train_logits_shape": list(train_logits_shape),
        "synthetic_box_count": len(rows),
        "initialized_fdi_head_from_coco": True,
        "forward_backward_optimizer_steps": 1,
        "loss_before_step": round(before, 6),
        "nonzero_gradient_parameter_tensors": nonzero_gradients,
        "cpu_training_step_seconds": elapsed,
        "system": platform.system(),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "real_dataset_loaded": False,
        "clinical_accuracy_measured": False,
        "weights_trained_on_real_radiographs": False,
        "model_checkpoint_saved": False,
        "cloud_real_image_processing_approved": False,
        "commercial_release_approved": False,
        "clinical_release_approved": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["synthetic_geometry"])
    ap.add_argument("--output-json", required=True, type=Path)
    ap.add_argument("--dataset-path", default="")
    args = ap.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        check_research_only_mode(args.mode, args.dataset_path)
        result = run_synthetic_gradient_step()
    except Exception as exc:
        result = {
            "schema": REPORT_SCHEMA,
            "status": "SYNTHETIC_TRAINING_FAIL_CLOSED",
            "error_type": type(exc).__name__,
            "reason": str(exc)[:350],
            "commercial_release_approved": False,
            "clinical_release_approved": False,
        }
        args.output_json.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, sort_keys=True))
        return 1
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
