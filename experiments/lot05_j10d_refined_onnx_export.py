#!/usr/bin/env python3
"""Isolated export/probe of four-class panoramic checkpoint (NOT a deployable artifact).

Do not package model bytes, since upstream HF weight licence is NC/SA.
The PyTorch source is pickle-bearing untrusted third-party material: execute
only in unprivileged ephemeral CI with no persistent GitHub credentials.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import traceback
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import HfApi, hf_hub_download
from ultralytics import YOLO

REPO="chemahc94/caries-detection-weights"
PATH="best_refined.pt"
OUT=Path(os.getenv("LOT05_REFINED_ONNX_REPORT","lot05-refined-onnx-export.json"))
EXPECTED_CLASSES=["Impacted","Caries","Periapical Lesion","Deep Caries"]
EXPECTED_SOURCE_SHA="bd993512487a74d2cba99698bc2d525d061d30a9306a9ab30a9049effdbc74d0"
REPORT={
 "mission":"LOT05/05.7-J10D",
 "experiment_only":True,
 "commercial_release_authorized":False,
 "source_repo":REPO,
 "source_license":"cc-by-nc-sa-4.0",
 "clinical_acceptance":False,
 "expected_model_classes":EXPECTED_CLASSES,
 "explicit_runtime_mapping":{
   "SOTAPanoramicEngine":[2,0,3,1],
   "PanoramicEngine":[3,0,2,1]
 },
 "no_binary_packaged":True,
 "status":"PENDING",
}


def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


try:
    commit=str(HfApi().model_info(REPO).sha)
    if len(commit)!=40:raise RuntimeError("HF source SHA is unpinned")
    pt=Path(hf_hub_download(REPO,PATH,revision=commit))
    actual=sha(pt)
    REPORT.update({"source_commit":commit,"source_sha256":actual,
                   "source_bytes":pt.stat().st_size})
    if actual!=EXPECTED_SOURCE_SHA:
        raise RuntimeError("Unexpected source SHA for refined4 candidate")
    model=YOLO(str(pt),task="detect")
    names=[str(model.names[k]) for k in sorted(model.names)]
    if names!=EXPECTED_CLASSES:
        raise RuntimeError(f"Unexpected class order: {names}")
    model_onnx=Path(model.export(format="onnx",imgsz=1280,dynamic=False,
                                simplify=False,opset=13,device="cpu"))
    opt=ort.SessionOptions()
    opt.intra_op_num_threads=2
    session=ort.InferenceSession(str(model_onnx),sess_options=opt,
                                 providers=["CPUExecutionProvider"])
    inputs=session.get_inputs()
    outputs=session.get_outputs()
    if len(inputs)!=1:raise RuntimeError("Expected exactly one ONNX tensor input")
    shape=list(inputs[0].shape)
    if shape!=[1,3,1280,1280]:raise RuntimeError(f"Unexpected image tensor: {shape}")
    x=np.zeros(shape,dtype=np.float32)
    x[:,:,440:700,250:900]=0.45
    tick=time.perf_counter()
    preds=session.run(None,{inputs[0].name:x})
    elapsed=time.perf_counter()-tick
    raw=np.asarray(preds[0])
    if not np.isfinite(raw).all():
        raise RuntimeError("Nonfinite ONNX output on deterministic synthetic input")
    if raw.ndim!=3 or raw.shape[0]!=1 or raw.shape[1]!=8:
        raise RuntimeError(f"Expected raw 4-class YOLO 1x8xN, got {raw.shape}")
    REPORT.update({
        "status":"SUCCESS_TECHNICAL_ONLY",
        "onnx_sha256":sha(model_onnx),
        "onnx_bytes":model_onnx.stat().st_size,
        "onnx_input":[list(t.shape) for t in inputs],
        "onnx_output":[list(t.shape) for t in outputs],
        "runtime_output_shape":list(raw.shape),
        "cpu_seconds_one_synthetic":round(elapsed,4),
        "finite_output":True,
        "structurally_compatible_only_with_explicit_class_adapter":True,
        "limitation":"Clinical cross-dataset testing and commercial redistribution rights absent; no binary uploaded",
    })
except Exception as error:
    REPORT.update({"status":"FAILED","error":str(error),
                   "traceback_tail":traceback.format_exc()[-3500:]})
finally:
    OUT.write_text(json.dumps(REPORT,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(REPORT,indent=2,sort_keys=True))
if REPORT["status"]!="SUCCESS_TECHNICAL_ONLY":raise SystemExit(1)
