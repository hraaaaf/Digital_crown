#!/usr/bin/env python3
"""LOT05/J10K — real CPU ONNX/PyTorch parity of public COCO backbone (not FDI).

Research-only GitHub Actions job, synthetic shapes in memory. Never bundles
public research weights into Digital Crown; never uses dental radiographs.
The independent third-party ONNX graph is checked BYTES vs source SHA before
onnxruntime can open it. Numerical parity is verified against the exact
upstream PyTorch checkpoint already tested in J10J.
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

SOURCE_REPO = "ustc-community/dfine-nano-coco"
SOURCE_REVISION = "066438d3d8f0da137a37b38fdf3368fd4afceced"
SOURCE_WEIGHTS_SHA = "19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b"
ONNX_REPO = "AnnotateIt/dfine-nano-coco-onnx"
ONNX_FILENAME = "model.onnx"
ONNX_SHA = "b0ec2e5793f3a3cbd07440d098645a0e102cd450fb92f4f35e713f36e35d152e"
ONNX_BYTES = 15_434_935
REPORT_SCHEMA = "digital-crown-lot05-j10k-onnx-pytorch-coco-parity-v1"


class ParityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_source_model(root: Path) -> None:
    weights = root / "model.safetensors"
    if not weights.is_file() or sha256(weights) != SOURCE_WEIGHTS_SHA:
        raise ParityError("source_weight_SHA256_mismatch")
    for basename in ("config.json", "preprocessor_config.json"):
        if not (root / basename).is_file():
            raise ParityError("source_config_missing_" + basename)


def verify_onnx(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ParityError("no_valid_onnx_graph")
    if path.stat().st_size != ONNX_BYTES:
        raise ParityError("unexpected_onnx_size")
    if sha256(path) != ONNX_SHA:
        raise ParityError("onnx_SHA256_mismatch")


def compare_tensors(torch_logits, torch_boxes, onnx_logits, onnx_boxes) -> dict:
    import numpy as np

    pairs = (
        ("logits", torch_logits, onnx_logits, (1, 300, 80), 0.08),
        ("pred_boxes", torch_boxes, onnx_boxes, (1, 300, 4), 0.02),
    )
    result = {}
    for name, pyt, ort, shape, max_tolerance in pairs:
        if tuple(pyt.shape) != shape or tuple(ort.shape) != shape:
            raise ParityError(f"{name}_tensor_shape_mismatch")
        if not (np.isfinite(pyt).all() and np.isfinite(ort).all()):
            raise ParityError(f"{name}_nonfinite")
        maximum = float(np.max(np.abs(pyt - ort)))
        mean = float(np.mean(np.abs(pyt - ort)))
        if maximum > max_tolerance:
            raise ParityError(
                f"{name}_parity_delta_exceeds_threshold:"
                f"{maximum:.6f}>{max_tolerance:.6f}"
            )
        result[f"{name}_max_abs_delta"] = round(maximum, 8)
        result[f"{name}_mean_abs_delta"] = round(mean, 8)
        result[f"{name}_shape"] = list(shape)
        result[f"{name}_tolerance"] = max_tolerance

    # Guard against gross label mismatch despite passing generous float
    # thresholds; comparison is only on synthetic COCO outputs, NOT FDI.
    best_pytorch = np.argmax(torch_logits, axis=-1)
    best_onnx = np.argmax(onnx_logits, axis=-1)
    same = int((best_pytorch == best_onnx).sum())
    result["same_argmax_class_queries"] = same
    if same < 285:  # at least 95% of queries
        raise ParityError(f"coco_class_argmax_mismatch:{same}/300")
    return result


def run() -> dict:
    import numpy as np
    import torch
    from PIL import Image, ImageDraw
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    from transformers import AutoImageProcessor, DFineForObjectDetection
    import onnx
    import onnxruntime as ort

    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    torch.set_num_threads(min(2, max(1, os.cpu_count() or 1)))

    with tempfile.TemporaryDirectory(prefix="dc_j10k_public_models_") as tmp:
        root = Path(tmp)
        # ONNX is a third-party conversion; record the exact resolved commit
        # AND enforce the independent expected SHA256 before loading it.
        info = HfApi().model_info(ONNX_REPO)
        if not isinstance(info.sha, str) or len(info.sha) != 40:
            raise ParityError("cannot_resolve_onnx_repository_commit")
        onnx_commit = info.sha
        f = Path(hf_hub_download(
            repo_id=ONNX_REPO,
            revision=onnx_commit,
            filename=ONNX_FILENAME,
            local_dir=root / "onnx",
        ))
        verify_onnx(f)

        source = Path(snapshot_download(
            repo_id=SOURCE_REPO,
            revision=SOURCE_REVISION,
            allow_patterns=["model.safetensors", "config.json", "preprocessor_config.json"],
            local_dir=root / "torch",
            max_workers=2,
        ))
        verify_source_model(source)

        model = DFineForObjectDetection.from_pretrained(
            str(source), trust_remote_code=False, local_files_only=True
        ).cpu().eval()
        processor = AutoImageProcessor.from_pretrained(
            str(source), trust_remote_code=False, local_files_only=True
        )
        synthetic = Image.new("RGB", (192, 128), (231, 233, 235))
        brush = ImageDraw.Draw(synthetic)
        brush.rectangle((17, 22, 60, 102), outline=(44, 49, 53), width=4)
        brush.ellipse((87, 15, 163, 112), fill=(188, 201, 210))
        inputs = processor(images=synthetic, return_tensors="pt")
        pixel = inputs["pixel_values"]
        if tuple(pixel.shape) != (1, 3, 640, 640):
            raise ParityError("wrong_pytorch_input_size")

        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(f), sess_options=options,
                                       providers=["CPUExecutionProvider"])
        if [x.name for x in session.get_inputs()] != ["pixel_values"]:
            raise ParityError("unknown_onnx_input")
        names = [x.name for x in session.get_outputs()]
        if set(names) != {"logits", "pred_boxes"}:
            raise ParityError("unknown_onnx_outputs")
        onnx.checker.check_model(str(f))

        start = time.perf_counter()
        with torch.inference_mode():
            ref = model(pixel_values=pixel)
        torch_seconds = round(time.perf_counter() - start, 4)

        start = time.perf_counter()
        ort_raw = session.run(None, {"pixel_values": pixel.numpy()})
        ort_seconds = round(time.perf_counter() - start, 4)
        named = dict(zip(names, ort_raw))
        differences = compare_tensors(
            ref.logits.detach().numpy(),
            ref.pred_boxes.detach().numpy(),
            named["logits"],
            named["pred_boxes"],
        )

        return {
            "schema": REPORT_SCHEMA,
            "status": "PINNED_COCO_ONNX_CPU_PARITY_PASS",
            "synthetic_only": True,
            "system": platform.system(),
            "onnx_source": ONNX_REPO,
            "onnx_resolved_commit": onnx_commit,
            "onnx_sha256": ONNX_SHA,
            "pytorch_source": SOURCE_REPO,
            "pytorch_revision": SOURCE_REVISION,
            "pytorch_weight_sha256": SOURCE_WEIGHTS_SHA,
            "torch_version": torch.__version__,
            "onnxruntime_version": ort.__version__,
            "cpu_torch_seconds": torch_seconds,
            "cpu_onnx_seconds": ort_seconds,
            "fdi_class_training_performed": False,
            "fdi_accuracy_validated": False,
            "commercial_release_approved": False,
            "clinical_use_approved": False,
            **differences,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = run()
    except Exception as e:
        report = {"schema": REPORT_SCHEMA, "status": "PARITY_FAIL_CLOSED",
                  "reason": f"{type(e).__name__}: {str(e)[:240]}",
                  "commercial_release_approved": False,
                  "clinical_use_approved": False}
        args.output_json.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
        return 1
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
