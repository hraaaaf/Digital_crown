#!/usr/bin/env python3
"""P6 scientific asset portability benchmark.

Research-only harness. Downloads public candidate weights, pins provenance,
computes SHA256, exports ONNX, and measures ONNX Runtime CPU behavior.
It does not modify Digital Crown clinical runtime wiring.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import gdown
import numpy as np
import onnx
import onnxruntime as ort
import torch
from ultralytics import YOLO

CEPH_REPO = "https://github.com/szuboy/CL-Detection2023.git"
CEPH_REPO_SHA = "dc1ce2bd0a3f317de4160cde17e4a6f60371e67c"
CEPH_GDRIVE_ID = "1Qvnym4oGSG903ti0z2HE6Dm1udNO692G"
ORALGUARD_REPO = "https://github.com/DrEnosh/Oral_guard.git"
ORALGUARD_REPO_SHA = "f619ae5078da80b1fc84fb34324d2100c2382e82"
ORALGUARD_HF_REPO = "Enosh729/oralguard"
ORALGUARD_WEIGHT = "oralguard_det_best.pt"
PANO_CLASS_TO_DIGITAL_CROWN = {
    "caries": "Caries",
    "deep caries": "Deep Caries",
    "impacted tooth": "Impacted",
    "periapical lesion": "Periapical Lesion",
}
EXPECTED_PANO_CLASSES = set(PANO_CLASS_TO_DIGITAL_CROWN)
RESULT_DIR = Path(os.environ.get("P6_BENCHMARK_DIR", "artifacts/p6-scientific-assets-benchmark"))
WORK_DIR = RESULT_DIR / "work"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 3)


def cpu_name() -> str:
    if Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text(errors="ignore").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def download_url(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "DigitalCrown-P6-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def hf_revision(repo_id: str) -> str:
    url = f"https://huggingface.co/api/models/{repo_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "DigitalCrown-P6-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    rev = payload.get("sha")
    if not isinstance(rev, str) or len(rev) < 12:
        raise RuntimeError(f"Hugging Face revision unavailable for {repo_id}")
    return rev


def clone_pinned(url: str, sha: str, dest: Path) -> None:
    subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", url, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", sha], check=True)
    actual = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if actual != sha:
        raise RuntimeError(f"Git pin mismatch: expected {sha}, got {actual}")


def benchmark_ort(path: Path, input_shape: list[int], iterations: int = 10, warmups: int = 3) -> dict[str, Any]:
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    t0 = time.perf_counter()
    session = ort.InferenceSession(str(path), sess_options=opts, providers=["CPUExecutionProvider"])
    cold_load_ms = (time.perf_counter() - t0) * 1000.0

    if session.get_providers() != ["CPUExecutionProvider"]:
        raise RuntimeError(f"Unexpected ORT providers: {session.get_providers()}")

    input_meta = session.get_inputs()[0]
    x = np.random.default_rng(20260825).random(input_shape, dtype=np.float32)

    for _ in range(warmups):
        session.run(None, {input_meta.name: x})

    times_ms = []
    outputs = None
    for _ in range(iterations):
        t = time.perf_counter()
        outputs = session.run(None, {input_meta.name: x})
        times_ms.append((time.perf_counter() - t) * 1000.0)

    return {
        "provider": session.get_providers(),
        "cold_load_ms": round(cold_load_ms, 2),
        "inference_ms": {
            "iterations": iterations,
            "mean": round(statistics.fmean(times_ms), 2),
            "median": round(statistics.median(times_ms), 2),
            "min": round(min(times_ms), 2),
            "max": round(max(times_ms), 2),
        },
        "input": {
            "name": input_meta.name,
            "shape": input_meta.shape,
            "type": input_meta.type,
        },
        "outputs": [
            {"name": meta.name, "shape": meta.shape, "type": meta.type}
            for meta in session.get_outputs()
        ],
        "runtime_output_shapes": [list(np.asarray(out).shape) for out in (outputs or [])],
    }


def load_cl_model(repo: Path, weight: Path) -> torch.nn.Module:
    module_path = repo / "utils" / "model.py"
    spec = importlib.util.spec_from_file_location("cl_detection_model", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import CL-Detection model architecture")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.load_model("UNet")

    state = torch.load(weight, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise RuntimeError(f"Unexpected CL checkpoint type: {type(state)!r}")
    model.load_state_dict(state, strict=True)
    model.eval()

    final_weight = state.get("out_tr.final_conv.weight")
    if final_weight is None or tuple(final_weight.shape[:1]) != (38,):
        raise RuntimeError(
            "CL checkpoint does not prove the expected 38-channel final layer"
        )
    return model


def onnx_opsets(path: Path) -> list[dict[str, Any]]:
    model = onnx.load(str(path))
    onnx.checker.check_model(model)
    return [
        {"domain": imp.domain or "ai.onnx", "version": int(imp.version)}
        for imp in model.opset_import
    ]


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "status": "research_only",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "machine": {
            "os": platform.platform(),
            "cpu": cpu_name(),
            "logical_cpu_count": os.cpu_count(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
        },
        "sources": {
            "cl_detection": {
                "repo": CEPH_REPO,
                "repo_commit": CEPH_REPO_SHA,
                "gdrive_id": CEPH_GDRIVE_ID,
            },
            "oralguard": {
                "repo": ORALGUARD_REPO,
                "repo_commit": ORALGUARD_REPO_SHA,
                "hf_repo": ORALGUARD_HF_REPO,
            },
        },
    }

    # CL-Detection2023: exact official artifact + SHA + 38-channel contract + ONNX CPU proxy.
    cl_repo = WORK_DIR / "CL-Detection2023"
    clone_pinned(CEPH_REPO, CEPH_REPO_SHA, cl_repo)
    cl_pt = WORK_DIR / "cl_detection_best_model.pt"
    downloaded = gdown.download(id=CEPH_GDRIVE_ID, output=str(cl_pt), quiet=False)
    if not downloaded or not cl_pt.exists() or cl_pt.stat().st_size == 0:
        raise RuntimeError("CL-Detection2023 official Google Drive weight download failed")

    cl_model = load_cl_model(cl_repo, cl_pt)
    cl_onnx = WORK_DIR / "cl_detection_38_landmarks.onnx"
    dummy_cl = torch.zeros((1, 3, 512, 512), dtype=torch.float32)
    torch.onnx.export(
        cl_model,
        dummy_cl,
        str(cl_onnx),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["heatmaps"],
        dynamic_axes=None,
    )
    cl_bench = benchmark_ort(cl_onnx, [1, 3, 512, 512])
    if cl_bench["runtime_output_shapes"] != [[1, 38, 512, 512]]:
        raise RuntimeError(
            f"CL ONNX output contract mismatch: {cl_bench['runtime_output_shapes']}"
        )
    report["cl_detection"] = {
        "pt": {"size_mb": size_mb(cl_pt), "sha256": sha256(cl_pt)},
        "onnx": {
            "size_mb": size_mb(cl_onnx),
            "sha256": sha256(cl_onnx),
            "opsets": onnx_opsets(cl_onnx),
        },
        "contract": {"input": [1, 3, 512, 512], "output": [1, 38, 512, 512]},
        "cpu": cl_bench,
    }

    # OralGuard: pin HF revision first, then detector-only PT -> ONNX.
    oral_repo = WORK_DIR / "Oral_guard"
    clone_pinned(ORALGUARD_REPO, ORALGUARD_REPO_SHA, oral_repo)
    oral_hf_sha = hf_revision(ORALGUARD_HF_REPO)
    oral_pt = WORK_DIR / ORALGUARD_WEIGHT
    download_url(
        f"https://huggingface.co/{ORALGUARD_HF_REPO}/resolve/{oral_hf_sha}/{ORALGUARD_WEIGHT}",
        oral_pt,
    )
    if not oral_pt.exists() or oral_pt.stat().st_size == 0:
        raise RuntimeError("OralGuard detector weight download failed")

    yolo = YOLO(str(oral_pt))
    names_obj = yolo.names
    if isinstance(names_obj, dict):
        names = [str(names_obj[i]) for i in sorted(names_obj)]
    else:
        names = [str(x) for x in names_obj]
    normalized = {name.strip().lower() for name in names}
    if normalized != EXPECTED_PANO_CLASSES:
        raise RuntimeError(
            f"OralGuard classes do not exactly match Digital Crown contract: {names}"
        )

    exported = yolo.export(
        format="onnx",
        imgsz=1024,
        opset=17,
        simplify=False,
        dynamic=False,
        device="cpu",
        batch=1,
        verbose=False,
    )
    oral_onnx = Path(str(exported))
    if not oral_onnx.is_absolute():
        oral_onnx = Path.cwd() / oral_onnx
    if not oral_onnx.exists():
        fallback = oral_pt.with_suffix(".onnx")
        if fallback.exists():
            oral_onnx = fallback
        else:
            raise RuntimeError(f"Ultralytics export path missing: {exported}")

    oral_bench = benchmark_ort(oral_onnx, [1, 3, 1024, 1024], iterations=8, warmups=2)
    if oral_bench["input"]["shape"] != [1, 3, 1024, 1024]:
        raise RuntimeError(f"OralGuard ONNX input contract mismatch: {oral_bench['input']['shape']}")
    oral_shapes = oral_bench["runtime_output_shapes"]
    if not any(len(shape) == 3 and 8 in (shape[1], shape[2]) for shape in oral_shapes):
        raise RuntimeError(
            f"OralGuard ONNX raw output does not expose 4 box + 4 class channels: {oral_shapes}"
        )
    report["oralguard"] = {
        "hf_revision": oral_hf_sha,
        "classes": names,
        "class_index_map": {str(i): name for i, name in enumerate(names)},
        "digital_crown_label_map": {
            name: PANO_CLASS_TO_DIGITAL_CROWN[name.strip().lower()]
            for name in names
        },
        "pt": {"size_mb": size_mb(oral_pt), "sha256": sha256(oral_pt)},
        "onnx": {
            "size_mb": size_mb(oral_onnx),
            "sha256": sha256(oral_onnx),
            "opsets": onnx_opsets(oral_onnx),
        },
        "contract": {
            "input": [1, 3, 1024, 1024],
            "expected_classes": sorted(EXPECTED_PANO_CLASSES),
        },
        "cpu": oral_bench,
    }

    report["machine"]["max_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
    report["result"] = "PASS"

    json_path = RESULT_DIR / "benchmark.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# P6 Scientific Assets Benchmark",
        "",
        "Research-only. No Digital Crown clinical runtime wiring changed.",
        "",
        f"- Result: **{report['result']}**",
        f"- Machine: `{report['machine']['cpu']}` / `{report['machine']['os']}`",
        f"- CL PT SHA256: `{report['cl_detection']['pt']['sha256']}`",
        f"- CL ONNX: {report['cl_detection']['onnx']['size_mb']} MB / "
        f"{report['cl_detection']['cpu']['inference_ms']['median']} ms median CPU",
        f"- OralGuard HF revision: `{report['oralguard']['hf_revision']}`",
        f"- OralGuard PT SHA256: `{report['oralguard']['pt']['sha256']}`",
        f"- OralGuard ONNX: {report['oralguard']['onnx']['size_mb']} MB / "
        f"{report['oralguard']['cpu']['inference_ms']['median']} ms median CPU",
        f"- OralGuard classes: `{', '.join(report['oralguard']['classes'])}`",
        "",
        "Full tensor contracts, opsets, runtimes and hashes are in `benchmark.json`.",
        "",
    ]
    (RESULT_DIR / "benchmark.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {
            "result": "FAIL",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "exception": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        (RESULT_DIR / "failure.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, indent=2, sort_keys=True), file=sys.stderr)
        raise
