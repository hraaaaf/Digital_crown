#!/usr/bin/env python3
"""Recompute LOT04 acceptance from frozen untouched predictions without rerunning ONNX."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics,time
from pathlib import Path
from scripts.validate_cephalo_vnext_lot04_contract import canonical_json_sha256,validate_manifest_semantics,validate_acceptance_semantics

AARIZ_TO_DC={
"A":"A","ANS":"ANS","B":"B","Me":"Me","N":"N","Or":"Or","Pog":"Pog","PNS":"PNS",
"Pn":"Prn","S":"S","Ar":"Ar","Co":"Co","Gn":"Gn","Go":"Go","Po":"Po","LIT":"L1_incisal",
"UIA":"U1_apex","UIT":"U1_incisal","LIA":"L1_apex","Li":"Li_soft","Ls":"Ls_soft",
"N\u0060":"N_soft","Pog\u0060":"Pog_soft","Sn":"Sn_soft",
}
SENTINELS=("SNA","SNB","ANB","FMA","IMPA","FMIA","SN-GoGn","Co-A","Co-Gn")
REQ={
"SNA":{"S","N","A"},"SNB":{"S","N","B"},"ANB":{"S","N","A","B"},
"FMA":{"Po","Or","Go","Me"},"IMPA":{"L1_apex","L1_incisal","Go","Me"},
"FMIA":{"L1_apex","L1_incisal","Po","Or"},"SN-GoGn":{"S","N","Go","Gn"},
"Co-A":{"Co","A"},"Co-Gn":{"Co","Gn"},
}
def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def pct(vals,p):
 s=sorted(vals); q=(len(s)-1)*p; lo=int(q); hi=min(lo+1,len(s)-1); w=q-lo
 return s[lo]*(1-w)+s[hi]*w
def vec(a,b):return (b[0]-a[0],b[1]-a[1])
def vang(u,v):
 nu,nv=math.hypot(*u),math.hypot(*v)
 if nu==0 or nv==0:raise ValueError("degenerate geometry")
 d=max(-1.0,min(1.0,(u[0]*v[0]+u[1]*v[1])/(nu*nv)))
 return math.degrees(math.acos(d))
def angle3(a,b,c):return vang(vec(b,a),vec(b,c))
def lineang(a,b,c,d):
 x=vang(vec(a,b),vec(c,d));return min(x,180.0-x)
def measure_one(mid,p,scale):
 if mid=="SNA":return angle3(p["S"],p["N"],p["A"])
 if mid=="SNB":return angle3(p["S"],p["N"],p["B"])
 if mid=="ANB":return angle3(p["S"],p["N"],p["A"])-angle3(p["S"],p["N"],p["B"])
 if mid=="FMA":return lineang(p["Po"],p["Or"],p["Go"],p["Me"])
 if mid=="IMPA":return lineang(p["L1_apex"],p["L1_incisal"],p["Go"],p["Me"])
 if mid=="FMIA":return lineang(p["L1_apex"],p["L1_incisal"],p["Po"],p["Or"])
 if mid=="SN-GoGn":return lineang(p["S"],p["N"],p["Go"],p["Gn"])
 if mid=="Co-A":return math.dist(p["Co"],p["A"])*scale
 if mid=="Co-Gn":return math.dist(p["Co"],p["Gn"])*scale
 raise KeyError(mid)
def main():
 ap=argparse.ArgumentParser()
 for n in ("manifest","results","corpus_manifest","qc","calibration_csv","output"):ap.add_argument(f"--{n.replace('_','-')}",type=Path,required=True)
 a=ap.parse_args()
 manifest=json.loads(a.manifest.read_text(encoding="utf-8"));validate_manifest_semantics(manifest)
 results=json.loads(a.results.read_text(encoding="utf-8"))
 mh=canonical_json_sha256(manifest)
 if results["manifest_sha256"]!=mh:raise SystemExit("results/manifest binding mismatch")
 if results["candidate_model_sha256"]!=manifest["candidate"]["model_sha256"]:raise SystemExit("candidate binding mismatch")
 acceptance=set(manifest["dataset"]["acceptance_case_ids"])
 preds={x["case_id"]:x for x in results["predictions"]}
 if set(preds)!=acceptance:raise SystemExit("prediction case set mismatch")
 corpus=json.loads(a.corpus_manifest.read_text(encoding="utf-8"))
 cases={c["case_id"]:c for c in corpus["cases"] if c["case_id"] in acceptance}
 qc=json.loads(a.qc.read_text(encoding="utf-8"))
 q={(x["case_id"],x["landmark"]):x for x in qc["pairs"]}
 cal={r["cephalogram_id"]:float(r["pixel_size"]) for r in csv.DictReader(a.calibration_csv.open(encoding="utf-8-sig",newline=""))}
 policy=manifest["acceptance_policy"]; lt={x["landmark_id"]:x for x in policy["landmark_tolerances"]}; ct={x["measurement_id"]:x for x in policy["clinical_tolerances"]}
 landmarks=[]
 for dc,tol in sorted(lt.items()):
  m=results["landmarks"][dc]; s=m["error_mm"]; fr=m["failure_rate"]
  if not s:decision="INSUFFICIENT_EVIDENCE"
  else:decision="PASS" if s["median"]<=tol["max_median_mm"] and s["p95"]<=tol["max_p95_mm"] and fr<=tol["max_failure_rate"] else "FAIL"
  landmarks.append({"landmark_id":dc,"status":"VALIDATION_REQUIRED","n":m["eligible_n"],"median_mm":None if not s else s["median"],"p95_mm":None if not s else s["p95"],"failure_rate":fr,"human_reference_uncertainty_mm":tol["max_p95_mm"],"tolerance_version":policy["tolerance_version"],"decision":decision})
 clinical=[]; detail={}
 for mid in SENTINELS:
  signed=[];absvals=[];eligible=0;not_comp=0
  for cid in sorted(acceptance):
   refs={}
   ok=True
   for dc in REQ[mid]:
    aariz=next(k for k,v in AARIZ_TO_DC.items() if v==dc)
    qr=q[(cid,aariz)]
    if qr["status"]!="CONSENSUS_CANDIDATE":ok=False;break
    refs[dc]=(float(qr["reference"]["x"]),float(qr["reference"]["y"]))
   if not ok:continue
   eligible+=1
   pr=preds[cid]
   if not all(pr["valid_in_frame"].get(k,False) for k in REQ[mid]):not_comp+=1;continue
   pp={k:tuple(pr["coordinates"][k]) for k in REQ[mid]}
   try:
    pv=measure_one(mid,pp,cal[cid]);rv=measure_one(mid,refs,cal[cid])
   except Exception:
    not_comp+=1;continue
   e=pv-rv;signed.append(e);absvals.append(abs(e))
  tol=ct[mid]
  if not absvals:decision="INSUFFICIENT_EVIDENCE";p95=None;bias=None
  else:
   p95=pct(absvals,.95);bias=statistics.fmean(signed)
   decision="FAIL" if not_comp else ("PASS" if p95<=tol["max_absolute_error"] else "FAIL")
  detail[mid]={"eligible_n":eligible,"valid_n":len(absvals),"not_computable_count":not_comp,"p95_abs":p95,"signed_bias":bias,"tolerance":tol["max_absolute_error"],"decision":decision}
  clinical.append({"measurement_id":mid,"n":len(absvals),"signed_bias":bias,"absolute_error":p95,"decision":decision})
 decisions=[x["decision"] for x in landmarks+clinical]
 overall="PASS" if all(x=="PASS" for x in decisions) else ("FAIL" if "FAIL" in decisions else "INSUFFICIENT_EVIDENCE")
 record={"schema_version":"CEPHALO_LOT04_ACCEPTANCE_RECORD_V1","manifest_sha256":mh,"candidate_model_sha256":manifest["candidate"]["model_sha256"],"executed_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"landmarks":landmarks,"clinical_measurements":clinical,"overall_decision":overall,"decision_reasons":["REFERENCE_EQUIVALENCE_V1 applied without post-result retuning","Recomputed from frozen untouched predictions; no second ONNX inference","Each sentinel measurement uses only its own preregistered G1-A required landmarks"]}
 validate_acceptance_semantics(record,manifest)
 payload={"source_results_sha256":sha256_file(a.results),"record":record,"clinical_detail":detail}
 a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"overall_decision":overall,"source_results_sha256":payload["source_results_sha256"],"output_sha256":sha256_file(a.output),"clinical_n":{k:v["valid_n"] for k,v in detail.items()}},sort_keys=True))
if __name__=="__main__":main()
