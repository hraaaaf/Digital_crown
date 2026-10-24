#!/usr/bin/env python3
"""LOT05 / 05.7-J10D: FDI tooth-numbering candidate research, never pathology diagnosis.

Synthetic-only GitHub Actions proof. Checkpoint is downloaded at immutable hub
commit; no patient files, no model binary in artifacts or in Digital Crown.
An ONNX/Windows/cabinet gate is a SEPARATE, later decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MODEL_REPO = "miquic/app-odonto-fdi-yolov8s"
MODEL_REVISION = "82b4d9a02f9e6f32a746dc17afe681e20e8b99e2"
MODEL_WEIGHTS_FILE = "best.pt"
MODEL_WEIGHTS_SHA256 = "533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6"
CLASS_ORDER = tuple(str(10 * q + i) for q in (1, 2, 3, 4) for i in range(1, 9))


class FDIProbeError(ValueError):
    pass


def verify_names(names: dict) -> tuple[str, ...]:
    """Do not infer tooth numbers from x/y or replace a missing tooth with a shifted ID."""
    if not isinstance(names, dict) or len(names) != 32:
        raise FDIProbeError("expected_exactly_32_fdi_classes")
    try:
        indexed = {int(i): str(name).strip() for i, name in names.items()}
    except (ValueError, TypeError) as exc:
        raise FDIProbeError("invalid_checkpoint_class_keys") from exc
    if set(indexed) != set(range(32)):
        raise FDIProbeError("unexpected_checkpoint_indices")
    observed = tuple(indexed[i] for i in range(32))
    if observed != CLASS_ORDER:
        raise FDIProbeError("fdi_label_order_mismatch")
    return observed


def validate_detections(labels, bounds, confidence, image_shape):
    import numpy as np
    labels = np.asarray(labels)
    bounds = np.asarray(bounds)
    confidence = np.asarray(confidence)
    if bounds.ndim != 2 or bounds.shape[1] != 4 or labels.ndim != 1 or confidence.ndim != 1:
        raise FDIProbeError("invalid_detections_shape")
    if not len(labels) == len(bounds) == len(confidence):
        raise FDIProbeError("inconsistent_detection_count")
    if not (np.isfinite(bounds).all() and np.isfinite(confidence).all() and np.isfinite(labels).all()):
        raise FDIProbeError("nonfinite_detection_values")
    if not np.all(labels == np.floor(labels)) or np.any((labels < 0) | (labels >= 32)):
        raise FDIProbeError("invalid_fdi_class")
    if np.any((confidence < 0) | (confidence > 1)):
        raise FDIProbeError("invalid_confidence")
    height, width = image_shape
    if len(bounds) and (np.any(bounds[:, 2] <= bounds[:, 0]) or np.any(bounds[:, 3] <= bounds[:, 1])
        or np.any(bounds[:, 0] < 0) or np.any(bounds[:, 1] < 0)
        or np.any(bounds[:, 2] > width) or np.any(bounds[:, 3] > height)):
        raise FDIProbeError("invalid_tooth_box")
    # Multiple proposals for one FDI code and missing teeth are POSSIBLE. Neither
    # force unique labeling nor silently assign shifted numbers: flag for clinician.
    fdi = [CLASS_ORDER[int(cls)] for cls in labels]
    duplicates = sorted({x for x in fdi if fdi.count(x) > 1})
    return {"proposals": len(fdi), "unique_fdi": len(set(fdi)),
            "duplicate_fdi_needs_review": duplicates,
            "missing_fdi_do_not_autofill": [x for x in CLASS_ORDER if x not in fdi]}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as fd:
        for data in iter(lambda: fd.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def run() -> dict:
    import numpy as np
    from huggingface_hub import HfApi, hf_hub_download
    from ultralytics import YOLO

    metadata = HfApi().model_info(MODEL_REPO, revision=MODEL_REVISION)
    revision = metadata.sha
    if revision != MODEL_REVISION:
        raise FDIProbeError("untrusted_hub_revision")
    files = [item.rfilename for item in metadata.siblings]
    if MODEL_WEIGHTS_FILE not in files:
        raise FDIProbeError("pinned_model_weight_missing")
    file_path = Path(hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_WEIGHTS_FILE, revision=revision))
    if not file_path.is_file() or not 1_000_000 < file_path.stat().st_size < 200_000_000:
        raise FDIProbeError("unexpected_weights_size")
    actual_sha256 = digest(file_path)
    if actual_sha256 != MODEL_WEIGHTS_SHA256:
        raise FDIProbeError("pinned_model_weight_sha256_mismatch")
    # .pt uses pickle; ONLY run on ephemeral unprivileged CI without credentials.
    model = YOLO(str(file_path), task="detect")
    class_names = verify_names(model.names)
    # Clearly artificial radiograph-like brightness gradient; not real medical data.
    wide = np.tile(np.linspace(10, 230, 2048, dtype=np.uint8), (1024, 1))
    synthetic = np.dstack((wide, wide, wide))
    prediction = model.predict(source=synthetic, device="cpu", imgsz=1024,
                               conf=0.25, iou=0.5, verbose=False)[0]
    summary = validate_detections(prediction.boxes.cls.cpu().numpy(),
                  prediction.boxes.xyxy.cpu().numpy(), prediction.boxes.conf.cpu().numpy(),
                  synthetic.shape[:2])
    return {
        "status": "PASS_SYNTHETIC_TECH_ONLY",
        "mission": "LOT05/05.7-J10D",
        "purpose": "32-class tooth boxes and FDI labels; no pathology detection",
        "source_repo": MODEL_REPO, "source_commit": revision, "weights_file": MODEL_WEIGHTS_FILE,
        "weights_sha256": actual_sha256, "weights_bytes": file_path.stat().st_size,
        "class_order": list(class_names), "synthetic_output": summary,
        "clinical_approved": False, "commercial_redistribution_cleared": False,
        "installed_in_cabinet": False, "tested_on_real_radiographs": False,
        "no_patient_data": True, "research_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("lot05-fdi-probe.json"))
    args = parser.parse_args()
    try:
        report = run()
    except Exception as exc:
        report = {"status": "FAILED_TO_VERIFY", "error": str(exc),
                  "clinical_approved": False, "no_patient_data": True}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS_SYNTHETIC_TECH_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
