"""Research-only GitHub Actions proof: export selected FDI .pt to ONNX and check parity.

Only public publisher AKUDENTAL films on ephemeral no-secret CPU. No images,
checkpoint, per-image predictions or ONNX weights are uploaded in artifacts.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import tempfile
import platform

from lot05_j10d_fdi_akudental_public_ci import (
    _safe_filename_resolution, materialize_verified_checkpoint,
)
from lot05_j10d_fdi_akudental_coco_adapter import coco_to_manifest
from lot05_j10d_fdi_tooth_model_probe import (
    MODEL_REPO, MODEL_REVISION, MODEL_WEIGHTS_FILE, verify_names,
)
from lot05_j10e_fdi_onnx_bridge import export_pinned_pt_to_onnx, hash_file


def box_iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0., x2-x1) * max(0., y2-y1)
    area_a = (a[2]-a[0])*(a[3]-a[1])
    area_b = (b[2]-b[0])*(b[3]-b[1])
    return inter / max(1e-12, area_a + area_b - inter)


def compare_predictions(ref, onnx, min_iou=.90, max_conf_delta=.08):
    """Same-class one-to-one IoU greedy parity without hiding unmatched boxes."""
    def entries(res):
        return sorted(zip(res.boxes.cls.cpu().numpy().tolist(),
                          res.boxes.xyxy.cpu().numpy().tolist(),
                          res.boxes.conf.cpu().numpy().tolist()),
                      key=lambda x: (-float(x[2]),int(x[0])))
    gt, pr = entries(ref), entries(onnx)
    if not gt and not pr:
        return {"pt": 0, "onnx": 0, "matching": 0, "fdi_mismatch_or_missing": 0}
    pairs = []
    for gi, (gc, gb, gs) in enumerate(gt):
        for pi, (pc, pb, ps) in enumerate(pr):
            if int(gc) != int(pc) or abs(gs-ps) > max_conf_delta:
                continue
            iou = box_iou(gb,pb)
            if iou >= min_iou:
                pairs.append((-iou,gi,pi))
    pairs.sort()
    matched_g, matched_p = set(), set()
    for _,gi,pi in pairs:
        if gi in matched_g or pi in matched_p:
            continue
        matched_g.add(gi); matched_p.add(pi)
    return {"pt":len(gt),"onnx":len(pr),"matching":len(matched_g),
            "fdi_mismatch_or_missing":max(len(gt),len(pr))-len(matched_g)}


def run(source: Path, count: int = 2):
    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO
    import cv2
    if not 1 <= count <= 8:
        raise ValueError("invalid_fixed_film_count")
    folder=source/"AKUDENTAL"
    original=json.loads((folder/"akudental_instances.json").read_text(encoding="utf-8"))
    mapped=_safe_filename_resolution(original,folder/"images",count)
    manifest,audit=coco_to_manifest(mapped,images_root=folder/"images",max_images=count)
    cases=manifest["cases"]
    if len(cases)!=count:
        raise ValueError("unexpected_source_sample_count")
    sample_fdi=0
    comparison=[]
    with tempfile.TemporaryDirectory(prefix="dc-fdi-onnx-") as tmp:
        workspace=Path(tmp)
        hf=Path(hf_hub_download(repo_id=MODEL_REPO,filename=MODEL_WEIGHTS_FILE,revision=MODEL_REVISION))
        pinned=materialize_verified_checkpoint(hf,workspace)
        meta=export_pinned_pt_to_onnx(pinned,workspace/"verified-best.onnx")
        ref_model=YOLO(str(pinned),task="detect")
        out_model=YOLO(str(workspace/"verified-best.onnx"),task="detect")
        verify_names(ref_model.names)
        verify_names(out_model.names)
        for case in cases:
            # Original image is local to ephemeral runner; not logged or uploaded.
            image=folder/"images"/case["image"]
            frame=cv2.imread(str(image),cv2.IMREAD_COLOR)
            if frame is None or frame.shape[:2] != (case["height"],case["width"]):
                raise ValueError("public_image_decode_or_size_mismatch")
            p=ref_model.predict(source=frame,device="cpu",imgsz=1024,conf=.25,iou=.5,verbose=False)[0]
            o=out_model.predict(source=frame,device="cpu",imgsz=1024,conf=.25,iou=.5,verbose=False)[0]
            result=compare_predictions(p,o)
            comparison.append(result)
            sample_fdi += len(case["gt"])
    total=Counter()
    for group in comparison:total.update(group)
    report={
        "purpose":"FDI numbering ONNX CPU parity, not diagnosis/clinical clearance",
        "model_repo":MODEL_REPO, "model_revision":MODEL_REVISION,
        "onnx_sha256":meta["sha256"],"onnx_bytes_retained":False,
        "public_source":"AKUDENTAL publisher public research collection",
        "source_cohort_ids_in_report":False,
        "images":len(cases),"source_reference_teeth":sample_fdi,
        "pt_detections":total["pt"],"onnx_detections":total["onnx"],
        "same_FDI_iou90_and_conf08_matches":total["matching"],
        "disagreement_count":total["fdi_mismatch_or_missing"],
        "parity_threshold":{"box_iou":.9,"confidence_abs_delta":.08},
        "status":"TECHNICAL_CPU_PARITY" if total["pt"]>0 and total["fdi_mismatch_or_missing"]==0 else "PARITY_NOT_ESTABLISHED",
        "tested_windows":platform.system() == "Windows","clinical_approval":False,"commercial_rights_cleared":False,
        "patient_data_uploaded":False,
    }
    return report


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--publisher-repo",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--count",type=int,default=2)
    args=p.parse_args()
    try:
        result=run(args.publisher_repo,args.count)
        args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k in
            {"status","images","source_reference_teeth","pt_detections",
             "onnx_detections","same_FDI_iou90_and_conf08_matches","disagreement_count",
             "tested_windows","clinical_approval"}}))
        if result["status"]!="TECHNICAL_CPU_PARITY":
            raise SystemExit(1)
    except Exception as exc:
        # Do not echo image filenames, paths or upstream untrusted text to logs.
        print(json.dumps({"status":"PARITY_CHECK_FAILED",
                          "error_class":type(exc).__name__[:50],
                          "clinical_approval":False}))
        raise SystemExit(1)


if __name__=="__main__":
    main()
