from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, random_split

LANDMARKS = ("R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts", "Pm_Ricketts", "DC_Ricketts")
IMAGE_SIZE = 64
MODEL_ID = "RICKETTS_MANDIBLE_SPECIALIST_V1"
NON_CLINICAL_MARKER = "NON_CLINICAL_SMOKE_ONLY"


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class SyntheticMandibleDataset(Dataset):
    """Deterministic synthetic fixture for CI plumbing only; never clinical data."""

    def __init__(self, count: int = 96, seed: int = 20261005) -> None:
        rng = np.random.default_rng(seed)
        self.images = []
        self.targets = []
        yy, xx = np.mgrid[0:IMAGE_SIZE, 0:IMAGE_SIZE]
        for _ in range(count):
            points = []
            image = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.float32)
            for idx in range(len(LANDMARKS)):
                x = float(rng.uniform(8, IMAGE_SIZE - 8))
                y = float(rng.uniform(8, IMAGE_SIZE - 8))
                points.extend((x / (IMAGE_SIZE - 1), y / (IMAGE_SIZE - 1)))
                sigma = 1.4 + 0.15 * idx
                blob = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * sigma**2))
                image += blob.astype(np.float32) * (0.35 + 0.10 * idx)
            image = np.clip(image / max(float(image.max()), 1e-6), 0.0, 1.0)
            image += rng.normal(0.0, 0.01, image.shape).astype(np.float32)
            self.images.append(np.clip(image, 0.0, 1.0)[None, ...])
            self.targets.append(np.asarray(points, dtype=np.float32))
        self.images = np.stack(self.images)
        self.targets = np.stack(self.targets)

    def __len__(self) -> int:
        return int(self.images.shape[0])

    def __getitem__(self, idx: int):
        return torch.from_numpy(self.images[idx]), torch.from_numpy(self.targets[idx])


class TinyMandibleNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 64),
            nn.ReLU(),
            nn.Linear(64, len(LANDMARKS) * 2),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.features(x))


@dataclass
class Metrics:
    model_id: str
    mode: str
    clinical_status: str
    seed: int
    epochs: int
    train_samples: int
    val_samples: int
    initial_train_loss: float
    final_train_loss: float
    val_mae_px: float
    onnx_max_abs_delta: float
    onnx_sha256: str
    landmark_order: list[str]


def validate_real_dataset_contract(dataset_root: Path) -> None:
    manifest = dataset_root / "manifest.json"
    if not manifest.exists():
        raise SystemExit(
            "REAL_DATASET_REQUIRED: mode=real requires a source-locked dataset manifest at "
            f"{manifest}. Clinical training is fail-closed."
        )
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema") != "RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1":
        raise SystemExit("INVALID_REAL_DATASET_SCHEMA")
    if data.get("landmarks") != list(LANDMARKS):
        raise SystemExit("INVALID_REAL_DATASET_LANDMARK_ORDER")
    if data.get("license_verified") is not True:
        raise SystemExit("REAL_DATASET_LICENSE_NOT_VERIFIED")
    if data.get("clinician_annotation_verified") is not True:
        raise SystemExit("REAL_DATASET_CLINICIAN_ANNOTATION_NOT_VERIFIED")
    raise SystemExit(
        "REAL_TRAINING_NOT_ENABLED_YET: dataset contract passed, but this POC intentionally "
        "contains no clinical runtime/training implementation."
    )


def mean_loss(model: nn.Module, loader: DataLoader, loss_fn: nn.Module) -> float:
    model.eval()
    values = []
    with torch.no_grad():
        for images, targets in loader:
            values.append(float(loss_fn(model(images), targets).item()))
    return float(np.mean(values)) if values else math.nan


def validate_mae_px(model: nn.Module, loader: DataLoader) -> float:
    model.eval()
    errors = []
    with torch.no_grad():
        for images, targets in loader:
            pred = model(images)
            errors.append(torch.abs(pred - targets).mean().item() * (IMAGE_SIZE - 1))
    return float(np.mean(errors)) if errors else math.nan


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_smoke(out_dir: Path, epochs: int, seed: int) -> Metrics:
    seed_everything(seed)
    torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))

    dataset = SyntheticMandibleDataset(seed=seed)
    generator = torch.Generator().manual_seed(seed)
    train_set, val_set = random_split(dataset, [72, 24], generator=generator)
    train_loader = DataLoader(train_set, batch_size=12, shuffle=True, generator=generator)
    val_loader = DataLoader(val_set, batch_size=12, shuffle=False)

    model = TinyMandibleNet()
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)

    initial = mean_loss(model, train_loader, loss_fn)
    for _ in range(epochs):
        model.train()
        for images, targets in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(images), targets)
            if not torch.isfinite(loss):
                raise RuntimeError("NON_FINITE_TRAINING_LOSS")
            loss.backward()
            optimizer.step()

    final = mean_loss(model, train_loader, loss_fn)
    if not math.isfinite(initial) or not math.isfinite(final):
        raise RuntimeError("NON_FINITE_SMOKE_METRICS")
    if final >= initial:
        raise RuntimeError(f"SMOKE_TRAINING_DID_NOT_IMPROVE initial={initial} final={final}")

    val_mae = validate_mae_px(model, val_loader)

    out_dir.mkdir(parents=True, exist_ok=True)
    pt_path = out_dir / "ricketts_mandible_specialist_smoke.pt"
    onnx_path = out_dir / "ricketts_mandible_specialist_smoke.onnx"
    torch.save(
        {
            "model_id": MODEL_ID,
            "clinical_status": NON_CLINICAL_MARKER,
            "landmarks": list(LANDMARKS),
            "state_dict": model.state_dict(),
        },
        pt_path,
    )

    sample = torch.zeros(1, 1, IMAGE_SIZE, IMAGE_SIZE, dtype=torch.float32)
    model.eval()
    with torch.no_grad():
        torch.onnx.export(
            model,
            sample,
            onnx_path,
            input_names=["image"],
            output_names=["landmarks_xy_norm"],
            dynamic_axes={"image": {0: "batch"}, "landmarks_xy_norm": {0: "batch"}},
            opset_version=18,
            do_constant_folding=True,
        )
        torch_out = model(sample).numpy()

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    ort_out = session.run(None, {"image": sample.numpy()})[0]
    delta = float(np.max(np.abs(torch_out - ort_out)))
    if delta > 1e-4:
        raise RuntimeError(f"ONNX_PARITY_FAILED max_abs_delta={delta}")

    metrics = Metrics(
        model_id=MODEL_ID,
        mode="smoke",
        clinical_status=NON_CLINICAL_MARKER,
        seed=seed,
        epochs=epochs,
        train_samples=len(train_set),
        val_samples=len(val_set),
        initial_train_loss=initial,
        final_train_loss=final,
        val_mae_px=val_mae,
        onnx_max_abs_delta=delta,
        onnx_sha256=sha256_file(onnx_path),
        landmark_order=list(LANDMARKS),
    )
    (out_dir / "metrics.json").write_text(json.dumps(asdict(metrics), indent=2) + "\n", encoding="utf-8")
    (out_dir / "README.txt").write_text(
        "NON-CLINICAL CI SMOKE ARTIFACT. Synthetic data only. "
        "Must never be loaded by Digital Crown clinical runtime.\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "real"), default="smoke")
    parser.add_argument("--out", default="artifacts/ricketts-mandible-specialist")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--dataset-root", default="")
    args = parser.parse_args()

    if args.mode == "real":
        if not args.dataset_root:
            raise SystemExit("REAL_DATASET_REQUIRED: --dataset-root is mandatory for mode=real")
        validate_real_dataset_contract(Path(args.dataset_root))

    metrics = run_smoke(Path(args.out), epochs=args.epochs, seed=args.seed)
    print(json.dumps(asdict(metrics), sort_keys=True))


if __name__ == "__main__":
    main()
