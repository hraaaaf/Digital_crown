#!/usr/bin/env python3
"""Research-only panoramic ONNX/CPU compatibility probe on pinned public GitHub weights.

No patient data, no production integration, no scientific/clinical acceptance.
Download untrusted checkpoint in isolated GitHub Actions with no credentials
persisted; never run on the cabinet or commit model bytes to this repository.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import traceback
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import onnxruntime as ort

WORKDIR = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve() / ".lot05-panoramic-probe"
WORKDIR.mkdir(parents=True, exist_ok=True)
REPORT = {
    "mission": "LOT05/05.7-J10D",
    "evidence": "RESEARCH-SMOKE-ONLY-NOT-CLINICAL",
    "source_repo_original": "NoahOksuz/DentalXrayAI",
    "source_commit_original": "a44a456cb76071f1776a7636204e8c48748a696d",
    "source_repo_tooth_only": "zephinax/dental-cnn-segmentation",
    "source_commit_tooth_only": "50b891d10d87325bcb7b6dc62e0e6b6c59472105",
    "source_declared_license_original": "Apache-2.0",
    "source_declared_license_tooth_only": "NO-LICENSE-FOUND",
    "source_reported_periapical_ap50": 0.13,
    "source_reported_map50": 0.458,
    "clinical_acceptance": False,
    "installable_certified": False,
    "machine": "ephemeral GitHub Actions linux runner, synthetic input",
    "models": {},
}
NAMES = ["Caries", "Deep Caries", "Impacted", "Periapical Lesion"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for data in iter(lambda: reader.read(4 * 1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def fetch(source_repo: str, commit: str, file_path: str, local_name: str, max_bytes: int) -> Path:
    target = WORKDIR / local_name
    url = f"https://raw.githubusercontent.com/{source_repo}/{commit}/{file_path}"
    request = Request(url, headers={"User-Agent": "DigitalCrown-LOT05-scientific-probe"})
    with urlopen(request, timeout=90) as response, target.open("wb") as dest:
        total = 0
        while data := response.read(1024 * 1024):
            total += len(data)
            if total > max_bytes:
                raise ValueError(f"Model exceeds research-only transfer limit: {local_name}")
            dest.write(data)
    if total < 1_000_000:
        raise ValueError(f"Model too small to be expected weights: {local_name}")
    return target


def onnx_cpu_smoke(model_path: Path, label: str, requested_resolution: int = 640) -> dict:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])
    input_info = session.get_inputs()[0]
    dims = [v if isinstance(v, int) and v > 0 else requested_resolution for v in input_info.shape]
    if len(dims) != 4 or dims[0] != 1 or dims[1] != 3:
        raise ValueError(f"Unexpected ONNX input tensor: {input_info.shape}")
    if dims[2] > 1280 or dims[3] > 1280:
        raise ValueError("Model unexpectedly requires very large input")
    inp = np.zeros(dims, dtype=np.float32)
    inp[:, :, dims[2] // 3:dims[2] // 2, dims[3] // 4:dims[3] * 3 // 4] = 0.5
    started = time.perf_counter()
    outputs = session.run(None, {input_info.name: inp})
    elapsed = time.perf_counter() - started
    if not outputs or not all(np.isfinite(np.asarray(x)).all() for x in outputs):
        raise ValueError("No ONNX output or non-finite inference values")
    result = {
        "source": label,
        "onnx_sha256": sha(model_path),
        "onnx_bytes": model_path.stat().st_size,
        "inputs": [{"name": x.name, "shape": list(x.shape), "dtype": x.type} for x in session.get_inputs()],
        "outputs": [{"name": y.name, "shape": list(y.shape), "dtype": y.type} for y in session.get_outputs()],
        "runtime_output_shapes": [list(np.asarray(x).shape) for x in outputs],
        "cpu_seconds_single_synthetic": round(elapsed, 3),
        "all_outputs_finite": True,
        "output_is_clinical_detection": False,
    }
    return result


try:
    noah = fetch(
        "NoahOksuz/DentalXrayAI",
        REPORT["source_commit_original"],
        "best.pt",
        "noah_dentex_4class.pt",
        25_000_000,
    )
    REPORT["models"]["noah_source"] = {
        "source_weight_sha256": sha(noah),
        "source_weight_bytes": noah.stat().st_size,
        "weights_untrusted_pickle": True,
    }
    # Ultralytics checkpoints are pickle-bearing: this step must only run on
    # isolated, unprivileged ephemeral CI with no token persistence or secrets.
    from ultralytics import YOLO
    yolo = YOLO(str(noah), task="detect")
    observed = [yolo.names[i] for i in sorted(yolo.names)]
    REPORT["models"]["noah_source"]["class_names"] = observed
    if observed != NAMES:
        raise ValueError(f"Class-order mismatch: {observed} != {NAMES}")
    exported = Path(yolo.export(format="onnx", imgsz=1280, dynamic=False, simplify=False, opset=13, device="cpu"))
    test = onnx_cpu_smoke(exported, "Noah Dentex-4-class", 1280)
    shape = test["runtime_output_shapes"][0]
    if len(shape) != 3 or shape[0] != 1 or shape[1] != 4 + len(NAMES):
        raise ValueError(f"Unexpected 4-class YOLO output shape: {shape}")
    REPORT["models"]["noah_source"].update(test)
    REPORT["models"]["noah_source"]["structural_compatibility_sota_panoramic"] = True
    REPORT["models"]["noah_source"]["direct_drop_in_panorama_service"] = False
    REPORT["models"]["noah_source"]["blocker"] = (
        "Periapical AP50 0.13 on 10 examples, no independent validation; "
        "second panoramic_service class order differs; FDI coordinate heuristic is not clinical numbering."
    )

    zeph = fetch(
        "zephinax/dental-cnn-segmentation",
        REPORT["source_commit_tooth_only"],
        "workspace/detectors/pano-yolo-merged-cpu/weights/best.onnx",
        "zeph_tooth_only.onnx",
        25_000_000,
    )
    REPORT["models"]["zeph_tooth_only"] = onnx_cpu_smoke(zeph, "zephinax tooth segmentation ONNX", 640)
    REPORT["models"]["zeph_tooth_only"]["semantic_compatibility"] = False
    REPORT["models"]["zeph_tooth_only"]["blocker"] = (
        "Tooth segmentation/numbering is not pathology detection; no repository LICENSE; "
        "reported high mAP cannot be compared with DENTEX pathology results."
    )
    REPORT["probe_success"] = True
except Exception as error:
    REPORT["probe_success"] = False
    REPORT["error"] = str(error)
    REPORT["traceback_tail"] = traceback.format_exc()[-3500:]
finally:
    Path(os.environ.get("LOT05_PANORAMIC_REPORT", "lot05-panoramic-probe.json")).write_text(
        json.dumps(REPORT, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("LOT05_PANORAMIC_PROBE=" + ("PASS" if REPORT["probe_success"] else "FAIL"))
    print(json.dumps(REPORT, indent=2, sort_keys=True))
if not REPORT["probe_success"]:
    raise SystemExit(1)
