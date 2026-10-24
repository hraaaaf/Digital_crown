#!/usr/bin/env python3
"""LOT05 / 05.7-J10D: OralGuard 4-class ONNX CPU export, shape and parity proof.

Only artificial synthetic inputs in an ephemeral unprivileged GitHub runner.
Report hashes/shapes/runtime, not model weights, images or patient data.
The candidate remains research-only regardless of PASS.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import time
import traceback

import numpy as np
import onnx
import onnxruntime as ort
import torch
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

MODEL_REPO = "Enosh729/oralguard"
MODEL_REVISION = "06b2a3c390a6caca640e6c6f74f73017e0c5a17b"
SOURCE_SHA256 = "c3303656e72ede3f3d3229e58b2da276448fa204046d3e7a11e13f4d77bc723a"
OUTPUT = Path(os.environ.get("LOT05_ORALGUARD_ONNX_REPORT", "lot05-oralguard-onnx-parity.json"))
RESOLUTION = 1024
report = {
    "mission": "LOT05/05.7-J10D",
    "model": MODEL_REPO,
    "source_commit": MODEL_REVISION,
    "purpose": "Synthetic CPU ONNX export and tensor parity, not clinical evaluation",
    "clinical_acceptance": False,
    "installable_certified": False,
    "commercial_authorization": False,
    "no_patient_data": True,
    "status": "PENDING",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


try:
    root = Path(os.environ.get("GITHUB_WORKSPACE", ".")) / ".lot05-oralguard-onnx"
    root.mkdir(parents=True, exist_ok=True)
    upstream = Path(hf_hub_download(
        repo_id=MODEL_REPO, filename="oralguard_det_best.pt", revision=MODEL_REVISION
    ))
    if sha256(upstream) != SOURCE_SHA256:
        raise RuntimeError("OralGuard source weight SHA256 changed: fail closed")
    local = root / "oralguard-v8m.pt"
    shutil.copyfile(upstream, local)
    model = YOLO(str(local), task="detect")
    values = {int(k): str(v) for k, v in model.names.items()}
    report["classes"] = values
    aliases = {
        "caries", "deepcaries", "periapicallesion", "impactedtooth", "impacted"
    }
    if len(values) != 4 or len({x.lower().replace("_", "").replace(" ", "") for x in values.values()}) != 4:
        raise RuntimeError("Not exactly four distinct OralGuard classes")
    if not all(x.lower().replace("_", "").replace(" ", "") in aliases for x in values.values()):
        raise RuntimeError(f"Unexpected classes in weight: {values}")

    rng = np.random.default_rng(20261021)
    inp = rng.random((1, 3, RESOLUTION, RESOLUTION), dtype=np.float32)
    # Fixed gaussian-like gradient input, no actual X-ray or patient content.
    tensor = torch.from_numpy(inp)
    with torch.inference_mode():
        torch_result = model.model.eval()(tensor)
    if isinstance(torch_result, (tuple, list)):
        torch_result = torch_result[0]
    torch_result = torch_result.detach().cpu().numpy()
    if torch_result.ndim != 3:
        raise RuntimeError(f"Unexpected PyTorch model head {torch_result.shape}")
    report["pytorch_raw_shape"] = list(torch_result.shape)

    exported = Path(model.export(
        format="onnx", imgsz=RESOLUTION, opset=13, dynamic=False,
        simplify=False, device="cpu",
    ))
    onnx.checker.check_model(str(exported))
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    sess = ort.InferenceSession(str(exported), providers=["CPUExecutionProvider"], sess_options=opts)
    input_meta = sess.get_inputs()
    if len(input_meta) != 1 or list(input_meta[0].shape) != [1, 3, RESOLUTION, RESOLUTION]:
        raise RuntimeError(f"Bad exported ONNX input: {[x.shape for x in input_meta]}")
    timings = []
    for _ in range(3):
        began = time.perf_counter()
        output_list = sess.run(None, {input_meta[0].name: inp})
        timings.append(time.perf_counter() - began)
    raw_onnx = np.asarray(output_list[0])
    if raw_onnx.shape != torch_result.shape:
        raise RuntimeError(f"PyTorch/ONNX output shapes differ: {torch_result.shape} vs {raw_onnx.shape}")
    if raw_onnx.shape[1] != 8:
        raise RuntimeError(f"Four-class class-count invalid: output shape {raw_onnx.shape}")
    if not np.isfinite(raw_onnx).all():
        raise RuntimeError("ONNX numerical output not finite")
    difference = np.abs(raw_onnx.astype(np.float64) - torch_result.astype(np.float64))
    metrics = {
        "mean_absolute_error": float(difference.mean()),
        "p99_absolute_error": float(np.percentile(difference, 99)),
        "max_absolute_error": float(difference.max()),
    }
    report.update({
        "source_sha256": sha256(upstream),
        "source_bytes": upstream.stat().st_size,
        "onnx_sha256": sha256(exported),
        "onnx_bytes": exported.stat().st_size,
        "onnx_cpu_providers": sess.get_providers(),
        "onnx_input_shape": list(input_meta[0].shape),
        "onnx_output_shape": list(raw_onnx.shape),
        "latency_median_seconds": round(statistics.median(timings), 4),
        "raw_tensor_parity": metrics,
        "tensor_test": "one seeded synthetic tensor, three ONNX CPU runs",
    })
    # The exported detector must numerically resemble its source; a syntactically
    # valid but unrelated / transposed head must never count as a successful port.
    if metrics["mean_absolute_error"] >= 0.01 or metrics["p99_absolute_error"] >= 0.1:
        raise RuntimeError(f"Export numerical mismatch: {metrics}")
    report["status"] = "PASS_ONNX_CPU_SYNTHETIC"
except Exception as exc:
    report["status"] = "FAILED_TO_VERIFY"
    report["error"] = str(exc)
    report["traceback_tail"] = traceback.format_exc()[-3000:]
finally:
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
if report["status"] != "PASS_ONNX_CPU_SYNTHETIC":
    raise SystemExit(1)
