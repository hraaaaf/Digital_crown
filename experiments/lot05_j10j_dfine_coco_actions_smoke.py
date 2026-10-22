#!/usr/bin/env python3
"""LOT05/J10J — GitHub Actions CPU-only D-FINE Nano COCO baseline verification.

NO FDI model is trained or claimed by this script.
NO panoramic patient image or research dataset is read or downloaded.
Only 3 model files from an immutable Apache-2.0 COCO foundation checkpoint
are fetched into runner temp storage; the full original file SHA256 is checked.
Only a metadata-only JSON report may be uploaded as a CI artifact.
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

MODEL_REPO = "ustc-community/dfine-nano-coco"
MODEL_REVISION = "066438d3d8f0da137a37b38fdf3368fd4afceced"
MODEL_WEIGHTS_SHA256 = "19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b"
FILES = ("model.safetensors", "config.json", "preprocessor_config.json")
REPORT_SCHEMA = "digital-crown-lot05-j10j-foundation-smoke-v1"


class FoundationSmokeError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_downloaded_snapshot(snapshot: Path) -> dict:
    if not snapshot.is_dir():
        raise FoundationSmokeError("missing_pinned_snapshot")
    model = snapshot / FILES[0]
    if not model.is_file():
        raise FoundationSmokeError("missing_pinned_weights")
    digest = sha256(model)
    if digest != MODEL_WEIGHTS_SHA256:
        raise FoundationSmokeError("untrusted_checkpoint_digest")
    for basename in FILES[1:]:
        p = snapshot / basename
        if not p.is_file() or p.is_symlink():
            raise FoundationSmokeError("missing_or_linked_config_" + basename)
    config = json.loads((snapshot / "config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != "d_fine":
        raise FoundationSmokeError("unexpected_model_architecture")
    id2label = config.get("id2label")
    if not isinstance(id2label, dict) or not (70 <= len(id2label) <= 100):
        raise FoundationSmokeError("checkpoint_does_not_have_COC0_class_count")
    return {
        "checkpoint_bytes": model.stat().st_size,
        "checkpoint_sha256": digest,
        "coco_class_count": len(id2label),
    }


def check_tensor_result(logits, pred_boxes, torch) -> dict:
    if logits.ndim != 3 or pred_boxes.ndim != 3 or logits.shape[0] != 1:
        raise FoundationSmokeError("bad_detection_tensor_dimensions")
    if logits.shape[1] <= 0 or pred_boxes.shape[1] != logits.shape[1]:
        raise FoundationSmokeError("bad_query_count")
    if logits.shape[2] <= 32:
        raise FoundationSmokeError("unexpected_fdi_head_in_coco_checkpoint")
    if pred_boxes.shape[2] != 4:
        raise FoundationSmokeError("bad_box_coordinates")
    if not torch.isfinite(logits).all().item() or not torch.isfinite(pred_boxes).all().item():
        raise FoundationSmokeError("nonfinite_detection_logits_or_boxes")
    return {
        "query_count": int(logits.shape[1]),
        "output_class_count": int(logits.shape[2]),
        "all_output_values_finite": True,
    }


def run_smoke() -> dict:
    # PyTorch/Transformers are imported ONLY inside GitHub Actions smoke job.
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from PIL import Image, ImageDraw
    from transformers import AutoImageProcessor, DFineForObjectDetection

    torch.set_num_threads(min(2, max(1, os.cpu_count() or 1)))
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"

    with tempfile.TemporaryDirectory(prefix="dc_j10j_public_coco_") as cache:
        start = time.perf_counter()
        # Allowlist only public NON-medical model metadata/checkpoint.
        snapshot = Path(snapshot_download(
            repo_id=MODEL_REPO,
            revision=MODEL_REVISION,
            allow_patterns=list(FILES),
            local_dir=cache,
            max_workers=2,
        ))
        integrity = verify_downloaded_snapshot(snapshot)
        download_s = round(time.perf_counter() - start, 3)

        # Strictly local-only load from verified bytes (never dynamic remote code).
        processor = AutoImageProcessor.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False
        )
        model = DFineForObjectDetection.from_pretrained(
            str(snapshot),
            local_files_only=True,
            trust_remote_code=False,
        ).eval().cpu()
        if int(model.config.num_labels) != integrity["coco_class_count"]:
            raise FoundationSmokeError("class_map_and_head_mismatch")

        # GENERATED SYNTHETIC GRAPHICS ONLY — NOT an x-ray, not a clinical test.
        image = Image.new("RGB", (192, 128), (231, 233, 235))
        artist = ImageDraw.Draw(image)
        artist.rectangle((17, 22, 60, 102), outline=(44, 49, 53), width=4)
        artist.ellipse((87, 15, 163, 112), fill=(188, 201, 210))
        inputs = processor(images=image, return_tensors="pt")
        if set(inputs) != {"pixel_values"}:
            raise FoundationSmokeError("unexpected_model_inputs")
        if inputs["pixel_values"].shape[0] != 1:
            raise FoundationSmokeError("bad_preprocessor_batch")
        started = time.perf_counter()
        with torch.inference_mode():
            outputs = model(**inputs)
        latency = round(time.perf_counter() - started, 3)
        tensor_result = check_tensor_result(outputs.logits, outputs.pred_boxes, torch)
        detections = processor.post_process_object_detection(
            outputs, target_sizes=torch.tensor([[image.height, image.width]]), threshold=0.50
        )
        if len(detections) != 1 or not all(
            torch.isfinite(detections[0][k]).all().item()
            for k in ("scores", "boxes")
        ):
            raise FoundationSmokeError("nonfinite_synthetic_postprocessing")
        output = {
            "schema": REPORT_SCHEMA,
            "status": "PUBLIC_COCO_FOUNDATION_SYNTHETIC_CPU_PASS",
            "training_performed": False,
            "fdi_detections_validated": False,
            "clinical_approval": False,
            "commercial_release_approval": False,
            "model_license_declared": "Apache-2.0",
            "model_repo": MODEL_REPO,
            "pinned_revision": MODEL_REVISION,
            **integrity,
            **tensor_result,
            "system": platform.system(),
            "processor_input_shape": list(inputs["pixel_values"].shape),
            "synthetic_only": True,
            "postprocessed_synthetic_boxes": len(detections[0]["scores"]),
            "download_seconds": download_s,
            "cpu_forward_seconds": latency,
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
        }
        if output["output_class_count"] == 32:
            raise FoundationSmokeError("wrongly_labelled_as_fdi_model")
        return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run_smoke()
    except Exception as e:
        failure = {"schema": REPORT_SCHEMA, "status": "SMOKE_FAIL_CLOSED",
                   "error_type": type(e).__name__,
                   "error_message": str(e)[:300],
                   "commercial_release_approval": False}
        args.output_json.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, sort_keys=True))
        return 1
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
