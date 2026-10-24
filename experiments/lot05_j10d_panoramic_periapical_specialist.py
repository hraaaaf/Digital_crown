#!/usr/bin/env python3
"""Research-only DENTEX cross-domain test of Dental_012 periapical ONNX.

The model card is CC-BY-NC-SA: clinical/commercial integration is prohibited
without rightsholder permission. No patient images or model bytes retained.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import time
import traceback
from pathlib import Path
from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download
from ultralytics import YOLO

REPO = "chemahc94/Dental_012"
OUTPUT = Path(os.getenv("LOT05_PERIAPICAL_REPORT", "lot05-periapical-specialist.json"))
THRESHOLDS = [0.10, 0.25, 0.50]
RESULT = {
  "mission": "LOT05/05.7-J10D",
  "repo": REPO,
  "filename": "best.onnx",
  "license": "cc-by-nc-sa-4.0",
  "dataset": "tirandazdylan/dentex-panoramic",
  "dataset_split": "test",
  "model_training_source": "Mendeley Panoramic radiographs with periapical lesions",
  "cross_domain_but_patient_overlap_not_proven": True,
  "target_gt_class": 2,
  "thresholds": THRESHOLDS,
  "match_iou": 0.5,
  "max_cases": 74,
  "clinical_acceptance": False,
  "commercial_use_authorized": False,
  "status": "PENDING"
}


def iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w*h
    ar_a = max(0.0, a[2]-a[0])*max(0.0, a[3]-a[1])
    ar_b = max(0.0, b[2]-b[0])*max(0.0, b[3]-b[1])
    return inter/max(ar_a+ar_b-inter,1e-9)


def gts(row):
    objects = row["objects"]
    if isinstance(objects, dict):
        boxes, labels = objects["bbox"], objects["diagnosis"]
    else:
        boxes = [v["bbox"] for v in objects]
        labels = [v["diagnosis"] for v in objects]
    return [[float(x), float(y), float(x)+float(w), float(y)+float(h)]
            for (x,y,w,h), k in zip(boxes, labels) if int(k)==2]


def match(ground, detections, confidence):
    used=set()
    true=0
    false=0
    for p, box in detections:
        if p < confidence: continue
        available=[(idx,iou(box,g)) for idx,g in enumerate(ground) if idx not in used]
        if available:
            idx,overlap=max(available,key=lambda z:z[1])
            if overlap>=0.5:
                true+=1
                used.add(idx)
                continue
        false+=1
    return true,false,len(ground)-len(used)


try:
    metadata=HfApi().model_info(REPO)
    revision=str(metadata.sha)
    if len(revision)!=40: raise ValueError("Unpinned HF commit")
    model_path=Path(hf_hub_download(REPO,"best.onnx",revision=revision))
    if not model_path.is_file(): raise FileNotFoundError("Missing pinned specialist")
    hasher=hashlib.sha256(model_path.read_bytes()).hexdigest()
    RESULT.update({"model_revision":revision,"sha256":hasher,
                   "file_bytes":model_path.stat().st_size})
    model=YOLO(str(model_path),task="detect")
    totals={str(t):{"tp":0,"fp":0,"fn":0} for t in THRESHOLDS}
    times=[]
    processed=0
    classes=None
    for row in load_dataset("tirandazdylan/dentex-panoramic","diagnosis",
                            split="test",streaming=True):
        image=row["image"].convert("RGB")
        gt=gts(row)
        t=time.perf_counter()
        res=model.predict(image,imgsz=640,conf=0.10,iou=0.50,device="cpu",verbose=False)[0]
        times.append(time.perf_counter()-t)
        if classes is None:
            classes={int(k):str(v) for k,v in res.names.items()}
            if len(classes)!=1:
                raise ValueError(f"Specialist expected 1 periapical class, got {classes}")
            RESULT["model_class_names"]=classes
        det=sorted(
            [(float(conf),list(map(float,bb))) for conf,bb in
             zip(res.boxes.conf.tolist(),res.boxes.xyxy.tolist())],
            key=lambda z:z[0],reverse=True)
        for threshold in THRESHOLDS:
            tp,fp,fn=match(gt,det,threshold)
            m=totals[str(threshold)]
            m["tp"]+=tp;m["fp"]+=fp;m["fn"]+=fn
        processed+=1
        if processed>=74:break
    if processed!=74:raise ValueError(f"Expected 74 radiographs, got {processed}")
    for t in THRESHOLDS:
        m=totals[str(t)]
        m["precision"]=m["tp"]/(m["tp"]+m["fp"]) if m["tp"]+m["fp"] else None
        m["recall"]=m["tp"]/(m["tp"]+m["fn"]) if m["tp"]+m["fn"] else None
    RESULT.update({
        "status":"COMPLETED_EXPLORATORY","radiographs":processed,
        "results":totals,"median_cpu_seconds":statistics.median(times),
        "disclaimer":"11 periapical ground truths in 74 DENTEX films: wide uncertainty; not a patient-independent diagnostic evaluation"
    })
except Exception as err:
    RESULT.update({"status":"FAILED_TO_EVALUATE","error":str(err),
                   "traceback_tail":traceback.format_exc()[-3000:]})
finally:
    OUTPUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(RESULT,indent=2,sort_keys=True))
if RESULT["status"]!="COMPLETED_EXPLORATORY":
    raise SystemExit(1)
