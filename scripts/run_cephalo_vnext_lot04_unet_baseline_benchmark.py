#!/usr/bin/env python3
"""LOT04 benchmark harness for the official CL-Detection2023 UNet baseline.

Certification-only. Two mandatory phases:
  1) manifest: freeze candidate/source/environment/dataset/policy before scoring.
  2) score: one untouched Aariz test pass, bound to the frozen manifest.

No product runtime or patient-data mutation.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math,statistics,subprocess,sys,time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from jsonschema import Draft202012Validator
from skimage import io as sk_io
from skimage import transform

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.validate_cephalo_vnext_lot04_contract import canonical_json_sha256,validate_manifest_semantics,validate_acceptance_semantics

CANDIDATE_ID="CLDETECTION2023_OFFICIAL_UNET_BASELINE"
SOURCE_REPO="szuboy/CL-Detection2023"
SOURCE_COMMIT="dc1ce2bd0a3f317de4160cde17e4a6f60371e67c"
WEIGHT_SHA256="b391e7925522185f993a88048ca7ace2d209ae0864116bdd255660f7a993eb71"
WEIGHT_SIZE=27354349
MODEL_PY_SHA256="2d8d8853b800af6579b4dd725850eb9d4c4b9849ebf405c493de9691b767dedc"
INFERENCE_PY_SHA256="650860cc5af8cdcd6339d3aa950b83c87b10bc9e0676e79ffe15344b5a494458"
MAPPING_VERSION="CL_DETECTION2023_POINTS_1_38__LOT03_V1"

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
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def git_head(repo:Path)->str:
    return subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()

def percentile(vals,p):
    s=sorted(vals); q=(len(s)-1)*p; lo=int(q); hi=min(lo+1,len(s)-1); w=q-lo
    return s[lo]*(1-w)+s[hi]*w

def summary(vals):
    if not vals:return None
    return {"n":len(vals),"mean":statistics.fmean(vals),"median":statistics.median(vals),
            "sd":statistics.pstdev(vals) if len(vals)>1 else 0.0,
            "p90":percentile(vals,.90),"p95":percentile(vals,.95),"max":max(vals)}

def load_cal(path:Path):
    rows=list(csv.DictReader(path.open(encoding="utf-8-sig",newline="")))
    if len(rows)!=1000:raise SystemExit(f"expected 1000 calibration rows, got {len(rows)}")
    return {r["cephalogram_id"]:r for r in rows}

def load_model_module(candidate_repo:Path):
    model_file=candidate_repo/"utils"/"model.py"
    if git_head(candidate_repo)!=SOURCE_COMMIT:raise SystemExit("candidate source HEAD mismatch")
    if sha256_file(model_file)!=MODEL_PY_SHA256:raise SystemExit("candidate model.py hash mismatch")
    if sha256_file(candidate_repo/"step3_test_and_visualize.py")!=INFERENCE_PY_SHA256:raise SystemExit("candidate inference source hash mismatch")
    spec=importlib.util.spec_from_file_location("cldetection2023_model",model_file)
    if spec is None or spec.loader is None:raise SystemExit("cannot load candidate model module")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def load_candidate(candidate_repo:Path,weights:Path):
    if weights.stat().st_size!=WEIGHT_SIZE:raise SystemExit("candidate weight size mismatch")
    if sha256_file(weights)!=WEIGHT_SHA256:raise SystemExit("candidate weight sha256 mismatch")
    module=load_model_module(candidate_repo)
    model=module.load_model(model_name="UNet")
    state=torch.load(str(weights),map_location="cpu")
    model.load_state_dict(state,strict=True)
    model.eval().cpu()
    with torch.no_grad():
        out=model(torch.zeros((1,3,512,512),dtype=torch.float32))
    if list(out.shape)!=[1,38,512,512]:raise SystemExit(f"unexpected candidate output shape {list(out.shape)}")
    return model

def validate_schema(payload:dict,schema_path:Path):
    schema=json.loads(schema_path.read_text(encoding="utf-8"))
    errors=sorted(Draft202012Validator(schema).iter_errors(payload),key=lambda e:list(e.path))
    if errors:raise SystemExit("schema validation failed: "+" | ".join(e.message for e in errors[:10]))

def manifest_cmd(a):
    corpus=json.loads(a.corpus_manifest.read_text(encoding="utf-8"))
    policy=json.loads(a.tolerance_policy.read_text(encoding="utf-8"))
    cal=load_cal(a.calibration_csv)
    model=load_candidate(a.candidate_repo,a.weights)
    del model
    cases=[];dev=[];acc=[]
    for case in corpus["cases"]:
        cid=case["case_id"]; row=cal[cid]; split=case["split"]
        cases.append({"case_id":cid,"sha256":case["image"]["sha256"],"layer":"G2",
                      "calibration_provenance":f"cephalogram_machine_mappings.csv|machine={row['machine']}|pixel_size={row['pixel_size']}"})
        (acc if split=="test" else dev).append(cid)
    payload={
      "schema_version":"CEPHALO_LOT04_CANDIDATE_BENCHMARK_MANIFEST_V1",
      "candidate":{
        "candidate_id":CANDIDATE_ID,"artifact_name":a.weights.name,
        "artifact_sha256":WEIGHT_SHA256,"model_sha256":WEIGHT_SHA256,"artifact_size_bytes":WEIGHT_SIZE,
        "source_repository":SOURCE_REPO,"source_commit":SOURCE_COMMIT,"source_license":"Apache-2.0",
        "weight_license_status":"EXTERNAL_CHECKPOINT_LICENSE_NOT_EXPLICITLY_SEPARATED_FROM_REPO_LICENSE",
        "framework":"PyTorch UNet","provider":"CPU","output_count":38,"index_mapping_version":MAPPING_VERSION,
        "source_model_file_sha256":MODEL_PY_SHA256,"source_inference_file_sha256":INFERENCE_PY_SHA256,
      },
      "environment":{
        "python":sys.version.split()[0],"torch":torch.__version__,"numpy":np.__version__,
        "skimage":__import__("skimage").__version__,"device":"cpu",
        "digital_crown_harness_commit":git_head(a.repo),
      },
      "preprocessing":{
        "input_size":[512,512],"resize_impl":"skimage.transform.resize","preserve_range":False,
        "channel_order":"RGB_HWC_TO_CHW","normalization":"NONE_BEYOND_SKIMAGE_PRESERVE_RANGE_FALSE",
        "decoder":"per-channel global max; all tied maxima averaged; x/y rescaled from 512x512 to original dimensions",
      },
      "dataset":{
        "manifest_frozen_before_scoring":True,"cases":cases,"development_case_ids":dev,"acceptance_case_ids":acc,
        "source_manifest_sha256":sha256_file(a.corpus_manifest),"qc_sha256":sha256_file(a.qc),
        "calibration_sha256":sha256_file(a.calibration_csv),
        "landmark_agreement_sha256":sha256_file(a.landmark_agreement),
        "measurement_agreement_sha256":sha256_file(a.measurement_agreement),
        "split_policy":"train+valid=development;test=acceptance",
      },
      "metrics":{"per_landmark_mm":True,"directional_xy":True,"robust_percentiles":True,"failure_rate":True,
                 "sdr_secondary":True,"clinical_propagation":list(SENTINELS),
                 "device_stratification":True},
      "acceptance_policy":{
        "policy_id":policy["policy_id"],"policy_sha256":sha256_file(a.tolerance_policy),
        "landmark_tolerances":policy["landmark_tolerances"],"clinical_tolerances":policy["clinical_tolerances"],
        "device_stratified_policy":policy["device_stratified_policy"],
      },
      "contamination":{
        "aariz_reference_found_in_frozen_source":False,
        "training_dataset_declared":"CL-Detection2023 challenge dataset",
        "external_patient_overlap_proven_absent":False,
        "note":"No Aariz/CEPHA29 reference found in the frozen official source. Undisclosed external cohort overlap cannot be independently proven absent.",
      },
    }
    validate_schema(payload,a.manifest_schema);validate_manifest_semantics(payload)
    a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"manifest_sha256":canonical_json_sha256(payload),"file_sha256":sha256_file(a.output),
                      "development_cases":len(dev),"acceptance_cases":len(acc)},sort_keys=True))

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

def score_cmd(a):
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    validate_schema(manifest,a.manifest_schema);validate_manifest_semantics(manifest)
    if manifest["environment"]["digital_crown_harness_commit"]!=git_head(a.repo):raise SystemExit("Digital Crown HEAD drift since manifest freeze")
    if manifest["candidate"]["source_commit"]!=git_head(a.candidate_repo):raise SystemExit("candidate repo HEAD drift since manifest freeze")
    if manifest["candidate"]["artifact_sha256"]!=sha256_file(a.weights):raise SystemExit("candidate weight drift since manifest freeze")
    bindings={
      "source_manifest_sha256":sha256_file(a.corpus_manifest),"qc_sha256":sha256_file(a.qc),
      "calibration_sha256":sha256_file(a.calibration_csv),"landmark_agreement_sha256":sha256_file(a.landmark_agreement),
      "measurement_agreement_sha256":sha256_file(a.measurement_agreement),
    }
    for k,v in bindings.items():
        if manifest["dataset"][k]!=v:raise SystemExit(f"{k} drift since manifest freeze")
    if manifest["acceptance_policy"]["policy_sha256"]!=sha256_file(a.tolerance_policy):raise SystemExit("policy drift since manifest freeze")

    model=load_candidate(a.candidate_repo,a.weights)
    corpus=json.loads(a.corpus_manifest.read_text(encoding="utf-8"))
    qc=json.loads(a.qc.read_text(encoding="utf-8"))
    agreement=json.loads(a.landmark_agreement.read_text(encoding="utf-8"))
    cal=load_cal(a.calibration_csv)
    acceptance=set(manifest["dataset"]["acceptance_case_ids"])
    cases={c["case_id"]:c for c in corpus["cases"] if c["case_id"] in acceptance}
    if set(cases)!=acceptance:raise SystemExit("acceptance case mismatch")
    q={(x["case_id"],x["landmark"]):x for x in qc["pairs"]}
    lt={x["landmark_id"]:x for x in manifest["acceptance_policy"]["landmark_tolerances"]}
    ct={x["measurement_id"]:x for x in manifest["acceptance_policy"]["clinical_tolerances"]}
    device_policy=manifest["acceptance_policy"]["device_stratified_policy"]

    errs=defaultdict(list);dxs=defaultdict(list);dys=defaultdict(list);fail=defaultdict(int);denom=defaultdict(int)
    bydev=defaultdict(lambda:defaultdict(list));status_counts=defaultdict(lambda:defaultdict(int))
    predictions=[];latencies=[];pred_case={};ref_case={}
    for cid in sorted(acceptance):
        case=cases[cid];row=cal[cid];scale=float(row["pixel_size"])
        path=a.dataset_root/case["image"]["path"];image=sk_io.imread(str(path))
        if image.ndim!=3 or image.shape[2]!=3:raise SystemExit(f"candidate expects RGB image: {cid} shape={image.shape}")
        h,w=image.shape[:2]
        resized=transform.resize(image,(512,512),mode="constant",preserve_range=False)
        tensor=torch.from_numpy(np.transpose(resized,(2,0,1))[None,:,:,:]).float()
        start=time.perf_counter()
        with torch.no_grad():heatmap=model(tensor)
        latencies.append(time.perf_counter()-start)
        hm=np.squeeze(heatmap.cpu().numpy())
        pred={};scores={}
        for i in range(38):
            ch=hm[i];yy,xx=np.where(ch==np.max(ch));x0=float(np.mean(xx))*w/512.0;y0=float(np.mean(yy))*h/512.0
            pred[INDEX_TO_DC[i]]=(x0,y0);scores[INDEX_TO_DC[i]]=float(np.max(ch))
        valid={k:(math.isfinite(x) and math.isfinite(y) and 0<=x<w and 0<=y<h) for k,(x,y) in pred.items()}
        pred_case[cid]=pred;refs={}
        for aariz,dc in AARIZ_TO_DC.items():
            qr=q[(cid,aariz)];status_counts[dc][qr["status"]]+=1
            if qr["status"]!="CONSENSUS_CANDIDATE":continue
            denom[dc]+=1;rr=qr["reference"];refs[dc]=(float(rr["x"]),float(rr["y"]))
            if not valid.get(dc,False):fail[dc]+=1;continue
            px,py=pred[dc];rx,ry=refs[dc];dx=(px-rx)*scale;dy=(py-ry)*scale;e=math.hypot(dx,dy)
            errs[dc].append(e);dxs[dc].append(dx);dys[dc].append(dy);bydev[dc][row["machine"]].append(e)
        ref_case[cid]=refs
        predictions.append({"case_id":cid,"machine":row["machine"],"pixel_size":scale,"latency_s":latencies[-1],
                            "coordinates":{k:[v[0],v[1]] for k,v in pred.items()},"valid_in_frame":valid,"scores":scores})

    landmark_results={};landmark_accept=[]
    for dc,tol in sorted(lt.items()):
        den=denom[dc];vals=errs[dc];fr=fail[dc]/den if den else 1.0;s=summary(vals)
        if not s:decision="INSUFFICIENT_EVIDENCE"
        else:decision="PASS" if s["median"]<=tol["max_median_mm"] and s["p95"]<=tol["max_p95_mm"] and fr<=tol["max_failure_rate"] else "FAIL"
        landmark_results[dc]={"eligible_n":den,"valid_n":len(vals),"failure_count":fail[dc],"failure_rate":fr,
                              "error_mm":s,"signed_x_mm":summary(dxs[dc]),"signed_y_mm":summary(dys[dc]),
                              "by_device":{d:summary(v) for d,v in sorted(bydev[dc].items())},
                              "reference_status_counts":dict(status_counts[dc]),"decision":decision}
        landmark_accept.append({"landmark_id":dc,"status":"VALIDATION_REQUIRED","n":den,
            "median_mm":None if not s else s["median"],"p95_mm":None if not s else s["p95"],"failure_rate":fr,
            "human_reference_uncertainty_mm":tol["max_p95_mm"],"tolerance_version":manifest["acceptance_policy"]["policy_id"],"decision":decision})

    device_strata=[]
    min_n=int(device_policy["min_n_for_hard_p95_gate"])
    for dc in sorted(lt):
        aariz=DC_TO_AARIZ[dc]
        for device,vals in sorted(bydev[dc].items()):
            n=len(vals);p95=percentile(vals,.95) if vals else None
            human=agreement["by_device"].get(device,{}).get(aariz)
            human_p95=None if human is None else human.get("p95")
            if n>=min_n:
                gate_status="HARD_GATE"
                if p95 is None or human_p95 is None:decision="INSUFFICIENT_EVIDENCE"
                else:decision="PASS" if p95<=human_p95 else "FAIL"
            else:
                gate_status="INSUFFICIENT_N_FOR_P95_GATE";decision="DESCRIPTIVE_ONLY"
            device_strata.append({"device":device,"landmark_id":dc,"n":n,"p95_mm":p95,
                                  "human_device_p95_mm":human_p95,"gate_status":gate_status,"decision":decision})

    clinical_results={};clinical_accept=[]
    for mid in SENTINELS:
        signed=[];absolute=[];eligible=0;not_comp=0
        for cid in sorted(acceptance):
            if not REQ[mid] <= set(ref_case[cid]):continue
            eligible+=1
            pred_rec=next(p for p in predictions if p["case_id"]==cid)
            if not all(pred_rec["valid_in_frame"].get(k,False) for k in REQ[mid]):not_comp+=1;continue
            try:
                pv=measure_one(mid,pred_case[cid],float(cal[cid]["pixel_size"]))
                rv=measure_one(mid,ref_case[cid],float(cal[cid]["pixel_size"]))
            except Exception:
                not_comp+=1;continue
            e=pv-rv;signed.append(e);absolute.append(abs(e))
        tol=ct[mid];s=summary(absolute);bias=statistics.fmean(signed) if signed else None
        if not s:decision="INSUFFICIENT_EVIDENCE"
        elif not_comp:decision="FAIL"
        else:decision="PASS" if s["p95"]<=tol["max_absolute_error"] else "FAIL"
        clinical_results[mid]={"eligible_n":eligible,"valid_n":len(absolute),"not_computable_count":not_comp,
                               "signed_bias":bias,"absolute_error":s,"decision":decision}
        clinical_accept.append({"measurement_id":mid,"n":len(absolute),"signed_bias":bias,
                                "absolute_error":None if not s else s["p95"],"decision":decision})

    hard_device=[x["decision"] for x in device_strata if x["gate_status"]=="HARD_GATE"]
    decisions=[x["decision"] for x in landmark_accept+clinical_accept]
    if all(x=="PASS" for x in decisions) and all(x=="PASS" for x in hard_device):overall="PASS"
    elif "FAIL" in decisions or "FAIL" in hard_device:overall="FAIL"
    else:overall="INSUFFICIENT_EVIDENCE"

    evidence={"schema":"CEPHALO_LOT04_CANDIDATE_BENCHMARK_RESULTS_V1","manifest_sha256":canonical_json_sha256(manifest),
              "candidate_model_sha256":WEIGHT_SHA256,"acceptance_cases":len(acceptance),"latency_seconds":summary(latencies),
              "landmarks":landmark_results,"clinical_measurements":clinical_results,"device_strata":device_strata,
              "predictions":predictions,"overall_decision":overall}
    acceptance_record={"schema_version":"CEPHALO_LOT04_ACCEPTANCE_RECORD_V1",
      "manifest_sha256":canonical_json_sha256(manifest),"candidate_model_sha256":WEIGHT_SHA256,
      "executed_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"landmarks":landmark_accept,
      "clinical_measurements":clinical_accept,"device_strata":device_strata,"overall_decision":overall,
      "decision_reasons":["REFERENCE_EQUIVALENCE_V1 applied without post-result retuning",
        "Device policy: n>=59 hard p95 gate; n<59 descriptive only; no post-hoc pooling",
        "Only anatomy-compatible Aariz mappings scored","Later human-review and clinical-validation gates remain mandatory"]}
    validate_schema(acceptance_record,a.acceptance_schema);validate_acceptance_semantics(acceptance_record,manifest)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    rp=a.output_dir/"cephalo_vnext_lot04_unet_results.json";ap=a.output_dir/"cephalo_vnext_lot04_unet_acceptance_record.json"
    rp.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    ap.write_text(json.dumps(acceptance_record,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"overall_decision":overall,"acceptance_cases":len(acceptance),
                      "latency_p95_s":evidence["latency_seconds"]["p95"],
                      "results_sha256":sha256_file(rp),"acceptance_sha256":sha256_file(ap),
                      "hard_device_strata":sum(x["gate_status"]=="HARD_GATE" for x in device_strata),
                      "descriptive_device_strata":sum(x["gate_status"]=="INSUFFICIENT_N_FOR_P95_GATE" for x in device_strata)},sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    m=sub.add_parser("manifest")
    for n in ("corpus_manifest","qc","calibration_csv","landmark_agreement","measurement_agreement","tolerance_policy","candidate_repo","weights","repo","manifest_schema","output"):
        m.add_argument(f"--{n.replace('_','-')}",type=Path,required=True)
    s=sub.add_parser("score")
    for n in ("manifest","manifest_schema","acceptance_schema","corpus_manifest","qc","calibration_csv","landmark_agreement","measurement_agreement","tolerance_policy","candidate_repo","weights","dataset_root","repo","output_dir"):
        s.add_argument(f"--{n.replace('_','-')}",type=Path,required=True)
    a=ap.parse_args()
    manifest_cmd(a) if a.cmd=="manifest" else score_cmd(a)
if __name__=="__main__":main()
