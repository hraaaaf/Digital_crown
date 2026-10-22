#!/usr/bin/env python3
"""LOT05/J10E: pinned FDI YOLO -> local ONNX -> REVIEW JSON, strictly research only.

No patient network, no model/weights bundled with the application, no production
backend integration. To use images, only on lawfully authorized isolated local PC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from lot05_j10d_fdi_tooth_model_probe import (
    MODEL_WEIGHTS_SHA256, CLASS_ORDER, verify_names,
)

REVIEW_SCHEMA = "digital-crown-fdi-review-v1"
ONNX_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})


class FDIIntegrationError(ValueError):
    pass


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_model_file(path: Path, expected_sha: str, extension: str) -> Path:
    if path.suffix.lower() != extension or not path.is_file() or path.is_symlink():
        raise FDIIntegrationError("model_must_be_local_regular_file")
    if not isinstance(expected_sha, str) or not ONNX_SHA_RE.fullmatch(expected_sha):
        raise FDIIntegrationError("invalid_trusted_hash")
    if hash_file(path) != expected_sha:
        raise FDIIntegrationError("model_hash_mismatch")
    return path


def format_predictions(width: int, height: int, rows: list) -> dict:
    if not isinstance(width, int) or isinstance(width, bool) or not 1 <= width <= 10000:
        raise FDIIntegrationError("invalid_image_width")
    if not isinstance(height, int) or isinstance(height, bool) or not 1 <= height <= 10000:
        raise FDIIntegrationError("invalid_image_height")
    if not isinstance(rows, list) or len(rows) > 300:
        raise FDIIntegrationError("invalid_proposal_count")
    proposals = []
    for row in rows:
        if not isinstance(row, dict):
            raise FDIIntegrationError("invalid_proposal")
        import math
        idx, box, confidence = row.get("cls"), row.get("box"), row.get("conf")
        if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < len(CLASS_ORDER):
            raise FDIIntegrationError("invalid_permanent_fdi_index")
        if not isinstance(box, (list, tuple)) or len(box) != 4 or any(
            not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in box
        ):
            raise FDIIntegrationError("invalid_pixel_bbox")
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise FDIIntegrationError("bbox_outside_image")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise FDIIntegrationError("invalid_confidence")
        proposals.append({
            "fdi": CLASS_ORDER[idx],
            "bbox": [round(x1 / width, 7), round(y1 / height, 7),
                     round(x2 / width, 7), round(y2 / height, 7)],
            "confidence": round(float(confidence), 6),
        })
    return {"schema": REVIEW_SCHEMA, "image_width": width, "image_height": height,
            "proposals": proposals}


def export_pinned_pt_to_onnx(checkpoint: Path, target: Path) -> dict:
    # A .pt file contains pickle, so NEVER use a downloaded or modified blob
    # without this immutable author-pinned checksum and disposable research sandbox.
    verified = verify_model_file(checkpoint, MODEL_WEIGHTS_SHA256, ".pt")
    if target.suffix.lower() != ".onnx" or target.is_symlink():
        raise FDIIntegrationError("invalid_onnx_output")
    from ultralytics import YOLO
    model = YOLO(str(verified), task="detect")
    verify_names(model.names)
    exported = Path(model.export(format="onnx", imgsz=1024, batch=1, dynamic=False,
                                 simplify=False, opset=17, device="cpu"))
    if not exported.is_file():
        raise FDIIntegrationError("onnx_export_missing")
    # Prevent replacing source checkpoint accidentally; no binary in repo or CI artifacts.
    if exported.resolve() != target.resolve():
        shutil.copyfile(exported, target)
    from ultralytics import YOLO as _YOLO
    probe = _YOLO(str(target), task="detect")
    verify_names(probe.names)
    return {"format": "ONNX", "sha256": hash_file(target), "model_classes": len(CLASS_ORDER),
            "imgsz": 1024, "clinical_approval": False, "commercial_rights_cleared": False}


def infer_from_local_onnx(onnx: Path, checksum: str, image: Path) -> dict:
    verify_model_file(onnx, checksum, ".onnx")
    if not image.is_file() or image.is_symlink() or image.suffix.lower() not in IMAGE_SUFFIXES:
        raise FDIIntegrationError("invalid_local_image")
    import cv2
    from ultralytics import YOLO
    pixels = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if pixels is None:
        raise FDIIntegrationError("image_decode_failed")
    h, w = pixels.shape[:2]
    if w > 10000 or h > 10000:
        raise FDIIntegrationError("image_dimensions_unsupported")
    model = YOLO(str(onnx), task="detect")
    verify_names(model.names)
    prediction = model.predict(source=pixels, imgsz=1024, device="cpu", conf=0.25,
                               iou=0.5, verbose=False)[0]
    rows = [
        {"cls": int(cls), "box": list(map(float, box)), "conf": float(score)}
        for cls, box, score in zip(
            prediction.boxes.cls.cpu().numpy().tolist(),
            prediction.boxes.xyxy.cpu().numpy().tolist(),
            prediction.boxes.conf.cpu().numpy().tolist())
    ]
    return format_predictions(w, h, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pinned 32-tooth FDI research ONNX bridge, offline only")
    parser.add_argument("operation", choices=("export", "infer"))
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--onnx", type=Path, required=True)
    parser.add_argument("--onnx-sha256")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--authorized-research-local", action="store_true")
    args = parser.parse_args()
    if not args.authorized_research_local:
        parser.error("requires --authorized-research-local (no clinical/production use)")
    try:
        if args.operation == "export":
            if args.checkpoint is None:
                raise FDIIntegrationError("pinned_pt_required")
            report = export_pinned_pt_to_onnx(args.checkpoint, args.onnx)
            print(json.dumps(report, sort_keys=True))  # no paths/data
        else:
            if args.onnx_sha256 is None or args.image is None or args.json_out is None:
                raise FDIIntegrationError("onnx_hash_image_and_output_required")
            data = infer_from_local_onnx(args.onnx, args.onnx_sha256, args.image)
            if args.json_out.is_symlink() or args.json_out.suffix.lower() != ".json":
                raise FDIIntegrationError("unsafe_local_report_path")
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": "RESEARCH_PROPOSALS_EXPORTED",
                              "proposals": len(data["proposals"]),
                              "clinical_approval": False,
                              "output_sent_to_network": False}))
    except Exception as exc:
        # No user path / patient identifiers / tracebacks in default terminal report.
        allowed = {"FDIIntegrationError", "FDIProbeError"}
        kind = type(exc).__name__
        print(json.dumps({"status": "RESEARCH_OPERATION_FAILED",
                          "error_class": kind if kind in allowed else "UnexpectedError",
                          "clinical_approval": False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
