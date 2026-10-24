"""ODF V5 G3 — import one REAL matched Aariz cephalogram/expert landmark pair.

Strictly disposable T2 laboratory, never a practice or patient dataset.
Uses HTTP range access to the official Figshare 2 GB ZIP; fetches only the
selected film and TWO expert JSON annotations. No full-dataset redistribution.

Reference: Khalid et al., Scientific Data 12, 1336 (2025), Figshare 27986417,
https://doi.org/10.6084/m9.figshare.27986417.v1 — CC BY 4.0.

The annotations represent research ground truth, not a manual tracing by
our imaginary dentist and not automatically approved treatment/diagnosis.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

AARIZ_FIGSHARE_ARTICLE="https://api.figshare.com/v2/articles/27986417"
AARIZ_DOWNLOAD="https://ndownloader.figshare.com/files/51041642"
AARIZ_ZIP_MD5="e0bd645bca6759abdae4f199d841bda6"
AARIZ_PUBLICATION="https://doi.org/10.1038/s41597-025-05542-3"
AARIZ_LICENCE="https://creativecommons.org/licenses/by/4.0/"
# Official code, not an assistant-supplied anatomical mapping.
AARIZ_TO_DC={
    "A":"A", "ANS":"ANS","B":"B","Me":"Me","N":"N","Or":"Or",
    "Pog":"Pog","PNS":"PNS","Pn":"Prn","S":"S","Ar":"Ar","Co":"Co",
    "Gn":"Gn","Go":"Go","Po":"Po","LIT":"L1_incisal","UIA":"U1_apex",
    "UIT":"U1_incisal","LIA":"L1_apex","Li":"Li_soft","Ls":"Ls_soft",
    "N`":"N_soft","Pog`":"Pog_soft","Sn":"Sn_soft",
}
MINIMUM={"S","N","A","B","Po","Or","Go","Me","Gn","L1_incisal",
         "U1_incisal","L1_apex","U1_apex"}

def guard():
    from scripts.odf_v5_lab_seed import guard as lab_guard
    lab_guard()
    if os.getenv("ODF_G3_MATCHED_ANNOTATIONS") != "1":
        raise RuntimeError("ODF_G3_EXPLICIT_EXPERT_ANNOTATIONS_MODE_REQUIRED")


def _paired_names(names: list[str]) -> tuple[str,str,str]:
    index={p.casefold():p for p in names}
    candidates=sorted(p for p in names if "/cephalograms/" in ("/"+p.lower())
                      and p.lower().endswith((".png",".jpg",".jpeg",".bmp")))
    # Prefer an ID from the independent validation set.
    candidates.sort(key=lambda p: (
        not any(part in ("/" + p.lower()) for part in ("/valid/", "/test/")),
        p.lower(),
    ))
    for image in candidates:
        root=image.rsplit("/",1)[0]
        prefix=root.rsplit("/",1)[0]+"/Annotations/Cephalometric Landmarks/"
        stem=Path(image).stem
        senior=index.get((prefix+"Senior Orthodontists/"+stem+".json").casefold())
        junior=index.get((prefix+"Junior Orthodontists/"+stem+".json").casefold())
        if senior and junior:
            return image,senior,junior
    raise RuntimeError("AARIZ_NO_SINGLE_IMAGE_PAIRED_WITH_BOTH_EXPERT_JSONS")


def _landmarks(blob:bytes) -> dict[str,tuple[float,float]]:
    obj=json.loads(blob)
    if not isinstance(obj,dict) or not isinstance(obj.get("landmarks"),list):
        raise ValueError("AARIZ_EXPERT_JSON_SCHEMA_MISMATCH")
    result={}
    for item in obj["landmarks"]:
        if not isinstance(item,dict):continue
        symbol=item.get("symbol")
        val=item.get("value")
        if not isinstance(symbol,str) or symbol not in AARIZ_TO_DC:
            continue
        if not isinstance(val,dict):continue
        x,y=val.get("x"),val.get("y")
        from math import isfinite
        if not all(isinstance(a,(float,int)) and not isinstance(a,bool) and isfinite(a)
                   for a in (x,y)):
            continue
        if symbol in result:raise ValueError("AARIZ_DUPLICATE_ANNOTATION_"+symbol)
        result[symbol]=(float(x),float(y))
    return result


def _extract_pair(archive):
    image_name,senior_name,junior_name=_paired_names(archive.namelist())
    out=[]
    for name,cap in [(image_name,12_000_000),(senior_name,800_000),(junior_name,800_000)]:
        info=archive.getinfo(name)
        if info.file_size<=0 or info.file_size>cap:
            raise RuntimeError("AARIZ_ENTRY_SIZE_NOT_WITHIN_ALLOWLIST")
        data=archive.read(name)
        if len(data)!=info.file_size:
            raise RuntimeError("AARIZ_ENTRY_TRUNCATED")
        out.append(data)
    return (image_name,senior_name,junior_name,*out)


def matched_pair():
    from remotezip import RemoteZip
    from zipfile import ZipFile
    from hashlib import md5
    import tempfile
    from urllib.request import urlopen, Request

    try:
        # Cheap: only the ZIP central directory and three source-bound entries.
        with RemoteZip(AARIZ_DOWNLOAD, initial_buffer_size=1024*1024,
                       support_suffix_range=True,timeout=45) as archive:
            return _extract_pair(archive)
    except Exception as exc:
        print("AARIZ_RANGE_UNAVAILABLE=" + type(exc).__name__, flush=True)
        if os.getenv("ODF_G3_FULL_ARCHIVE_FALLBACK") != "1":
            raise RuntimeError("AARIZ_RANGE_DOWNLOAD_BLOCKED") from exc
    # The official host may reject HTTP ranges. In a *disposable CI runner*
    # only, permit one exact MD5 checked archive download (<2.15 GiB), then
    # extract a single paired film and two expert traces. No redistribution.
    with tempfile.TemporaryDirectory(prefix="odf-g3-aariz-") as tmp:
        target=Path(tmp)/"Aariz.zip"
        hasher=md5()
        count=0
        with urlopen(Request(AARIZ_DOWNLOAD,headers={
            "User-Agent":"DigitalCrown-ODF-G3-ResearchLab/1.0"}),timeout=60) as src:
            with target.open("wb") as sink:
                while True:
                    chunk=src.read(8*1024*1024)
                    if not chunk:break
                    count+=len(chunk)
                    if count>2_200_000_000:
                        raise RuntimeError("AARIZ_REMOTE_ARCHIVE_EXCEEDS_VERIFIED_SOURCE")
                    hasher.update(chunk)
                    sink.write(chunk)
        if hasher.hexdigest()!=AARIZ_ZIP_MD5:
            raise RuntimeError("AARIZ_SOURCE_ZIP_MD5_INTEGRITY_FAILED")
        with ZipFile(target) as archive:
            return _extract_pair(archive)


def seed_verified_pair():
    guard()
    image_name,senior_name,junior_name,image_bytes,senior_bytes,junior_bytes=matched_pair()
    from PIL import Image,ImageOps,ImageDraw
    image=Image.open(BytesIO(image_bytes))
    image.load()
    if image.width<600 or image.height<600 or image.width>6000 or image.height>6000:
        raise RuntimeError("AARIZ_IMAGE_DIMENSIONS_UNEXPECTED")
    original_shape=(image.width,image.height)
    senior=_landmarks(senior_bytes)
    junior=_landmarks(junior_bytes)
    shared=set(senior)&set(junior)
    if len(shared)<19 or len({AARIZ_TO_DC[k] for k in shared}&MINIMUM)!=len(MINIMUM):
        raise RuntimeError("AARIZ_REQUIRED_EXPERT_TRACING_POINTS_MISSING")
    # A unique 1:1 paired image and two experts: research consensus average.
    # The actual numerical positioning is derived only from these JSON files.
    factor=min(1935/image.width,2400/image.height)
    new_w,new_h=round(image.width*factor),round(image.height*factor)
    scale_x=new_w/image.width
    scale_y=new_h/image.height
    left=(1935-new_w)//2
    top=(2400-new_h)//2
    transformed=[]
    for key in sorted(shared):
        src_x=(senior[key][0]+junior[key][0])/2
        src_y=(senior[key][1]+junior[key][1])/2
        if not(0<=src_x<image.width and 0<=src_y<image.height):
            raise RuntimeError("AARIZ_EXPERT_COORDINATE_OUTSIDE_MATCHED_IMAGE")
        transformed.append({"id":AARIZ_TO_DC[key],
             "x":float(src_x*scale_x+left),"y":float(src_y*scale_y+top)})
    if len({p["id"] for p in transformed})!=len(transformed):
        raise RuntimeError("AARIZ_CANONICAL_LANDMARK_DUPLICATION")

    canvas=Image.new("RGB",(1935,2400),(16,21,29))
    canvas.paste(image.convert("RGB").resize((new_w,new_h)),(left,top))
    png=ROOT/"backend/static/uploads/radios/t2-cephalo-seeded.png"
    png.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(png,format="PNG")
    output=ROOT/"artifacts/ortho-v5-g3-expert-lateral"
    output.mkdir(parents=True,exist_ok=True)
    (output/"expert-matched-cephalogram.png").write_bytes(png.read_bytes())
    overlay=canvas.copy()
    draw=ImageDraw.Draw(overlay)
    for p in transformed:
        if p["id"] in {"S","N","A","B","Or","Po","Go","Me","Gn",
                       "U1_incisal","L1_incisal","U1_apex","L1_apex"}:
            x,y=p["x"],p["y"]
            draw.ellipse((x-7,y-7,x+7,y+7),outline="#ffd166",width=3)
            draw.text((x+12,y-10),p["id"],fill="#ffd166")
    overlay.save(output/"expert-landmarks-on-same-real-film.png")
    from backend import models,database
    from backend.services.cephalo_safe_engine import cephalo_safe_engine
    from backend.services.cephalo_runtime_evidence import (
        EVIDENCE_GRAPH_KEY,build_cephalo_runtime_evidence_payload)
    from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    with database.SessionLocal() as db:
        dentist=db.query(models.User).filter(
            models.User.email=="odf-lab-dentiste@example.com").one()
        patient=db.query(models.Patient).filter(
            models.Patient.numero_dossier=="T2-0001",
            models.Patient.employer_id==dentist.id).one()
        study=db.query(models.CephaloAnalysis).filter(
            models.CephaloAnalysis.patient_id==patient.id,
            models.CephaloAnalysis.image_original_path=="api/static/uploads/radios/t2-cephalo-seeded.png"
        ).order_by(models.CephaloAnalysis.id).offset(1).first()
        if study is None: raise RuntimeError("AARIZ_TARGET_T2_STUDY_A_ABSENT")
        metrics=cephalo_safe_engine.calculate_metrics(
            {p["id"]:(p["x"],p["y"]) for p in transformed},
            custom_mm_ratio=None,
        )
        graph=build_cephalo_runtime_evidence_payload(
            patient_id=patient.id,
            image_record_id=study.image_original_path,
            result=metrics,landmarks=transformed,
            inference_mode=None,manual_revision=True,
            is_calibrated=False,calibration_data=None,
            case_id=f"odf-v5-aariz-pair:{patient.id}:{study.id}",
        )
        payload={**metrics.model_dump(),EVIDENCE_GRAPH_KEY:graph,
                 "odf_lab_image_landmark_alignment":"VERIFIED_AARIZ_EXPERT_PAIR",
                 "odf_lab_source_image_sha256":sha256(image_bytes).hexdigest(),
                 "odf_lab_display_png_sha256":sha256(png.read_bytes()).hexdigest(),
                 "odf_lab_source_senior_sha256":sha256(senior_bytes).hexdigest(),
                 "odf_lab_source_junior_sha256":sha256(junior_bytes).hexdigest(),
                 "odf_lab_dataset_image_id":image_name,
                 "vision_metadata":{"mode_inference":"EXTERNAL_RESEARCH_EXPERT_ANNOTATIONS",
                                    "source":"AARIZ_PUBLIC_CC_BY_4_0"},
                 "calibration_status":"unverified",
                 "t1_projection":{},"t2_projection":{},
                 }
        scientific=project_runtime_chain_read_path(payload,patient_id=patient.id)
        read=scientific["scientific_read_path"]
        if read.get("active_chain")!="VERIFIED" or read.get("revision")!=1:
            raise RuntimeError("AARIZ_EVIDENCE_NOT_VERIFIED")
        if not cephalo_consistency_validator.validate(payload).is_valid:
            raise RuntimeError("AARIZ_CONSISTENCY_VALIDATOR_REFUSED")
        study.landmarks_data=transformed
        study.angles_data=payload
        study.is_calibrated=False
        study.mm_per_pixel=None
        study.calibration_data=None
        db.commit()
        source={
          "dataset":"Aariz Cephalometric Dataset",
          "article_id":27986417,"file_id":51041642,
          "source_article":AARIZ_FIGSHARE_ARTICLE,
          "source_license":AARIZ_LICENCE,
          "attribution":AARIZ_PUBLICATION,
          "license":"CC BY 4.0",
          "image_entry":image_name,"senior_entry":senior_name,
          "junior_entry":junior_name,
          "image_sha256":sha256(image_bytes).hexdigest(),
          "senior_sha256":sha256(senior_bytes).hexdigest(),
          "junior_sha256":sha256(junior_bytes).hexdigest(),
          "original_dimensions":original_shape,
          "display_dimensions":[1935,2400],
          "transform":{"scale_x":scale_x,"scale_y":scale_y,"left":left,"top":top},
          "expert_point_count":len(transformed),
          "patient_id":patient.id,"analysis_id":study.id,
          "analysis_revision":read["revision"],
          "scientific_state":read["active_chain"],
          "scientific_source":"EXPERT_ANNOTATIONS_RESEARCH_NOT_SYNTHETIC",
          "interpretation":"NO DIAGNOSIS NO PRACTITIONER-R14 VALIDATION",
          "angle_class":"INDEPENDENT_SYNTHETIC_CAST_EXAM_NOT_RADIOGRAPH",
          "mm_calibration":"UNVERIFIED: ONLY SOURCE-LOCKED ANGLES MAY PRINT",
        }
        (output/"expert-pair-provenance.json").write_text(
            json.dumps(source,indent=2,ensure_ascii=False),encoding="utf-8")
        (output/"recomputed-canonical-angles.json").write_text(json.dumps([
            {"id":m["canonical_measurement_id"],"availability":m["availability_status"],
             "value":m["value"],"unit":m["unit"]}
            for m in read.get("canonical_measurements") or []
            if m.get("unit")=="°"
        ],indent=2,ensure_ascii=False),encoding="utf-8")
        print("ODF_G3_EXPERT_IMAGE_MATCHED_SOURCE_VERIFIED="+json.dumps({
            "head":os.environ.get("PRODUCT_HEAD"),"analysis_id":study.id,
            "point_count":len(transformed),"canonical_count":len(read.get("canonical_measurements") or []),
            "dataset":"Aariz CC BY 4.0","revision":read["revision"],
        }),flush=True)

if __name__=="__main__":
    seed_verified_pair()
