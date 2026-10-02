#!/usr/bin/env python3
"""Build a deterministic LOT02 manifest from an extracted official Aariz dataset.

The dataset itself is never committed. This tool verifies the expected Aariz
layout, keeps junior/senior annotations separate, hashes every accepted file,
and emits a reproducible JSON manifest for later human-reference statistics.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

DATASET_DOI="10.6084/m9.figshare.27986417.v1"
FIGSHARE_ARTICLE_ID=27986417
ARCHIVE_FILE_ID=51041642
ARCHIVE_SIZE=2098209792
ARCHIVE_MD5="e0bd645bca6759abdae4f199d841bda6"
LICENSE="CC BY 4.0"
SPLITS=("train","valid","test")

AARIZ_TO_DC={
"A":"A","ANS":"ANS","B":"B","Me":"Me","N":"N","Or":"Or","Pog":"Pog","PNS":"PNS",
"Pn":"Prn","S":"S","Ar":"Ar","Co":"Co","Gn":"Gn","Go":"Go","Po":"Po",
"LIT":"L1_incisal","UIA":"U1_apex","UIT":"U1_incisal","LIA":"L1_apex",
"Li":"Li_soft","Ls":"Ls_soft","N`":"N_soft","Pog`":"Pog_soft","Sn":"Sn_soft",
}
HOLD={"UMT":"U6","LMT":"L6"}
EXPECTED_SYMBOLS=set(AARIZ_TO_DC)|set(HOLD)|{"R","LPM","UPM"}

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def parse_annotation(p:Path):
    d=json.loads(p.read_text(encoding="utf-8"))
    pts=d.get("landmarks")
    if not isinstance(pts,list) or len(pts)!=29:
        raise ValueError(f"{p}: expected 29 landmarks")
    out=[]
    for item in pts:
        value=item.get("value",{})
        symbol=item.get("symbol") or item.get("name") or item.get("title")
        # Official files may identify points by stable ids; retain full raw object
        # and resolve symbols later if the annotation does not embed them.
        x,y=value.get("x"),value.get("y")
        if not isinstance(x,(int,float)) or not isinstance(y,(int,float)):
            raise ValueError(f"{p}: invalid landmark coordinates")
        out.append({"symbol":symbol,"x":x,"y":y,"raw_id":item.get("id")})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    cases=[]
    for split in SPLITS:
        base=a.root/split
        images=base/"Cephalograms"
        junior=base/"Annotations"/"Cephalometric Landmarks"/"Junior Orthodontists"
        senior=base/"Annotations"/"Cephalometric Landmarks"/"Senior Orthodontists"
        for d in (images,junior,senior):
            if not d.is_dir(): raise SystemExit(f"missing required directory: {d}")
        for image in sorted(p for p in images.iterdir() if p.is_file()):
            stem=image.stem
            jp=junior/f"{stem}.json"; sp=senior/f"{stem}.json"
            if not jp.is_file() or not sp.is_file():
                raise SystemExit(f"missing paired annotations for {split}/{stem}")
            cases.append({
                "case_id":stem,"split":split,
                "image":{"path":str(image.relative_to(a.root)),"sha256":sha256(image),"size":image.stat().st_size},
                "junior":{"path":str(jp.relative_to(a.root)),"sha256":sha256(jp),"landmarks":parse_annotation(jp)},
                "senior":{"path":str(sp.relative_to(a.root)),"sha256":sha256(sp),"landmarks":parse_annotation(sp)},
            })
    counts={s:sum(c["split"]==s for c in cases) for s in SPLITS}
    if len(cases)!=1000: raise SystemExit(f"expected 1000 cases, got {len(cases)}")
    manifest={
      "schema":"CEPHALO_LOT02_AARIZ_MANIFEST_V1",
      "source":{"doi":DATASET_DOI,"figshare_article_id":FIGSHARE_ARTICLE_ID,
        "archive_file_id":ARCHIVE_FILE_ID,"archive_size":ARCHIVE_SIZE,
        "archive_md5":ARCHIVE_MD5,"license":LICENSE},
      "counts":counts,
      "mapping":{"direct":AARIZ_TO_DC,"semantic_hold":HOLD,
        "policy":"No HOLD or absent identity may be promoted by name similarity."},
      "cases":cases,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"cases":len(cases),"counts":counts,"manifest_sha256":sha256(a.output)},sort_keys=True))
if __name__=="__main__": main()
