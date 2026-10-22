#!/usr/bin/env python3
"""R23-K: compare EXACT 38 SRPose38 channels to the SAME CL-Detection2023 film's
human GT indices (1..38). No anatomical aliases, angles, training or norm.

Protected challenge data must be supplied locally under legitimate permission.
Never upload radiographs/GT/derived overlays to CI, GitHub, or public storage.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODEL_SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
MODEL_BYTES = 267_484_931
SOURCE_REPO = "https://github.com/cwwang1979/CL-detection2023"
SOURCE_DATA = "https://zenodo.org/records/7787671"
REPORT_SCHEMA = "CEPH_R23K_EXACT_SAME_FILM_38_INDEX_COMPARISON_V1"

class PairEvidenceError(ValueError):
    pass

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for part in iter(lambda: inp.read(8 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def load_organizer_gt(gt_path: Path, case_id: int) -> tuple[list[tuple[float, float]], float]:
    """Original organizer format: point = [x, y, 1-based image id], name=1..38."""
    if gt_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(gt_path) as z:
            matches = [x for x in z.infolist()
                       if Path(x.filename).name.lower() == "train-gt.json" and not x.is_dir()]
            if len(matches) != 1 or matches[0].file_size > 30_000_000:
                raise PairEvidenceError("Exactly one bounded original train-gt.json required")
            raw = z.read(matches[0])
    elif gt_path.suffix.lower() == ".json":
        if gt_path.stat().st_size > 30_000_000:
            raise PairEvidenceError("Oversized GT JSON")
        raw = gt_path.read_bytes()
    else:
        raise PairEvidenceError("Only official train-gt.json or its ZIP supported")
    doc = json.loads(raw)
    if not isinstance(doc, dict) or not isinstance(doc.get("points"), list):
        raise PairEvidenceError("Expected original organizer points list, not predictions")
    points = {}
    scales = set()
    for row in doc["points"]:
        if not isinstance(row, dict):
            raise PairEvidenceError("Malformed ground truth row")
        xyz = row.get("point")
        if not isinstance(xyz, list) or len(xyz) != 3:
            raise PairEvidenceError("Missing original [x,y,z] ground truth coordinate")
        z = xyz[2]
        if isinstance(z, bool) or type(z) is not int:
            raise PairEvidenceError("Noninteger image identifier")
        if z != case_id:
            continue
        k = row.get("name")
        if type(k) is not int or k < 1 or k > 38 or k in points:
            raise PairEvidenceError("Duplicate / missing / invalid GT channel 1..38")
        x, y = xyz[:2]
        try:
            x, y, scale = float(x), float(y), float(row.get("scale"))
        except (TypeError, ValueError) as exc:
            raise PairEvidenceError("Unusable GT coordinate or spacing") from exc
        if not all(math.isfinite(q) for q in (x, y, scale)) or x < 0 or y < 0 or scale <= 0:
            raise PairEvidenceError("Nonfinite, negative or zero GT coordinate/spacing")
        points[k] = (x, y)
        scales.add(scale)
    if set(points) != set(range(1, 39)):
        raise PairEvidenceError(f"Film {case_id}: {len(points)}/38 ground truth points; refusing partial pair")
    if len(scales) != 1:
        raise PairEvidenceError("Multiple inconsistent mm/px scales in SAME film")
    return [points[k] for k in range(1, 39)], scales.pop()

def read_original_mha_slice(mha_path: Path, case_id: int):
    """Read one uncompressed LOCAL MetaImage slice without loading 400 images.

    Only accepts the exact class of contiguous 3D unsigned-byte image stacks,
    never silently guesses compressed/layout formats.
    """
    import numpy as np
    meta = {}
    with mha_path.open("rb") as source:
        for i in range(120):
            line = source.readline(4096)
            if not line or len(line) >= 4096:
                raise PairEvidenceError("Missing bounded MHA header")
            stripped = line.decode("ascii", errors="strict").strip()
            if "=" not in stripped:
                continue
            key, value = [x.strip() for x in stripped.split("=", 1)]
            meta[key] = value
            if key == "ElementDataFile":
                break
        offset = source.tell()
        if meta.get("ElementDataFile", "").upper() != "LOCAL":
            raise PairEvidenceError("Only original LOCAL MHA stacks supported")
        if meta.get("CompressedData", "False").lower() in ("true", "1"):
            raise PairEvidenceError("Compressed MHA not supported; do not guess image extraction")
        if meta.get("ElementType") != "MET_UCHAR" or meta.get("NDims") != "3":
            raise PairEvidenceError("Expected 3D unsigned-byte MetaImage stack")
        if meta.get("BinaryData", "True").lower() not in ("true", "1"):
            raise PairEvidenceError("Expected binary MHA stack")
        try:
            width, height, depth = map(int, meta["DimSize"].split())
            channels = int(meta.get("ElementNumberOfChannels", "1"))
        except (ValueError, KeyError) as exc:
            raise PairEvidenceError("Missing exact dimensions/channels") from exc
        if channels not in (1, 3) or width < 20 or height < 20 or depth < 1:
            raise PairEvidenceError("Unsupported image geometry")
        if width * height * channels > 75_000_000 or depth > 1000:
            raise PairEvidenceError("Refusing unsafe stack size")
        if not (1 <= case_id <= depth):
            raise PairEvidenceError("Requested 1-based film ID not present in stack")
        stride = width * height * channels
        expected = offset + stride * depth
        if mha_path.stat().st_size != expected:
            raise PairEvidenceError("Raw MHA body size/layout not exact; refuse unsafe image/GT pairing")
        source.seek(offset + (case_id-1) * stride)
        raw = source.read(stride)
    if len(raw) != stride:
        raise PairEvidenceError("Truncated film slice")
    if channels == 3:
        rgb = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3).copy()
        # Original color MHA convention follows SimpleITK RGB; cv2 model uses BGR.
        bgr = rgb[..., ::-1].copy()
    else:
        mono = np.frombuffer(raw, dtype=np.uint8).reshape(height, width).copy()
        bgr = np.repeat(mono[..., None], 3, axis=2)
    # Exact organizer preprocessing crops ZERO padding from bottom/right only.
    valid_y = np.any(bgr != 0, axis=(1, 2))
    valid_x = np.any(bgr != 0, axis=(0, 2))
    if not valid_y.any() or not valid_x.any():
        raise PairEvidenceError("All-zero image")
    bgr = bgr[:int(np.flatnonzero(valid_y)[-1])+1,
              :int(np.flatnonzero(valid_x)[-1])+1, :]
    return bgr

def score_channels(pred, ground_truth, mm_per_px: float, width: int, height: int):
    """STRICT positional index i=0..37 ↔ official GT name i+1."""
    import numpy as np
    p = np.asarray(pred, dtype=float)
    gt = np.asarray(ground_truth, dtype=float)
    if p.shape != (38, 2) or gt.shape != (38, 2) or not np.isfinite(gt).all():
        raise PairEvidenceError("Exactly 38 (x,y) predictions and 38 reference points required")
    if not math.isfinite(mm_per_px) or mm_per_px <= 0:
        raise PairEvidenceError("Image-specific GT scale is missing")
    data = []
    for i in range(38):
        x, y = map(float, p[i])
        rx, ry = map(float, gt[i])
        if not (0 <= rx < width and 0 <= ry < height):
            raise PairEvidenceError(f"GT channel {i+1} is outside matched film")
        valid = math.isfinite(x) and math.isfinite(y) and 0 <= x < width and 0 <= y < height
        px = math.hypot(x-rx, y-ry) if valid else None
        data.append({"index_1_based":i+1,
                     "gt_x":rx,"gt_y":ry,"pred_x":x if valid else None,
                     "pred_y":y if valid else None,
                     "dx_px":x-rx if valid else None,"dy_px":y-ry if valid else None,
                     "error_px":px,"error_mm":px*mm_per_px if px is not None else None,
                     "valid_in_frame":valid})
    return data

def inference(image, model_file: Path):
    import numpy as np
    if not model_file.is_file() or model_file.stat().st_size != MODEL_BYTES or sha256(model_file) != MODEL_SHA256:
        raise PairEvidenceError("SRPose38 model missing or mismatched size/SHA256")
    reg = json.loads((ROOT/"backend/scientific_assets.json").read_text())
    expected = next(x for x in reg["assets"] if x["id"]=="cephalo_sota")
    if expected["sha256"] != MODEL_SHA256 or expected["size_bytes"] != MODEL_BYTES:
        raise PairEvidenceError("Scientific asset registry drift")
    import onnxruntime as ort
    from backend.services.srpose38_pipeline import (
        decode_srpose38_heatmaps, prepare_srpose38_input)
    session = ort.InferenceSession(str(model_file), providers=["CPUExecutionProvider"])
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise PairEvidenceError("Expected CPUExecutionProvider only")
    tensor, geometry = prepare_srpose38_input(image)
    output = session.run(None, {session.get_inputs()[0].name: tensor})[0]
    pred, scores = decode_srpose38_heatmaps(output, geometry)
    if pred.shape != (38, 2) or scores.shape != (38,):
        raise PairEvidenceError("Unexpected ONNX 38-channel output")
    return pred

def make_overlay(image, rows, destination: Path):
    import cv2
    canvas = image.copy()
    for r in rows:
        a = (round(r["gt_x"]), round(r["gt_y"]))
        cv2.circle(canvas, a, 7, (50, 200, 60), thickness=2, lineType=cv2.LINE_AA)
        if r["valid_in_frame"]:
            b = (round(r["pred_x"]), round(r["pred_y"]))
            cv2.line(canvas, a, b, (0, 235, 255), thickness=2, lineType=cv2.LINE_AA)
            cv2.circle(canvas, b, 3, (15, 15, 245), thickness=-1, lineType=cv2.LINE_AA)
        cv2.putText(canvas, str(r["index_1_based"]), (a[0]+7, a[1]-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 200, 60), 1, cv2.LINE_AA)
    if not cv2.imwrite(str(destination), canvas):
        raise PairEvidenceError("Could not write overlay")
    return destination

def run(args):
    if not args.confirm_dataset_rights:
        raise PairEvidenceError("Official image dataset is RESTRICTED: permission must be separately obtained and confirmed")
    if args.case_id < 1 or args.case_id > 400:
        raise PairEvidenceError("This comparator only accepts original TRAIN 1-based case IDs 1..400")
    for file in (args.mha, args.gt):
        if not file.is_file():
            raise PairEvidenceError(f"Required original source file absent: {file.name}")
    gt, scale = load_organizer_gt(args.gt, args.case_id)
    img = read_original_mha_slice(args.mha, args.case_id)
    height, width = img.shape[:2]
    # Always check exact source pairing BEFORE any GPU/ONNX inference.
    score_channels(gt, gt, scale, width, height)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": REPORT_SCHEMA, "status": "PAIR_VERIFIED_MODEL_NOT_RUN",
        "clinical_release": False, "anatomical_name_mapping_verified": False,
        "independent_test": False, # CL2023 training image: possible model exposure.
        "case_id":args.case_id,
        "source":SOURCE_DATA, "organizer_ground_truth":SOURCE_REPO,
        "mha_sha256":sha256(args.mha),"gt_sha256":sha256(args.gt),
        "dimensions_cropped":[width, height],
        "gt_points":38,"mm_per_px_source":scale,
        "model_sha256_expected":MODEL_SHA256,
        "model_checked":False,"model_ran":False,
        "per_channel":[],"summary":None,
        "restrictions":"Local authorized research only. Do not publish patient radiograph/annotation or treat train images as untouched acceptance."
    }
    if args.check_pair_only:
        pass
    else:
        pred = inference(img,args.model)
        rows = score_channels(pred,gt,scale,width,height)
        import numpy as np
        valid = [r["error_mm"] for r in rows if r["valid_in_frame"]]
        report["per_channel"] = rows
        report["summary"] = {
            "n_valid":len(valid),"n_failed":38-len(valid),
            "mean_mm":float(np.mean(valid)) if valid else None,
            "median_mm":float(np.median(valid)) if valid else None,
            # p95 across 38 channels of ONE film, not population model P95!
            "single_film_channel_p95_mm":float(np.percentile(valid,95)) if valid else None
        }
        report["model_checked"] = True
        report["model_ran"] = True
        report["status"] = "PAIR38_SCORED_RETROSPECTIVE_ONLY"
        with (args.output/"channels.csv").open("w",newline="",encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        make_overlay(img,rows,args.output/"overlay_local_only.png")
    (args.output/"report.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"case_id":args.case_id,
                      "points":38,"model_ran":report["model_ran"],
                      "clinical_release":False},sort_keys=True))
    return 0

def main():
    p=argparse.ArgumentParser(description="CL2023 same-film exact channel-index SRPose38 comparison (private/local)")
    p.add_argument("--mha",type=Path,required=True,help="Licensed original train_stack.mha")
    p.add_argument("--gt",type=Path,required=True,help="Original train-gt.json[.zip] organizer annotations")
    p.add_argument("--case-id",type=int,required=True,help="Original 1-based z/slice ID, not array index")
    p.add_argument("--model",type=Path,default=ROOT/"backend/ai_models/srpose38-tta-1024.onnx")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--confirm-dataset-rights",action="store_true",help="You have independently obtained organizer authorization; NOT an access bypass")
    p.add_argument("--check-pair-only",action="store_true",help="Read real matched image+38 GT; do not infer or claim scoring")
    args=p.parse_args()
    try:
        return run(args)
    except (PairEvidenceError,KeyError,TypeError,ValueError) as exc:
        print(f"R23K_FAIL_CLOSED_NO_COMPARISON: {exc}",file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
