"""Nonclinical J2.1 M6 proof: public radiograph + prior J1 ONNX points.

Renders lab-only raster previews. NOT the Digital Crown Desktop UI. The
media-binding envelope is synthetic: encrypted production linkage is NOT proven.
"""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3

from PIL import Image, ImageDraw, ImageOps

# Import only the isolated source files; DO NOT initialize the clinic backend.
from scripts.ceph_premium_j21m1_scene_fue import namespace, load_source

namespace("backend", "backend")
namespace("backend.services", "backend/services")
namespace("backend.schemas", "backend/schemas")
load_source("backend.services.srpose38_contract", "backend/services/srpose38_contract.py")

from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft
from backend.services.ceph_premium_pixel_transform_lab import SourceView
from backend.services.ceph_premium_scene_ledger_lab import SceneLabLedger
from backend.services.ceph_premium_scene_source_lab import verify_original_pixels
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING, SRPOSE38_MODEL_SHA256

SHA=lambda data:hashlib.sha256(data).hexdigest()


def main():
    image_bytes=Path(os.environ["CEPH_PUBLIC_SOURCE_IMAGE"]).read_bytes()
    j1_bytes=Path(os.environ["CEPH_J1_COORDS_JSON"]).read_bytes()
    out=Path(os.environ["CEPH_J21_EVIDENCE_DIR"])
    out.mkdir(parents=True,exist_ok=True)
    j1=json.loads(j1_bytes)
    case=next(x for x in j1["cases"] if x["radio"]=="anug")
    assert j1["head"]=="3137fa4c1611d47e4d71906cf5e4542cc8b01b49"
    assert j1["model_sha256"]==SRPOSE38_MODEL_SHA256
    assert j1["clinical_authority"] is False
    assert case["source_image_sha256"]==SHA(image_bytes)=="ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6"
    points=case["landmarks"]
    assert len(points)==38 and {p["id"] for p in points}==set(SOTA_LANDMARKS_MAPPING.values())
    raw={
        "schema_version":"CEPH_PREMIUM_SCENE_V1_DRAFT",
        "identity":{
            "employer_id":1001,"patient_id":2001,"study_id":3001,
            "original_asset_id":4001,"original_sha256":SHA(image_bytes),
            "original_width":2272,"original_height":1818,
            "scientific_revision":1,"scientific_digest":SHA(j1_bytes),
            "scene_revision":1,"parent_scene_sha256":None,
            "detector_model":"srpose38-tta-1024.onnx",
            "detector_sha256":SRPOSE38_MODEL_SHA256,
            "detector_mapping_authority":"LEGACY_LOCAL_UNVERIFIED",
            "coordinate_system":"SOURCE_IMAGE_PIXELS_TOP_LEFT"
        },
        "landmarks":[{"id":p["id"],"x":p["x"],"y":p["y"],
                      "origin":"SRPOSE38_AUTO","score_status":"NOT_EMITTED"}
                     for p in points],
        "measurements":[],"contours":[],"constructions":[],
        "document_status":"NONCLINICAL_DRAFT","clinical_release":False
    }
    scene=CephaloPremiumSceneDraft.model_validate(raw)
    mock={"binding_state":"EXPLICIT_VERIFIED_ORIGINALS","study_id":3001,
          "patient_id":2001,"revision":1,"clinical_release":False,
          "items":[{"role":"RADIO_SOURCE","asset_id":4001,
                    "sha256":SHA(image_bytes),"revision":1}]}
    evidence=verify_original_pixels(scene,verified_media=mock,original_bytes=image_bytes)
    conn=sqlite3.connect(":memory:")
    ledger=SceneLabLedger(conn)
    digest=ledger.append(scene,expected_parent_sha256=None,actor_employer_id=1001,
                         actor_patient_id=2001,actor_study_id=3001)
    assert ledger.latest(employer_id=1001,patient_id=2001,study_id=3001).sha256()==digest
    base=Image.open(BytesIO(image_bytes))
    previews=[]
    for name,view in (
        ("m6-lab-anug-1280.png",SourceView(2272,1818,viewport_width=1280,viewport_height=900)),
        ("m6-lab-anug-crop-1600.png",SourceView(2272,1818,crop_x=800,crop_y=300,
             crop_width=1450,crop_height=1450,viewport_width=1600,viewport_height=1000,
             zoom=1.25,pan_x=20,pan_y=-25)),
    ):
        img=ImageOps.exif_transpose(base).convert("RGB")
        assert img.size==view.oriented_size
        cropped=img.crop((view.crop_x,view.crop_y,view.crop_x+view.crop_width,
                          view.crop_y+view.crop_height))
        scale,left,top=view.scale_and_origin
        image=cropped.resize((round(view.crop_width*scale),round(view.crop_height*scale)))
        canvas=Image.new("RGB",(view.viewport_width,view.viewport_height),(24,32,43))
        canvas.paste(image,(round(left),round(top)))
        d=ImageDraw.Draw(canvas)
        pts={p["id"]:p for p in points}
        for a,b,color in (("S","N","#4ad4ff"),("N","A","#ffbf61"),
                          ("N","B","#ff8f82"),("U1_incisal","U1_apex","#b2f483"),
                          ("L1_incisal","L1_apex","#b2f483")):
            d.line([view.to_screen(pts[a]["x"],pts[a]["y"]),
                    view.to_screen(pts[b]["x"],pts[b]["y"])],fill=color,width=3)
        max_error=0.0
        for p in points:
            x,y=view.to_screen(p["x"],p["y"])
            px,py=view.to_original(x,y)
            max_error=max(max_error,abs(px-p["x"]),abs(py-p["y"]))
            if 0<=x<view.viewport_width and 0<=y<view.viewport_height:
                d.ellipse((x-3,y-3,x+3,y+3),fill="#ffe065",outline="#18202b")
        assert max_error<1e-7
        d.rectangle((0,0,view.viewport_width,31),fill="#132333")
        d.text((10,10),"J2.1 LAB ONLY | REAL RADIO + PRIOR J1 ONNX | NOT DESKTOP OR CLINICAL",fill="#ffffff")
        path=out/name
        canvas.save(path)
        previews.append({"filename":name,"sha256":SHA(path.read_bytes()),
                         "max_roundtrip_error":max_error,"viewport":list(canvas.size)})
    report={"head":os.environ["PRODUCT_HEAD"],"prior_onnx_head":j1["head"],
            "prior_onnx_artifact":13703923098,"coords_sha256":SHA(j1_bytes),
            "source_sha256":SHA(image_bytes),"model_sha256":j1["model_sha256"],
            "points":len(points),"scene_sha256":digest,"scene_reopened":True,
            "mock_binding_envelope":True,"real_authenticated_dc_dos05_binding":False,
            "native_desktop_fue_complete":False,"new_onnx_inference":False,
            "clinical_release":False,"views":previews,
            "source_dimensions":[evidence["source_width"],evidence["source_height"]]}
    (out/"m6-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    (out/"m6-scene.json").write_bytes(scene.canonical_bytes())
    print("M6_REAL_RADIO_LAB_PREVIEW_PASS",json.dumps({"points":38,"head":report["head"],
          "screenshots":[x["filename"] for x in previews],"desktop":False}))


if __name__=="__main__":
    main()
