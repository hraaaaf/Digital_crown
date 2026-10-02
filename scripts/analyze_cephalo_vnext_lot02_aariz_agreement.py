#!/usr/bin/env python3
"""Compute junior/senior landmark disagreement from a LOT02 Aariz manifest."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

def _key(item, idx):
    return item.get("symbol") or item.get("raw_id") or f"index:{idx}"

def _load_calibration(path: Path):
    out={}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            cid=row["cephalogram_id"].strip()
            size=float(row["pixel_size"])
            if not math.isfinite(size) or size <= 0:
                raise SystemExit(f"invalid pixel_size for {cid}")
            if cid in out:
                raise SystemExit(f"duplicate calibration for {cid}")
            machine=row["machine"].strip()
            if not machine:
                raise SystemExit(f"missing machine for {cid}")
            out[cid]={"pixel_size":size,"machine":machine}
    if len(out)!=1000:
        raise SystemExit(f"expected 1000 calibration rows, got {len(out)}")
    return out

def _summary(vals):
    sv=sorted(vals)
    def pct(p):
        q=(len(sv)-1)*p
        lo=int(q)
        hi=min(lo+1,len(sv)-1)
        w=q-lo
        return sv[lo]*(1-w)+sv[hi]*w
    return {
        "n":len(vals),
        "mean":statistics.fmean(vals),
        "median":statistics.median(vals),
        "sd":statistics.pstdev(vals),
        "p90":pct(.90),
        "p95":pct(.95),
        "max":max(vals),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--calibration-csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()

    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    calibration=_load_calibration(a.calibration_csv)
    case_ids={c["case_id"] for c in m["cases"]}
    if set(calibration)!=case_ids:
        missing=sorted(case_ids-set(calibration))
        extra=sorted(set(calibration)-case_ids)
        raise SystemExit(f"calibration/manifest mismatch missing={missing[:3]} extra={extra[:3]}")

    by_px=defaultdict(list)
    by_mm=defaultdict(list)
    dx_px=defaultdict(list)
    dy_px=defaultdict(list)
    dx_mm=defaultdict(list)
    dy_mm=defaultdict(list)
    by_device=defaultdict(lambda:defaultdict(list))

    for case in m["cases"]:
        info=calibration[case["case_id"]]
        scale=info["pixel_size"]
        machine=info["machine"]
        j=case["junior"]["landmarks"]
        s=case["senior"]["landmarks"]
        if len(j)!=29 or len(s)!=29:
            raise SystemExit("annotation cardinality != 29")
        for i,(jp,sp) in enumerate(zip(j,s)):
            kj,ks=_key(jp,i),_key(sp,i)
            if kj!=ks:
                raise SystemExit(f"annotation identity mismatch {case['case_id']} index {i}: {kj} != {ks}")
            dx=float(jp["x"])-float(sp["x"])
            dy=float(jp["y"])-float(sp["y"])
            d=math.hypot(dx,dy)
            by_px[kj].append(d)
            by_mm[kj].append(d*scale)
            dx_px[kj].append(dx)
            dy_px[kj].append(dy)
            dx_mm[kj].append(dx*scale)
            dy_mm[kj].append(dy*scale)
            by_device[machine][kj].append(d*scale)

    out={
        "schema":"CEPHALO_LOT02_AARIZ_AGREEMENT_V3",
        "cases":len(m["cases"]),
        "calibration":{"source":a.calibration_csv.name,"rows":len(calibration),"unit":"mm_per_pixel"},
        "landmarks":{},
        "by_device":{},
    }

    for k in sorted(by_px):
        p=_summary(by_px[k])
        mm=_summary(by_mm[k])
        out["landmarks"][k]={
            "n":p["n"],
            "mean_px":p["mean"],
            "median_px":p["median"],
            "sd_px":p["sd"],
            "p90_px":p["p90"],
            "p95_px":p["p95"],
            "max_px":p["max"],
            "mean_dx_px":statistics.fmean(dx_px[k]),
            "mean_dy_px":statistics.fmean(dy_px[k]),
            "sd_dx_px":statistics.pstdev(dx_px[k]),
            "sd_dy_px":statistics.pstdev(dy_px[k]),
            "mean_mm":mm["mean"],
            "median_mm":mm["median"],
            "sd_mm":mm["sd"],
            "p90_mm":mm["p90"],
            "p95_mm":mm["p95"],
            "max_mm":mm["max"],
            "mean_dx_mm":statistics.fmean(dx_mm[k]),
            "mean_dy_mm":statistics.fmean(dy_mm[k]),
            "sd_dx_mm":statistics.pstdev(dx_mm[k]),
            "sd_dy_mm":statistics.pstdev(dy_mm[k]),
        }

    for machine in sorted(by_device):
        out["by_device"][machine]={k:_summary(v) for k,v in sorted(by_device[machine].items())}

    if len(out["landmarks"])!=29:
        raise SystemExit(f"expected 29 landmark identities, got {len(out['landmarks'])}")

    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"cases":out["cases"],"landmarks":len(out["landmarks"]),"calibrations":len(calibration)},sort_keys=True))

if __name__=="__main__":
    main()
