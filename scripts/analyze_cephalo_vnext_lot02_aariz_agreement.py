#!/usr/bin/env python3
"""Compute junior/senior landmark disagreement from a LOT02 Aariz manifest."""
from __future__ import annotations
import argparse, json, math, statistics
from collections import defaultdict
from pathlib import Path

def _key(item, idx):
    return item.get("symbol") or item.get("raw_id") or f"index:{idx}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    by=defaultdict(list); xy=defaultdict(lambda:{"dx":[],"dy":[]})
    for case in m["cases"]:
        j=case["junior"]["landmarks"]; s=case["senior"]["landmarks"]
        if len(j)!=29 or len(s)!=29: raise SystemExit("annotation cardinality != 29")
        for i,(jp,sp) in enumerate(zip(j,s)):
            kj,ks=_key(jp,i),_key(sp,i)
            if kj!=ks: raise SystemExit(f"annotation identity mismatch {case['case_id']} index {i}: {kj} != {ks}")
            dx=float(jp["x"])-float(sp["x"]); dy=float(jp["y"])-float(sp["y"])
            d=math.hypot(dx,dy)
            by[kj].append(d); xy[kj]["dx"].append(dx); xy[kj]["dy"].append(dy)
    out={"schema":"CEPHALO_LOT02_AARIZ_AGREEMENT_V1","cases":len(m["cases"]),"landmarks":{}}
    for k,vals in sorted(by.items()):
        sv=sorted(vals)
        def pct(p):
            if not sv: return None
            q=(len(sv)-1)*p; lo=int(q); hi=min(lo+1,len(sv)-1); w=q-lo
            return sv[lo]*(1-w)+sv[hi]*w
        out["landmarks"][k]={
            "n":len(vals),"mean_px":statistics.fmean(vals),"median_px":statistics.median(vals),
            "p90_px":pct(.90),"p95_px":pct(.95),"max_px":max(vals),
            "mean_dx_px":statistics.fmean(xy[k]["dx"]),"mean_dy_px":statistics.fmean(xy[k]["dy"]),
        }
    if len(out["landmarks"])!=29: raise SystemExit(f"expected 29 landmark identities, got {len(out['landmarks'])}")
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"cases":out["cases"],"landmarks":len(out["landmarks"])},sort_keys=True))
if __name__=="__main__": main()
