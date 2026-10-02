#!/usr/bin/env python3
"""Compute junior/senior landmark disagreement from a LOT02 Aariz manifest."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

def _key(item, idx):
    return item.get("symbol") or item.get("raw_id") or f"index:{idx}"

def _load_pixel_sizes(path: Path) -> dict[str, float]:
    out={}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            cid=row["cephalogram_id"].strip()
            size=float(row["pixel_size"])
            if not math.isfinite(size) or size <= 0:
                raise SystemExit(f"invalid pixel_size for {cid}")
            if cid in out:
                raise SystemExit(f"duplicate calibration for {cid}")
            out[cid]=size
    if len(out)!=1000:
        raise SystemExit(f"expected 1000 calibration rows, got {len(out)}")
    return out

def _summary(vals):
    sv=sorted(vals)
    def pct(p):
        q=(len(sv)-1)*p; lo=int(q); hi=min(lo+1,len(sv)-1); w=q-lo
        return sv[lo]*(1-w)+sv[hi]*w
    return {
        "n":len(vals),"mean":statistics.fmean(vals),"median":statistics.median(vals),
        "p90":pct(.90),"p95":pct(.95),"max":max(vals),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--calibration-csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    pixel_sizes=_load_pixel_sizes(a.calibration_csv)
    case_ids={c["case_id"] for c in m["cases"]}
    if set(pixel_sizes)!=case_ids:
        missing=sorted(case_ids-set(pixel_sizes)); extra=sorted(set(pixel_sizes)-case_ids)
        raise SystemExit(f"calibration/manifest mismatch missing={missing[:3]} extra={extra[:3]}")
    by_px=defaultdict(list); by_mm=defaultdict(list)
    dx_px=defaultdict(list); dy_px=defaultdict(list); dx_mm=defaultdict(list); dy_mm=defaultdict(list)
    for case in m["cases"]:
        scale=pixel_sizes[case["case_id"]]
        j=case["junior"]["landmarks"]; s=case["senior"]["landmarks"]
        if len(j)!=29 or len(s)!=29: raise SystemExit("annotation cardinality != 29")
        for i,(jp,sp) in enumerate(zip(j,s)):
            kj,ks=_key(jp,i),_key(sp,i)
            if kj!=ks: raise SystemExit(f"annotation identity mismatch {case['case_id']} index {i}: {kj} != {ks}")
            dx=float(jp["x"])-float(sp["x"]); dy=float(jp["y"])-float(sp["y"]); d=math.hypot(dx,dy)
            by_px[kj].append(d); by_mm[kj].append(d*scale)
            dx_px[kj].append(dx); dy_px[kj].append(dy); dx_mm[kj].append(dx*scale); dy_mm[kj].append(dy*scale)
    out={"schema":"CEPHALO_LOT02_AARIZ_AGREEMENT_V2","cases":len(m["cases"]),
         "calibration":{"source":a.calibration_csv.name,"rows":len(pixel_sizes),"unit":"mm_per_pixel"},
         "landmarks":{}}
    for k in sorted(by_px):
        p=_summary(by_px[k]); mm=_summary(by_mm[k])
        out["landmarks"][k]={
            "n":p["n"],
            "mean_px":p["mean"],"median_px":p["median"],"p90_px":p["p90"],"p95_px":p["p95"],"max_px":p["max"],
            "mean_dx_px":statistics.fmean(dx_px[k]),"mean_dy_px":statistics.fmean(dy_px[k]),
            "mean_mm":mm["mean"],"median_mm":mm["median"],"p90_mm":mm["p90"],"p95_mm":mm["p95"],"max_mm":mm["max"],
            "mean_dx_mm":statistics.fmean(dx_mm[k]),"mean_dy_mm":statistics.fmean(dy_mm[k]),
        }
    if len(out["landmarks"])!=29: raise SystemExit(f"expected 29 landmark identities, got {len(out['landmarks'])}")
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"cases":out["cases"],"landmarks":len(out["landmarks"]),"calibrations":len(pixel_sizes)},sort_keys=True))
if __name__=="__main__": main()
