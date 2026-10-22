#!/usr/bin/env python3
"""OralGuard pinned 1024px ONNX CPU RESEARCH-ONLY offline detector.

Never connects to Digital Crown's cabinet API or patient DB, and never assigns FDI
numbers/diagnoses. Input files stay on the local machine. CI uses synthetic pixels.
A readable JSON result means experimental object localization, not clinical truth.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

INPUT_SIZE = 1024
ORALGUARD_ONNX_SHA256 = "493d5cef350572af09b16825aca393bd030cbe74c0bdc2cb1a880c6d82c7304f"
EXPECTED_ORDER = ("caries", "deep_caries", "periapical_lesion", "impacted_tooth")
MAX_CANDIDATES = 5000
MAX_DETECTIONS = 100


class OralGuardProbeError(ValueError):
    """Refuse malformed, mislabelled, or untrusted model or output."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(path: Path, expected_sha256: str = ORALGUARD_ONNX_SHA256) -> None:
    if not path.is_file() or path.is_symlink():
        raise OralGuardProbeError("pinned_model_not_found")
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256.lower()):
        raise OralGuardProbeError("invalid_expected_sha256")
    if sha256(path) != expected_sha256.lower():
        raise OralGuardProbeError("model_sha256_mismatch")


def _normal_label(label: Any) -> str:
    if not isinstance(label, str):
        raise OralGuardProbeError("non_string_class_name")
    return "".join(ch for ch in label.lower() if ch.isalnum())


def verify_class_order(metadata: Any) -> tuple[str, ...]:
    """Require actual checkpoint metadata; never trust a caller-supplied index list."""
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            try:
                metadata = ast.literal_eval(metadata)
            except (SyntaxError, ValueError, TypeError) as exc:
                raise OralGuardProbeError("invalid_class_metadata") from exc
    if not isinstance(metadata, dict) or len(metadata) != 4:
        raise OralGuardProbeError("missing_or_extra_classes")
    try:
        indexed = {int(k): v for k, v in metadata.items()}
    except (TypeError, ValueError) as exc:
        raise OralGuardProbeError("invalid_class_index") from exc
    if set(indexed) != {0, 1, 2, 3}:
        raise OralGuardProbeError("wrong_class_indices")
    observed = tuple(_normal_label(indexed[i]) for i in range(4))
    canonical = tuple(_normal_label(v) for v in EXPECTED_ORDER)
    if observed != canonical:
        raise OralGuardProbeError("unsafe_class_order")
    return EXPECTED_ORDER


def verify_session(session: Any) -> None:
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise OralGuardProbeError("not_cpu_only")
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if len(inputs) != 1 or list(inputs[0].shape) != [1, 3, INPUT_SIZE, INPUT_SIZE]:
        raise OralGuardProbeError("invalid_input_shape")
    if len(outputs) != 1 or list(outputs[0].shape) != [1, 8, 21504]:
        raise OralGuardProbeError("invalid_output_shape")
    meta = session.get_modelmeta().custom_metadata_map
    if not isinstance(meta, dict) or not meta.get("names"):
        raise OralGuardProbeError("class_metadata_missing")
    verify_class_order(meta["names"])


def letterbox(image_rgb: np.ndarray) -> tuple[np.ndarray, float, tuple[int, int]]:
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3 or image_rgb.dtype != np.uint8:
        raise OralGuardProbeError("invalid_rgb_image")
    height, width = image_rgb.shape[:2]
    if not height or not width:
        raise OralGuardProbeError("empty_image")
    ratio = min(INPUT_SIZE / height, INPUT_SIZE / width)
    new_w, new_h = round(width * ratio), round(height * ratio)
    resized = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    total_w, total_h = INPUT_SIZE - new_w, INPUT_SIZE - new_h
    left, top = round(total_w / 2 - 0.1), round(total_h / 2 - 0.1)
    right, bottom = total_w - left, total_h - top
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    tensor = np.transpose(padded.astype(np.float32) / 255.0, (2, 0, 1))[None, :]
    return np.ascontiguousarray(tensor), ratio, (left, top)


def _iou(one: np.ndarray, others: np.ndarray) -> np.ndarray:
    upper = np.maximum(one[:2], others[:, :2])
    lower = np.minimum(one[2:], others[:, 2:])
    size = np.maximum(0.0, lower - upper)
    inter = size[:, 0] * size[:, 1]
    area_one = (one[2] - one[0]) * (one[3] - one[1])
    areas = (others[:, 2] - others[:, 0]) * (others[:, 3] - others[:, 1])
    return inter / np.maximum(area_one + areas - inter, 1e-9)


def decode_onnx(raw_output: np.ndarray, *, image_shape: tuple[int, int], scale: float, padding: tuple[int, int], confidence: float = 0.25) -> list[dict[str, Any]]:
    """Decode 4-class YOLOv8 ONNX tensor; class-aware IoU NMS, no tooth ID."""
    if not 0.0 < confidence < 1.0:
        raise OralGuardProbeError("invalid_confidence")
    predictions = np.asarray(raw_output)
    if predictions.shape != (1, 8, 21504) or not np.isfinite(predictions).all():
        raise OralGuardProbeError("invalid_or_nonfinite_output")
    head = predictions[0]
    cls_idx = head[4:8].argmax(axis=0)
    scores = head[4:8].max(axis=0)
    keep = np.flatnonzero(scores >= confidence)
    if len(keep) > MAX_CANDIDATES:
        raise OralGuardProbeError("too_many_candidates")
    if len(keep) == 0:
        return []
    candidate_xywh = head[:4, keep].T
    if (candidate_xywh[:, 2:] <= 0).any():
        raise OralGuardProbeError("invalid_box_geometry")
    centers = candidate_xywh[:, :2]
    half_sizes = candidate_xywh[:, 2:] / 2
    boxes = np.concatenate([centers - half_sizes, centers + half_sizes], axis=1)
    boxes[:, (0, 2)] = (boxes[:, (0, 2)] - padding[0]) / scale
    boxes[:, (1, 3)] = (boxes[:, (1, 3)] - padding[1]) / scale
    h, w = image_shape
    boxes[:, (0, 2)] = np.clip(boxes[:, (0, 2)], 0, w)
    boxes[:, (1, 3)] = np.clip(boxes[:, (1, 3)], 0, h)
    valid = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])
    boxes = boxes[valid]
    class_ids = cls_idx[keep][valid]
    conf_scores = scores[keep][valid]
    if len(boxes) == 0:
        return []
    order = np.argsort(-conf_scores, kind="stable")
    selected: list[int] = []
    for index in order:
        same_cls = [i for i in selected if class_ids[i] == class_ids[index]]
        if same_cls and np.any(_iou(boxes[index], boxes[same_cls]) > 0.50):
            continue
        selected.append(int(index))
        if len(selected) >= MAX_DETECTIONS:
            break
    return [{
        "finding_candidate": EXPECTED_ORDER[int(class_ids[i])],
        "confidence_uncalibrated": round(float(conf_scores[i]), 6),
        "bbox_xyxy_pixels": [round(float(v), 2) for v in boxes[i]],
    } for i in selected]


def run_probe(onnx_path: Path, image_rgb: np.ndarray, *, expected_sha256: str = ORALGUARD_ONNX_SHA256, confidence: float = 0.25) -> dict[str, Any]:
    verify_artifact(onnx_path, expected_sha256)
    import onnxruntime as ort  # delayed import: unit tests do not need engine
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    verify_session(session)
    img, scale, padding = letterbox(image_rgb)
    output = session.run(None, {session.get_inputs()[0].name: img})
    if len(output) != 1:
        raise OralGuardProbeError("unexpected_number_of_outputs")
    findings = decode_onnx(np.asarray(output[0]), image_shape=image_rgb.shape[:2], scale=scale, padding=padding, confidence=confidence)
    return {"status": "EXPERIMENTAL_ONLY", "model": "OralGuard", "class_order_verified": True,
            "onnx_sha256_verified": True, "patient_diagnosis": False, "fdi_numbering": None,
            "confidence_threshold_uncalibrated": confidence, "findings": findings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pinned offline research-only OralGuard ONNX CPU probe; NOT for clinical use")
    parser.add_argument("--onnx", type=Path, required=True)
    parser.add_argument("--image", type=Path, help="Local image path; omitted means synthetic research input")
    parser.add_argument("--expected-sha256", required=True, help="Trusted digest from verified source-pinned ONNX export or release manifest")
    parser.add_argument("--research-only", action="store_true", required=True, help="Acknowledge this is NOT clinical diagnosis")
    parser.add_argument("--report", type=Path, help="Explicit local JSON report path (no source filename in report)")
    args = parser.parse_args()
    if args.image:
        # Never upload or automatically archive input pixels or patient metadata.
        bgr = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
        if bgr is None:
            raise OralGuardProbeError("unreadable_local_image")
        image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    else:
        gradient = np.tile(np.linspace(0, 255, 1536, dtype=np.uint8), (768, 1))
        image = np.dstack((gradient, gradient, gradient))
    result = run_probe(args.onnx, image, expected_sha256=args.expected_sha256)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
