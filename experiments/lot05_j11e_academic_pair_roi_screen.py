#!/usr/bin/env python3
"""J11E research-only central dental-region distance for six dHash candidate pairs.

Public university JPEGs and identifiers are ephemeral/in-memory on Actions.
No pair IDs, photographs, pixels, perceptual hashes, individual scores or source
filenames are logged or uploaded. ROI photometric distances cannot establish
patient identity, same examination, or a clinically valid ground truth.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import statistics
import sys

HERE=Path(__file__).parent
def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    assert spec and spec.loader
    obj=importlib.util.module_from_spec(spec)
    sys.modules[name]=obj
    spec.loader.exec_module(obj)
    return obj
J11B=load("j11e_j11b","lot05_j11b_private_candidate_pair_roster.py")
J11A=J11B.J11A
SCHEMA="digital-crown-lot05-j11e-academic-pair-roi-screen-v1"

class ScreenError(ValueError):
    pass


def roi(path: Path):
    from PIL import Image,ImageOps
    if path.is_symlink() or not path.is_file() or path.suffix.lower()!=".jpg":
        raise ScreenError("source_image_missing_or_untrusted")
    if not 100 <= path.stat().st_size <= 25_000_000:
        raise ScreenError("source_image_size_invalid")
    with Image.open(path) as raw:
        if raw.format!="JPEG" or raw.width*raw.height > 40_000_000:
            raise ScreenError("unsafe_jpeg")
        oriented=ImageOps.exif_transpose(raw)
        gray=oriented.convert("L")
        w,h=gray.size
        # Geometry is a coarse standardized dental ROI, NOT landmark registration.
        box=(round(.16*w),round(.22*h),round(.84*w),round(.82*h))
        result=gray.crop(box).resize((224,128),Image.Resampling.BILINEAR)
        return ImageOps.autocontrast(result,cutoff=2)


def distance(a,b) -> float:
    from PIL import ImageChops,ImageStat
    if a.size != b.size:
        raise ScreenError("roi_dimensions_not_normalized")
    return ImageStat.Stat(ImageChops.difference(a,b)).mean[0]/255.0


def evaluate(a,b)->tuple[float,float]:
    from PIL import ImageOps
    return distance(a,b),distance(a,ImageOps.mirror(b))


def screen(images: Path, labels: Path) -> dict:
    if any(p.is_symlink() or not p.is_dir() for p in (images,labels)):
        raise ScreenError("input_roots_missing")
    seen=set()
    records=[]
    for split,expected in J11A.SPLITS.items():
        partition=labels/split
        if partition.is_symlink() or not partition.is_dir():
            raise ScreenError("split_dir_missing")
        source=sorted(partition.glob("*.txt"))
        if len(source)!=expected:
            raise ScreenError("split_count_changed")
        for label in source:
            if label.is_symlink() or not label.stem.isdecimal() or label.stem in seen:
                raise ScreenError("source_unique_id_invalid")
            seen.add(label.stem)
            records.append((split,label.stem,
                            J11A.fingerprint_jpeg(images/(label.stem+".jpg"),split)))
    if len(records)!=333:
        raise ScreenError("coverage_changed")
    pairs=J11B.candidates(records)
    if len(pairs)!=6:
        raise ScreenError("candidate_pairs_changed")
    roi_best=[]
    normal_better=0
    mirror_better=0
    close_direction=0
    dims_changed=0
    implicated=set()
    for pair in pairs:
        a,b=pair["source_image_stem_a"],pair["source_image_stem_b"]
        implicated.add(a)
        implicated.add(b)
        path_a=images/(a+".jpg")
        path_b=images/(b+".jpg")
        from PIL import Image
        with Image.open(path_a) as pic_a,Image.open(path_b) as pic_b:
            dims_changed+=pic_a.size!=pic_b.size
        ra,rb=roi(path_a),roi(path_b)
        try:
            dn,dm=evaluate(ra,rb)
        finally:
            ra.close()
            rb.close()
        roi_best.append(min(dn,dm))
        close_direction+=abs(dn-dm) < .015
        normal_better+=dn+.015<dm
        mirror_better+=dm+.015<dn
    return {
        "schema":SCHEMA,
        "status":"ACADEMIC_PAIR_IMAGE_ROI_DISTANCE_NOT_PATIENT_PROOF",
        "academic_source_images":len(records),
        "cross_split_pair_candidates":len(pairs),
        "distinct_source_images_in_candidate_pairs":len(implicated),
        "different_source_pixel_dimensions_pairs":dims_changed,
        "central_dental_roi_mae_min":round(min(roi_best),4),
        "central_dental_roi_mae_median":round(statistics.median(roi_best),4),
        "central_dental_roi_mae_max":round(max(roi_best),4),
        "central_dental_roi_mae_below_010":sum(d<.10 for d in roi_best),
        "central_dental_roi_mae_above_020":sum(d>.20 for d in roi_best),
        "central_dental_roi_mirror_better_pairs":mirror_better,
        "central_dental_roi_normal_better_pairs":normal_better,
        "central_dental_roi_direction_ambiguous_pairs":close_direction,
        "roi_not_registered_to_anatomical_landmarks":True,
        "same_patient_or_exam_proven":False,
        "expert_pair_adjudications_performed":0,
        "source_rights_commercial_verified":False,
        "patient_independence_established":False,
        "individual_pairs_or_hashes_logged":False,
        "images_exported_or_modified":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--images-dir",type=Path,required=True)
    p.add_argument("--labels-dir",type=Path,required=True)
    args=p.parse_args()
    try:
        result=screen(args.images_dir,args.labels_dir)
    except (ScreenError,J11A.AuditError,J11B.LocalReviewError,OSError,ValueError):
        print(json.dumps({"schema":SCHEMA,"status":"FAIL_CLOSED"}))
        return 1
    print("J11E_AGGREGATE_ONLY="+json.dumps(result,sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
