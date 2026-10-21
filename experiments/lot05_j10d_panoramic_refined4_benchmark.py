#!/usr/bin/env python3
"""Research-only 4-class alternative YOLO benchmark on SAME DENTEX films.

The source weight repo declares CC-BY-NC-SA-4.0. No commercial use
or clinical deployment. Benchmark dataset/source-image overlap unknown.
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

REPO = "chemahc94/caries-detection-weights"
WEIGHT = "best_refined.pt"
OUT = Path(os.getenv("LOT05_REFINED4_REPORT", "lot05-refined4-research.json"))
CONFIDENCES=(0.10,0.25,0.45)
# DENTEX official: impacted, caries, periapical, deep caries
NAMES=["Impacted","Caries","Periapical Lesion","Deep Caries"]
RESULT={
 "mission":"LOT05/05.7-J10D",
 "research_only":True,
 "clinical_acceptance":False,
 "source":REPO,
 "filename":WEIGHT,
 "license":"cc-by-nc-sa-4.0",
 "dataset":"tirandazdylan/dentex-panoramic",
 "split":"test",
 "images_requested":74,
 "training_overlap_unknown":True,
 "match_iou":0.5,
 "thresholds":CONFIDENCES,
 "status":"PENDING",
}

def overlap(a,b):
    w=max(0.,min(a[2],b[2])-max(a[0],b[0]))
    h=max(0.,min(a[3],b[3])-max(a[1],b[1]))
    c=w*h
    aa=max(0.,a[2]-a[0])*max(0.,a[3]-a[1])
    bb=max(0.,b[2]-b[0])*max(0.,b[3]-b[1])
    return c/max(aa+bb-c,1e-9)

def gt_objects(row):
    obj=row["objects"]
    boxes=obj["bbox"] if isinstance(obj,dict) else [v["bbox"] for v in obj]
    labels=obj["diagnosis"] if isinstance(obj,dict) else [v["diagnosis"] for v in obj]
    result=[]
    for rect,k in zip(boxes,labels):
        x,y,w,h=[float(z) for z in rect]
        k=int(k)
        if k not in (0,1,2,3):raise ValueError(f"unknown label {k}")
        result.append((k,[x,y,x+w,y+h]))
    return result

def score(gt,preds,conf):
    counts=[{"tp":0,"fp":0,"fn":0,"gt":0} for _ in NAMES]
    used=set()
    for cls,_ in gt:counts[cls]["gt"]+=1
    for cls,p,rect in preds:
        if p<conf:continue
        candidates=[(j,overlap(rect,b)) for j,(actual,b) in enumerate(gt)
                    if j not in used and actual==cls]
        if candidates:
            index,iou=max(candidates,key=lambda t:t[1])
            if iou>=0.5:
                used.add(index)
                counts[cls]["tp"]+=1
                continue
        counts[cls]["fp"]+=1
    for j,(k,b) in enumerate(gt):
        if j not in used:counts[k]["fn"]+=1
    return counts

try:
    commit=str(HfApi().model_info(REPO).sha)
    if len(commit)!=40:raise ValueError("source revision not pinned")
    source=Path(hf_hub_download(REPO,WEIGHT,revision=commit))
    filesize=source.stat().st_size
    if not 1_000_000<filesize<120_000_000:
        raise ValueError(f"unexpected source weights size {filesize}")
    h=hashlib.sha256()
    with source.open("rb") as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b""):
            h.update(chunk)
    RESULT.update({"source_commit":commit,"source_sha256":h.hexdigest(),
                   "source_bytes":filesize})
    model=YOLO(str(source),task="detect")
    raw_names=[str(model.names[k]) for k in sorted(model.names)]
    RESULT["observed_classes"]=raw_names
    if [x.lower() for x in raw_names]!=[x.lower() for x in NAMES]:
        raise RuntimeError("Different class ontology: "+repr(raw_names))
    agg={str(t):[{"tp":0,"fp":0,"fn":0,"gt":0} for _ in NAMES] for t in CONFIDENCES}
    durations=[]
    n=0
    for row in load_dataset("tirandazdylan/dentex-panoramic","diagnosis",
                            split="test",streaming=True):
        gt=gt_objects(row)
        start=time.perf_counter()
        r=model.predict(row["image"].convert("RGB"),imgsz=1280,
                        conf=0.10,iou=0.5,device="cpu",verbose=False)[0]
        durations.append(time.perf_counter()-start)
        preds=sorted(((int(k),float(p),[float(z) for z in rect])
                     for k,p,rect in zip(r.boxes.cls.tolist(),r.boxes.conf.tolist(),
                                         r.boxes.xyxy.tolist())),key=lambda z:z[1],reverse=True)
        for t in CONFIDENCES:
            cases=score(gt,preds,t)
            for i,c in enumerate(cases):
                for metric,val in c.items():agg[str(t)][i][metric]+=val
        n+=1
        if n==74:break
    if n!=74:raise ValueError("not 74 DENTEX cases")
    by_t={}
    for t,counts in agg.items():
        per_class={}
        for name,c in zip(NAMES,counts):
            d=c.copy()
            d["precision"]=c["tp"]/(c["tp"]+c["fp"]) if c["tp"]+c["fp"] else None
            d["recall"]=c["tp"]/(c["tp"]+c["fn"]) if c["tp"]+c["fn"] else None
            per_class[name]=d
        tp=sum(x["tp"] for x in counts)
        fp=sum(x["fp"] for x in counts)
        fn=sum(x["fn"] for x in counts)
        by_t[t]={"classes":per_class,"overall":{
            "tp":tp,"fp":fp,"fn":fn,
            "precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,
        }}
    RESULT.update({"status":"COMPLETED_EXPLORATORY","images":n,
                   "results":by_t,
                   "median_cpu_seconds":statistics.median(durations),
                   "limitations":"No independent split or licensing clearance, scientific reviewer missing."})
except Exception as err:
    RESULT.update({"status":"FAILED_TO_EVALUATE","error":str(err),
                   "traceback_tail":traceback.format_exc()[-2800:]})
finally:
    OUT.write_text(json.dumps(RESULT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(RESULT,indent=2,sort_keys=True))
if RESULT["status"]!="COMPLETED_EXPLORATORY":raise SystemExit(1)
