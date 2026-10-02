#!/usr/bin/env python3
"""Deterministic QC/adjudication triage for Aariz junior/senior landmark pairs.

2 mm / 4 mm are QC triage bands only. They are not clinical acceptance limits.
Only CONSENSUS_CANDIDATE pairs may receive an automatic midpoint reference.
"""
from __future__ import annotations
import argparse, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path

CONSENSUS_MM=2.0
ADJUDICATION_MM=4.0

def classify_pair(jx,jy,sx,sy,width,height,pixel_size):
    vals=(jx,jy,sx,sy,width,height,pixel_size)
    if not all(isinstance(v,(int,float)) and math.isfinite(float(v)) for v in vals):
        return "STRUCTURAL_INVALID", None
    if width<=0 or height<=0 or pixel_size<=0:
        return "STRUCTURAL_INVALID", None
    if jx<=0 or jy<=0 or sx<=0 or sy<=0:
        return "STRUCTURAL_INVALID", None
    if jx>width or sx>width or jy>height or sy>height:
        return "STRUCTURAL_INVALID", None
    d=math.hypot(float(jx)-float(sx),float(jy)-float(sy))*float(pixel_size)
    if d<=CONSENSUS_MM:
        return "CONSENSUS_CANDIDATE", d
    if d<=ADJUDICATION_MM:
        return "REVIEW_REQUIRED", d
    return "ADJUDICATION_REQUIRED", d

def load_calibration(path):
    out={}
    with path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid=row["cephalogram_id"].strip(); px=float(row["pixel_size"])
            if cid in out: raise SystemExit(f"duplicate calibration: {cid}")
            out[cid]=px
    if len(out)!=1000: raise SystemExit(f"expected 1000 calibrations, got {len(out)}")
    return out

def key(item,idx):
    return item.get("symbol") or item.get("raw_id") or f"index:{idx}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--calibration-csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    cal=load_calibration(a.calibration_csv)
    counts=Counter(); by_landmark=defaultdict(Counter); rows=[]
    for case in m["cases"]:
        image=case["image"]; width=image.get("width"); height=image.get("height")
        if width is None or height is None:
            raise SystemExit("manifest lacks image width/height; rebuild with current builder")
        cid=case["case_id"]; px=cal.get(cid)
        if px is None: raise SystemExit(f"missing calibration: {cid}")
        for i,(j,s) in enumerate(zip(case["junior"]["landmarks"],case["senior"]["landmarks"])):
            kj,ks=key(j,i),key(s,i)
            if kj!=ks: raise SystemExit(f"identity mismatch {cid}/{i}: {kj} != {ks}")
            status,d=classify_pair(j["x"],j["y"],s["x"],s["y"],width,height,px)
            counts[status]+=1; by_landmark[kj][status]+=1
            ref=None
            if status=="CONSENSUS_CANDIDATE":
                ref={"x":(float(j["x"])+float(s["x"]))/2.0,"y":(float(j["y"])+float(s["y"]))/2.0}
            rows.append({"case_id":cid,"split":case["split"],"landmark":kj,"status":status,
                         "disagreement_mm":d,"reference":ref})
    if sum(counts.values())!=29000: raise SystemExit(f"expected 29000 pairs, got {sum(counts.values())}")
    out={"schema":"CEPHALO_LOT02_AARIZ_QC_V1",
         "policy":{"consensus_max_mm":CONSENSUS_MM,"review_max_mm":ADJUDICATION_MM,
                   "clinical_acceptance":False,
                   "rule":"Only CONSENSUS_CANDIDATE gets an automatic midpoint; review/adjudication/invalid never do."},
         "counts":dict(sorted(counts.items())),
         "by_landmark":{k:dict(sorted(v.items())) for k,v in sorted(by_landmark.items())},
         "pairs":rows}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out["counts"],sort_keys=True))
if __name__=="__main__": main()
