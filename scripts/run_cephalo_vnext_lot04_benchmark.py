#!/usr/bin/env python3
"""Cephalo vNext LOT04 immutable-manifest + untouched SRPose38 benchmark harness.

Certification harness only. It does not mutate product runtime or patient data.
"""
from __future__ import annotations
import argparse, ast, csv, hashlib, importlib.util, json, math, statistics, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
_PIPELINE_PATH=ROOT/"backend"/"services"/"srpose38_pipeline.py"
_spec=importlib.util.spec_from_file_location("lot04_srpose38_pipeline",_PIPELINE_PATH)
if _spec is None or _spec.loader is None: raise RuntimeError("cannot load frozen SRPose38 pipeline")
_pipeline=importlib.util.module_from_spec(_spec); sys.modules[_spec.name]=_pipeline; _spec.loader.exec_module(_pipeline)
prepare_srpose38_input=_pipeline.prepare_srpose38_input
decode_srpose38_heatmaps=_pipeline.decode_srpose38_heatmaps

from scripts.validate_cephalo_vnext_lot04_contract import (
    canonical_json_sha256, validate_manifest_semantics, validate_acceptance_semantics,
)

MODEL_SHA256="a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
MODEL_SIZE=267484931
CHECKPOINT_SHA256="fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc"
SOURCE_COMMIT="18d17d1934970016e7610c4849311900b8d1f191"
MAPPING_VERSION="LOT03_V1"
INDEX_TO_DC={
0:"S",1:"N",2:"Or",3:"Po",4:"A",5:"B",6:"Pog",7:"Me",8:"Gn",9:"Go",
10:"L1_incisal",11:"U1_incisal",12:"Ls_soft",13:"Li_soft",14:"Sn_soft",15:"Pog_soft",
16:"PNS",17:"ANS",18:"Ar",19:"D_point",20:"U1_apex",21:"L1_apex",22:"Cm",23:"Ptm",
24:"Co",25:"Prn",26:"Ba",27:"PT_point",28:"Bo",29:"Ls2",30:"Li2",31:"Gn_soft",
32:"Me_soft",33:"G_soft",34:"N_soft",35:"C_point",36:"U6",37:"L6",
}
AARIZ_TO_DC={
"A":"A","ANS":"ANS","B":"B","Me":"Me","N":"N","Or":"Or","Pog":"Pog","PNS":"PNS",
"Pn":"Prn","S":"S","Ar":"Ar","Co":"Co","Gn":"Gn","Go":"Go","Po":"Po","LIT":"L1_incisal",
"UIA":"U1_apex","UIT":"U1_incisal","LIA":"L1_apex","Li":"Li_soft","Ls":"Ls_soft",
"N\u0060":"N_soft","Pog\u0060":"Pog_soft","Sn":"Sn_soft",
}
DC_TO_AARIZ={v:k for k,v in AARIZ_TO_DC.items()}
def _runtime_mapping_from_source():
    tree=ast.parse((ROOT/"backend"/"services"/"sota_vision_service.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="SOTA_LANDMARKS_MAPPING" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("SOTA_LANDMARKS_MAPPING not found")
if INDEX_TO_DC != _runtime_mapping_from_source():
    raise RuntimeError("LOT04 benchmark mapping drifted from runtime SOTA_LANDMARKS_MAPPING")
SENTINELS=("SNA","SNB","ANB","FMA","IMPA","FMIA","SN-GoGn","Co-A","Co-Gn")
REQ={
"SNA":{"S","N","A"},"SNB":{"S","N","B"},"ANB":{"S","N","A","B"},
"FMA":{"Po","Or","Go","Me"},"IMPA":{"L1_apex","L1_incisal","Go","Me"},
"FMIA":{"L1_apex","L1_incisal","Po","Or"},"SN-GoGn":{"S","N","Go","Gn"},
"Co-A":{"Co","A"},"Co-Gn":{"Co","Gn"},
}

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def percentile(vals,p):
    s=sorted(vals); q=(len(s)-1)*p; lo=int(q); hi=min(lo+1,len(s)-1); w=q-lo
    return s[lo]*(1-w)+s[hi]*w

def summary(vals):
    if not vals: return None
    return {"n":len(vals),"mean":statistics.fmean(vals),"median":statistics.median(vals),
            "sd":statistics.pstdev(vals) if len(vals)>1 else 0.0,
            "p90":percentile(vals,.90),"p95":percentile(vals,.95),"max":max(vals)}

def git_head(repo:Path)->str:
    return subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()

def load_cal(path:Path):
    rows=list(csv.DictReader(path.open(encoding="utf-8-sig",newline="")))
    if len(rows)!=1000: raise SystemExit(f"expected 1000 calibration rows, got {len(rows)}")
    return {r["cephalogram_id"]:r for r in rows}

def make_session(model:Path):
    if model.stat().st_size!=MODEL_SIZE: raise SystemExit("model size mismatch")
    if sha256_file(model)!=MODEL_SHA256: raise SystemExit("model sha256 mismatch")
    sess=ort.InferenceSession(str(model),providers=["CPUExecutionProvider"])
    if sess.get_providers()[0]!="CPUExecutionProvider": raise SystemExit("unexpected execution provider")
    if len(sess.get_inputs())!=1 or len(sess.get_outputs())!=1: raise SystemExit("expected one input and output")
    return sess

def build_manifest(args):
    corpus=json.loads(args.corpus_manifest.read_text(encoding="utf-8"))
    policy=json.loads(args.tolerance_policy.read_text(encoding="utf-8"))
    cal=load_cal(args.calibration_csv)
    sess=make_session(args.model)
    inp,out=sess.get_inputs()[0],sess.get_outputs()[0]
    cases=[]; dev=[]; acc=[]
    for case in corpus["cases"]:
        cid=case["case_id"]; row=cal[cid]; split=case["split"]
        cases.append({"case_id":cid,"sha256":case["image"]["sha256"],"layer":"G2",
            "calibration_provenance":f"cephalogram_machine_mappings.csv|machine={row['machine']}|pixel_size={row['pixel_size']}"})
        (acc if split=="test" else dev).append(cid)
    manifest={
      "schema_version":"CEPHALO_LOT04_BENCHMARK_MANIFEST_V1",
      "candidate":{"model_name":args.model.name,"model_sha256":MODEL_SHA256,"model_size_bytes":MODEL_SIZE,
        "checkpoint_sha256":CHECKPOINT_SHA256,"source_commit":SOURCE_COMMIT,
        "preprocessing_commit":git_head(args.repo),"provider":"CPUExecutionProvider","output_count":38,
        "index_mapping_version":MAPPING_VERSION},
      "environment":{"python":sys.version.split()[0],"numpy":np.__version__,"onnxruntime":ort.__version__,"opencv":cv2.__version__},
      "onnx_interface":{"input_name":inp.name,"input_dtype":inp.type,"input_shape":list(inp.shape),
        "output_name":out.name,"output_dtype":out.type,"output_shape":list(out.shape)},
      "preprocessing":{"input_size":[1024,1024],"bbox_padding":1.25,"interpolation":"cv2.INTER_LINEAR",
        "color_conversion":"BGR_TO_RGB","mean":[121.25,121.25,121.25],"std":[76.5,76.5,76.5],
        "tta_embedded_in_onnx":True,"darkpose_blur_kernel":11},
      "dataset":{"manifest_frozen_before_scoring":True,"source_manifest_sha256":sha256_file(args.corpus_manifest),
        "qc_sha256":sha256_file(args.qc),"calibration_sha256":sha256_file(args.calibration_csv),
        "landmark_agreement_sha256":sha256_file(args.landmark_agreement),
        "measurement_agreement_sha256":sha256_file(args.measurement_agreement),
        "split_policy":"train+valid=development;test=acceptance","cases":cases,
        "development_case_ids":dev,"acceptance_case_ids":acc},
      "metrics":{"per_landmark_mm":True,"directional_xy":True,"robust_percentiles":True,
        "failure_rate":True,"sdr_secondary":True,"clinical_propagation":list(SENTINELS)},
      "acceptance_policy":{"preregistered":True,"universal_2mm_gate":False,
        "human_reference_uncertainty_required":True,"landmark_specific":True,
        "aggregate_regression_masking_forbidden":True,"tolerance_version":policy["policy_id"],
        "policy_sha256":sha256_file(args.tolerance_policy),
        "landmark_tolerances":policy["landmark_tolerances"],"clinical_tolerances":policy["clinical_tolerances"]},
    }
    validate_manifest_semantics(manifest)
    args.output.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"manifest_sha256":canonical_json_sha256(manifest),"acceptance_cases":len(acc),
                      "development_cases":len(dev),"output":str(args.output)},sort_keys=True))

def vec(a,b): return (b[0]-a[0],b[1]-a[1])
def vang(u,v):
    nu,nv=math.hypot(*u),math.hypot(*v)
    if nu==0 or nv==0: raise ValueError("degenerate geometry")
    d=max(-1.0,min(1.0,(u[0]*v[0]+u[1]*v[1])/(nu*nv)))
    return math.degrees(math.acos(d))
def angle3(a,b,c): return vang(vec(b,a),vec(b,c))
def lineang(a,b,c,d):
    x=vang(vec(a,b),vec(c,d)); return min(x,180.0-x)
def measures(p,scale):
    sna=angle3(p["S"],p["N"],p["A"]); snb=angle3(p["S"],p["N"],p["B"])
    return {"SNA":sna,"SNB":snb,"ANB":sna-snb,
      "FMA":lineang(p["Po"],p["Or"],p["Go"],p["Me"]),
      "IMPA":lineang(p["L1_apex"],p["L1_incisal"],p["Go"],p["Me"]),
      "FMIA":lineang(p["L1_apex"],p["L1_incisal"],p["Po"],p["Or"]),
      "SN-GoGn":lineang(p["S"],p["N"],p["Go"],p["Gn"]),
      "Co-A":math.dist(p["Co"],p["A"])*scale,"Co-Gn":math.dist(p["Co"],p["Gn"])*scale}

def score(args):
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest_semantics(manifest)
    if manifest["candidate"]["model_sha256"]!=MODEL_SHA256: raise SystemExit("manifest/model identity mismatch")
    if manifest["candidate"]["preprocessing_commit"]!=git_head(args.repo): raise SystemExit("repo HEAD drift since manifest freeze")
    if sha256_file(args.model)!=MODEL_SHA256: raise SystemExit("model drift since manifest freeze")
    corpus=json.loads(args.corpus_manifest.read_text(encoding="utf-8"))
    qc=json.loads(args.qc.read_text(encoding="utf-8")); cal=load_cal(args.calibration_csv)
    bindings={
      "source_manifest_sha256":sha256_file(args.corpus_manifest),
      "qc_sha256":sha256_file(args.qc),
      "calibration_sha256":sha256_file(args.calibration_csv),
      "landmark_agreement_sha256":sha256_file(args.landmark_agreement),
      "measurement_agreement_sha256":sha256_file(args.measurement_agreement),
    }
    for key,value in bindings.items():
        if manifest["dataset"].get(key)!=value: raise SystemExit(f"{key} drift since manifest freeze")
    if manifest["acceptance_policy"].get("policy_sha256")!=sha256_file(args.tolerance_policy):
        raise SystemExit("tolerance policy drift since manifest freeze")
    acceptance=set(manifest["dataset"]["acceptance_case_ids"])
    cases={c["case_id"]:c for c in corpus["cases"] if c["case_id"] in acceptance}
    if set(cases)!=acceptance: raise SystemExit("acceptance case mismatch")
    q={(x["case_id"],x["landmark"]):x for x in qc["pairs"]}
    sess=make_session(args.model); input_name=sess.get_inputs()[0].name
    tol_l={x["landmark_id"]:x for x in manifest["acceptance_policy"]["landmark_tolerances"]}
    tol_c={x["measurement_id"]:x for x in manifest["acceptance_policy"]["clinical_tolerances"]}
    errs=defaultdict(list); dxs=defaultdict(list); dys=defaultdict(list); fail=defaultdict(int); denom=defaultdict(int)
    bydev=defaultdict(lambda:defaultdict(list)); predictions=[]; latencies=[]; unresolved=defaultdict(lambda:defaultdict(int))
    pred_case={}; ref_case={}
    for cid in sorted(acceptance):
        case=cases[cid]; row=cal[cid]; scale=float(row["pixel_size"])
        image_path=args.dataset_root / case["image"]["path"]; image=cv2.imread(str(image_path),cv2.IMREAD_COLOR)
        if image is None: raise SystemExit(f"unreadable image {cid}")
        start=time.perf_counter()
        tensor,geom=prepare_srpose38_input(image)
        encoded=sess.run(None,{input_name:tensor})[0]
        coords,scores=decode_srpose38_heatmaps(encoded,geom)
        latencies.append(time.perf_counter()-start)
        pred={INDEX_TO_DC[i]:(float(x),float(y)) for i,(x,y) in enumerate(coords)}
        valid={k:(math.isfinite(x) and math.isfinite(y) and 0<=x<image.shape[1] and 0<=y<image.shape[0])
               for k,(x,y) in pred.items()}
        pred_case[cid]=pred
        refs={}
        for aariz,dc in AARIZ_TO_DC.items():
            qr=q[(cid,aariz)]; unresolved[dc][qr["status"]]+=1
            if qr["status"]!="CONSENSUS_CANDIDATE": continue
            denom[dc]+=1; rr=qr["reference"]; refs[dc]=(float(rr["x"]),float(rr["y"]))
            if not valid.get(dc,False):
                fail[dc]+=1; continue
            px,py=pred[dc]; rx,ry=refs[dc]; dx=(px-rx)*scale; dy=(py-ry)*scale
            e=math.hypot(dx,dy); errs[dc].append(e); dxs[dc].append(dx); dys[dc].append(dy); bydev[dc][row["machine"]].append(e)
        ref_case[cid]=refs
        predictions.append({"case_id":cid,"machine":row["machine"],"pixel_size":scale,
          "latency_s":latencies[-1],"coordinates":{k:[v[0],v[1]] for k,v in pred.items()},
          "valid_in_frame":valid,"scores":{INDEX_TO_DC[i]:float(scores[i]) for i in range(38)}})
    lm_results={}; lm_accept=[]
    for dc,tol in sorted(tol_l.items()):
        den=denom[dc]; er=errs[dc]; fr=(fail[dc]/den if den else 1.0); s=summary(er)
        if not s: decision="INSUFFICIENT_EVIDENCE"
        else: decision="PASS" if s["median"]<=tol["max_median_mm"] and s["p95"]<=tol["max_p95_mm"] and fr<=tol["max_failure_rate"] else "FAIL"
        lm_results[dc]={"eligible_n":den,"valid_n":len(er),"failure_count":fail[dc],"failure_rate":fr,
          "error_mm":s,"signed_x_mm":summary(dxs[dc]),"signed_y_mm":summary(dys[dc]),
          "by_device":{d:summary(v) for d,v in sorted(bydev[dc].items())},
          "reference_status_counts":dict(unresolved[dc]),"decision":decision}
        lm_accept.append({"landmark_id":dc,"status":"VALIDATION_REQUIRED","n":den,
          "median_mm":None if not s else s["median"],"p95_mm":None if not s else s["p95"],
          "failure_rate":fr,"human_reference_uncertainty_mm":tol["max_p95_mm"],
          "tolerance_version":manifest["acceptance_policy"]["tolerance_version"],"decision":decision})
    clinical_results={}; clinical_accept=[]
    for mid in SENTINELS:
        signed=[]; absolute=[]; not_comp=0
        for cid in sorted(acceptance):
            if not REQ[mid] <= set(ref_case[cid]): continue
            if not all(0<=pred_case[cid][k][0]<cases[cid]["image"]["width"] and 0<=pred_case[cid][k][1]<cases[cid]["image"]["height"] for k in REQ[mid]):
                not_comp+=1; continue
            try:
                pm=measures(pred_case[cid],float(cal[cid]["pixel_size"]))[mid]
                rm=measures(ref_case[cid],float(cal[cid]["pixel_size"]))[mid]
            except Exception:
                not_comp+=1; continue
            signed.append(pm-rm); absolute.append(abs(pm-rm))
        tol=tol_c[mid]; s=summary(absolute); bias=statistics.fmean(signed) if signed else None
        if not s: decision="INSUFFICIENT_EVIDENCE"
        elif not_comp: decision="FAIL"
        else: decision="PASS" if s["p95"]<=tol["max_absolute_error"] else "FAIL"
        clinical_results[mid]={"valid_n":len(absolute),"not_computable_count":not_comp,
          "signed_bias":bias,"absolute_error":s,"decision":decision}
        clinical_accept.append({"measurement_id":mid,"n":len(absolute),"signed_bias":bias,
          "absolute_error":None if not s else s["p95"],"decision":decision})
    decisions=[x["decision"] for x in lm_accept+clinical_accept]
    if all(d=="PASS" for d in decisions): overall="PASS"
    elif "FAIL" in decisions: overall="FAIL"
    else: overall="INSUFFICIENT_EVIDENCE"
    evidence={"schema":"CEPHALO_LOT04_BENCHMARK_RESULTS_V1","manifest_sha256":canonical_json_sha256(manifest),
      "candidate_model_sha256":MODEL_SHA256,"acceptance_cases":len(acceptance),
      "latency_seconds":summary(latencies),"landmarks":lm_results,"clinical_measurements":clinical_results,
      "predictions":predictions,"overall_decision":overall}
    acceptance_record={"schema_version":"CEPHALO_LOT04_ACCEPTANCE_RECORD_V1",
      "manifest_sha256":canonical_json_sha256(manifest),"candidate_model_sha256":MODEL_SHA256,
      "executed_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"landmarks":lm_accept,
      "clinical_measurements":clinical_accept,"overall_decision":overall,
      "decision_reasons":["REFERENCE_EQUIVALENCE_V1 applied without post-result retuning",
                          "Only anatomy-compatible Aariz mappings were scored",
                          "Later human-review and clinical-validation gates remain mandatory"]}
    validate_acceptance_semantics(acceptance_record,manifest)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"cephalo_vnext_lot04_results.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.output_dir/"cephalo_vnext_lot04_acceptance_record.json").write_text(json.dumps(acceptance_record,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"overall_decision":overall,"acceptance_cases":len(acceptance),
      "latency_p95_s":evidence["latency_seconds"]["p95"],
      "results_sha256":sha256_file(args.output_dir/"cephalo_vnext_lot04_results.json"),
      "acceptance_sha256":sha256_file(args.output_dir/"cephalo_vnext_lot04_acceptance_record.json")},sort_keys=True))

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    m=sub.add_parser("manifest")
    for p in ("corpus_manifest","qc","calibration_csv","landmark_agreement","measurement_agreement","model","tolerance_policy","repo","output"): m.add_argument(f"--{p.replace('_','-')}",type=Path,required=True)
    s=sub.add_parser("score")
    for p in ("manifest","corpus_manifest","qc","calibration_csv","landmark_agreement","measurement_agreement","tolerance_policy","dataset_root","model","repo","output_dir"): s.add_argument(f"--{p.replace('_','-')}",type=Path,required=True)
    a=ap.parse_args(); build_manifest(a) if a.cmd=="manifest" else score(a)
if __name__=="__main__": main()
