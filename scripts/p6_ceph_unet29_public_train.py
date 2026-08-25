#!/usr/bin/env python3
"""Public ephemeral full-training runner for DC-Ceph-UNet29Q4 on Aariz v1.

Research-only. Trains from the exact public P6 research contract, selects on validation,
keeps the Aariz test split sealed until the frozen validation checkpoint passes the
pre-test gate, and emits a candidate only for benchmark/transfer purposes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
import torch

SEED = 20260825
AARIZ_SHA256 = "d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea"
AARIZ_DOI = "10.6084/m9.figshare.27986417.v1"
OFFICIAL_REFERENCE = {"mre_mm": 1.789, "sdr_2mm_percent": 78.44, "sdr_4mm_percent": 94.44}
PRETEST_GATE = {"max_mre_mm": 2.5, "min_sdr_2mm_percent": 60.0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_rng(epoch: int, image_id: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{SEED}:{epoch}:{image_id}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def intensity_augment(image: torch.Tensor, epoch: int, image_id: str) -> torch.Tensor:
    rng = stable_rng(epoch, image_id)
    brightness = float(rng.uniform(0.90, 1.10))
    contrast = float(rng.uniform(0.90, 1.10))
    mean = image.mean()
    augmented = (image - mean) * contrast + mean
    return (augmented * brightness).clamp(0.0, 1.0)


def find_dataset_root(extracted: Path) -> Path:
    matches = list(extracted.rglob("cephalogram_machine_mappings.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one Aariz root, found {len(matches)}")
    root = matches[0].parent
    for split in ("train", "valid", "test"):
        if not (root / split / "Cephalograms").is_dir():
            raise RuntimeError(f"invalid Aariz root: missing {split}/Cephalograms")
    return root


def batch_from_indices(dataset: Any, indices: list[int], epoch: int, augment: bool) -> tuple[torch.Tensor, torch.Tensor]:
    samples = [dataset[index] for index in indices]
    images = [intensity_augment(sample["image"], epoch, str(sample["image_id"])) if augment else sample["image"] for sample in samples]
    return torch.stack(images), torch.stack([sample["coords"] for sample in samples])


def evaluate(model: Any, dataset: Any, q4: Any, data_mod: Any) -> dict[str, Any]:
    model.eval()
    rows: list[np.ndarray] = []
    with torch.no_grad():
        for index in range(len(dataset)):
            sample = dataset[index]
            logits = model(sample["image"].unsqueeze(0))
            prediction = q4.decode_heatmaps_q4(logits)[0].cpu().numpy()
            transform = data_mod.LetterboxTransform(**sample["transform"])
            rows.append(q4.errors_mm_for_sample(prediction, sample["coords_original"].cpu().numpy(), transform, float(sample["pixel_size_mm"])))
    return q4.summarize_errors_mm(np.stack(rows, axis=0))


def export_and_benchmark(model: Any, path: Path, q4: Any) -> dict[str, Any]:
    model.eval()
    dummy = torch.zeros((1, 1, q4.INPUT_SIZE, q4.INPUT_SIZE), dtype=torch.float32)
    torch.onnx.export(model, dummy, str(path), opset_version=17, input_names=["image"], output_names=["heatmaps"], dynamic_axes=None)
    checked = onnx.load(str(path))
    onnx.checker.check_model(checked)
    started = time.perf_counter()
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    cold_ms = (time.perf_counter() - started) * 1000.0
    tensor = np.zeros((1, 1, q4.INPUT_SIZE, q4.INPUT_SIZE), dtype=np.float32)
    for _ in range(2):
        session.run(None, {session.get_inputs()[0].name: tensor})
    timings: list[float] = []
    output = None
    for _ in range(8):
        started = time.perf_counter()
        output = session.run(None, {session.get_inputs()[0].name: tensor})[0]
        timings.append((time.perf_counter() - started) * 1000.0)
    expected = (1, 29, q4.HEATMAP_SIZE, q4.HEATMAP_SIZE)
    if output is None or tuple(output.shape) != expected:
        raise RuntimeError("ONNX output mismatch")
    return {
        "opset": 17,
        "input_shape": [1, 1, q4.INPUT_SIZE, q4.INPUT_SIZE],
        "output_shape": list(expected),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "cold_load_ms": round(cold_ms, 2),
        "cpu_inference_ms": {
            "iterations": len(timings),
            "median": round(statistics.median(timings), 2),
            "mean": round(statistics.fmean(timings), 2),
            "min": round(min(timings), 2),
            "max": round(max(timings), 2),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--extracted-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    from scripts import p6_ceph_aariz_data as data_mod
    from scripts import p6_ceph_train_contract as q4
    from scripts.p6_aariz_objective_qualification import localization_objective

    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.use_deterministic_algorithms(True)

    root = find_dataset_root(args.extracted_dir)
    train = data_mod.Aariz29GeometryDataset(root, "train", image_size=q4.INPUT_SIZE, ground_truth_policy="official_v1_ceil")
    valid = data_mod.Aariz29GeometryDataset(root, "valid", image_size=q4.INPUT_SIZE, ground_truth_policy="official_v1_ceil")

    model = q4.DCCephUNet29Q4(base_channels=16)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2, threshold=0.002, threshold_mode="abs", min_lr=1e-5)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_path = args.output_dir / "model_state.pt"
    history: list[dict[str, Any]] = []
    best_mre = float("inf")
    best_epoch = -1
    best_valid: dict[str, Any] | None = None
    stale_epochs = 0
    started = time.perf_counter()

    for epoch in range(args.max_epochs):
        model.train()
        order = torch.randperm(len(train), generator=torch.Generator().manual_seed(SEED + epoch)).tolist()
        losses: list[float] = []
        for start in range(0, len(order), args.batch_size):
            indices = order[start:start + args.batch_size]
            images, coords = batch_from_indices(train, indices, epoch, augment=True)
            target = q4.batch_gaussian_heatmaps(coords, sigma_heatmap_px=2.0)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss, _ = localization_objective(logits, target, coords)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss at epoch {epoch + 1}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            losses.append(float(loss.detach()))

        valid_metrics = evaluate(model, valid, q4, data_mod)
        valid_mre = float(valid_metrics["all29"]["mre_mm"])
        scheduler.step(valid_mre)
        record = {
            "epoch": epoch + 1,
            "train_objective_mean": round(statistics.fmean(losses), 7),
            "valid_all29_mre_mm": valid_mre,
            "valid_all29_sdr2_percent": valid_metrics["all29"]["sdr_percent"]["2.0"],
            "valid_dc20_mre_mm": valid_metrics["dc20"]["mre_mm"],
            "lr": float(optimizer.param_groups[0]["lr"]),
        }
        history.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
        if valid_mre < best_mre - 0.005:
            best_mre = valid_mre
            best_epoch = epoch + 1
            best_valid = valid_metrics
            torch.save(model.state_dict(), best_path)
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= args.patience:
            break

    if best_valid is None or not best_path.exists():
        raise RuntimeError("no valid checkpoint selected")
    model.load_state_dict(torch.load(best_path, map_location="cpu", weights_only=True), strict=True)
    model.eval()
    state_sha = sha256(best_path)

    val_mre = float(best_valid["all29"]["mre_mm"])
    val_sdr2 = float(best_valid["all29"]["sdr_percent"]["2.0"])
    pretest_pass = val_mre <= PRETEST_GATE["max_mre_mm"] and val_sdr2 >= PRETEST_GATE["min_sdr_2mm_percent"]
    test_metrics: dict[str, Any] | None = None
    if pretest_pass:
        test = data_mod.Aariz29GeometryDataset(root, "test", image_size=q4.INPUT_SIZE, ground_truth_policy="official_v1_ceil")
        test_metrics = evaluate(model, test, q4, data_mod)

    reference_pass = False
    if test_metrics is not None:
        test_all29 = test_metrics["all29"]
        reference_pass = (
            float(test_all29["mre_mm"]) <= OFFICIAL_REFERENCE["mre_mm"]
            and float(test_all29["sdr_percent"]["2.0"]) >= OFFICIAL_REFERENCE["sdr_2mm_percent"]
            and float(test_all29["sdr_percent"]["4.0"]) >= OFFICIAL_REFERENCE["sdr_4mm_percent"]
        )

    status = "VALIDATION_BELOW_PRETEST_GATE_TEST_NOT_TOUCHED"
    if pretest_pass:
        status = "PUBLIC_REFERENCE_PASS_NOT_CLINICAL" if reference_pass else "PUBLIC_REFERENCE_NOT_BEATEN"

    onnx_report = None
    onnx_path = args.output_dir / "model.onnx"
    if reference_pass:
        onnx_report = export_and_benchmark(model, onnx_path, q4)

    report = {
        "result": "PASS" if reference_pass else "CANDIDATE_NOT_PUBLISHED",
        "status": status,
        "clinical_claim": False,
        "source_head": args.source_head,
        "dataset": {"name": "Aariz v1", "doi": AARIZ_DOI, "sha256": AARIZ_SHA256, "license": "CC BY 4.0"},
        "config": {"model": "DC-Ceph-UNet29Q4", "parameters": parameter_count, "batch_size": args.batch_size, "max_epochs": args.max_epochs, "patience": args.patience, "seed": SEED},
        "selection": {"best_epoch": best_epoch, "best_validation": best_valid, "pretest_gate": PRETEST_GATE, "pretest_pass": pretest_pass, "test_loaded_once": test_metrics is not None},
        "test": test_metrics,
        "official_reference": OFFICIAL_REFERENCE,
        "beats_official_reference": reference_pass,
        "history": history,
        "artifacts": {"state_sha256": state_sha, "onnx": onnx_report},
        "runtime": {"elapsed_s": round(time.perf_counter() - started, 2), "threads": threads, "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2), "machine": platform.platform(), "python": platform.python_version(), "torch": torch.__version__, "onnxruntime": ort.__version__},
    }
    (args.output_dir / "training_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if not reference_pass:
        best_path.unlink(missing_ok=True)
    print(json.dumps({"status": status, "best_epoch": best_epoch, "reference_pass": reference_pass}, sort_keys=True))


if __name__ == "__main__":
    main()
