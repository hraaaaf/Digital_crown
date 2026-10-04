#!/usr/bin/env python3
"""Reproducible Junior/Senior sentinel-measurement agreement for LOT02 Aariz."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path

SENTINELS=("SNA","SNB","ANB","FMA","IMPA","FMIA","SN-GoGn","Co-A","Co-Gn")
REQ={
"SNA":{"S","N","A"},"SNB":{"S","N","B"},"ANB":{"S","N","A","B"},
"FMA":{"Po","Or","Go","Me"},"IMPA":{"LIA","LIT","Go","Me"},
"FMIA":{"LIA","LIT","Po","Or"},"SN-GoGn":{"S","N","Go","Gn"},
"Co-A":{"Co","A"},"Co-Gn":{"Co","Gn"},
}

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _amap(case,role):
    return {p["symbol"]:(float(p["x"]),float(p["y"])) for p in case[role]["landmarks"]}

def _dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def _vang(u,v):
    nu,nv=math.hypot(*u),math.hypot(*v)
    if nu==0 or nv==0: raise ValueError("degenerate geometry")
    d=max(-1.0,min(1.0,(u[0]*v[0]+u[1]*v[1])/(nu*nv)))
    return math.degrees(math.acos(d))
def _angle3(a,b,c): return _vang((a[0]-b[0],a[1]-b[1]),(c[0]-b[0],c[1]-b[1]))
def _lineang(a,b,c,d):
    x=_vang((b[0]-a[0],b[1]-a[1]),(d[0]-c[0],d[1]-c[1]))
    return min(x,180.0-x)

def _measures(p,scale):
    sna=_angle3(p["S"],p["N"],p["A"]); snb=_angle3(p["S"],p["N"],p["B"])
    return {
      "SNA":sna,"SNB":snb,"ANB":sna-snb,
      "FMA":_lineang(p["Po"],p["Or"],p["Go"],p["Me"]),
      "IMPA":_lineang(p["LIA"],p["LIT"],p["Go"],p["Me"]),
      "FMIA":_lineang(p["LIA"],p["LIT"],p["Po"],p["Or"]),
      "SN-GoGn":_lineang(p["S"],p["N"],p["Go"],p["Gn"]),
      "Co-A":_dist(p["Co"],p["A"])*scale,
      "Co-Gn":_dist(p["Co"],p["Gn"])*scale,
    }

def _summary(vals):
    sv=sorted(vals)
    def pct(p):
        q=(len(sv)-1)*p; lo=int(q); hi=min(lo+1,len(sv)-1); w=q-lo
        return sv[lo]*(1-w)+sv[hi]*w
    return {"n":len(vals),"mean_abs":statistics.fmean(vals),"median_abs":statistics.median(vals),
            "p95_abs":pct(.95),"max_abs":max(vals)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--calibration-csv",type=Path,required=True)
    ap.add_argument("--qc",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    q=json.loads(a.qc.read_text(encoding="utf-8"))
    cal={r["cephalogram_id"]:float(r["pixel_size"]) for r in csv.DictReader(a.calibration_csv.open(encoding="utf-8-sig",newline=""))}
    if len(cal)!=1000: raise SystemExit(f"expected 1000 calibrations, got {len(cal)}")
    qc={(x["case_id"],x["landmark"]):x["status"] for x in q["pairs"]}
    all_err={k:[] for k in SENTINELS}; consensus_err={k:[] for k in SENTINELS}; failures=[]
    for case in m["cases"]:
        cid=case["case_id"]
        try:
            jm,sm=_measures(_amap(case,"junior"),cal[cid]),_measures(_amap(case,"senior"),cal[cid])
        except Exception as exc:
            failures.append({"case_id":cid,"error":type(exc).__name__})
            continue
        for k in SENTINELS:
            e=abs(jm[k]-sm[k]); all_err[k].append(e)
            if all(qc.get((cid,lm))=="CONSENSUS_CANDIDATE" for lm in REQ[k]):
                consensus_err[k].append(e)
    out={"schema":"CEPHALO_LOT02_SENTINEL_MEASUREMENT_AGREEMENT_V2",
         "manifest_sha256":sha256(a.manifest),"qc_sha256":sha256(a.qc),
         "cases":len(m["cases"]),"failures":failures,
         "all_source":{k:_summary(v) for k,v in all_err.items()},
         "g1a_consensus_only":{k:_summary(v) for k,v in consensus_err.items()},
         "units":{k:("mm" if k in {"Co-A","Co-Gn"} else "deg") for k in SENTINELS},
         "policy":{"all_source_is_stress_context":True,"g1a_is_exact_reference_subset":True,
                   "clinical_acceptance":False,"no_threshold_retuning_to_candidate_model":True}}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"cases":out["cases"],"failures":len(failures),
                      "g1a_n":{k:out["g1a_consensus_only"][k]["n"] for k in SENTINELS}},sort_keys=True))
if __name__=="__main__": main()
