#!/usr/bin/env python3
"""Generate a STRICTLY ARTIFICIAL 1024px radiographic geometry *phantom* for FUE-P2.

A raster with an exact drawn ruler of 200 px = 20 DESIGN mm (0.1 design-mm/px).
This is NOT an actual physical scale, radiographic acquisition, anatomy,
orthodontist-labelled goldset, or validated patient image.
Generated ONLY in disposable CI T2, never shipped into the application.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W=H=1024
P1=(420, 862)
P2=(620, 862)
DESIGN_MM=20.0
RATIO=DESIGN_MM / (P2[0]-P1[0])
OUT=Path(os.environ.get("CEPH_FUE_P2_PHANTOM_DIR", "/tmp/ceph-fue-p2-phantom"))
OUT.mkdir(parents=True, exist_ok=True)

im=Image.new("RGB", (W,H), (24,28,32))
px=im.load()
# Deterministic grayscale texture: deliberately NOT copied from a human.
for y in range(H):
    for x in range(W):
        n=((x*37+y*17+(x*y)%13)%31)-15
        grad=round(25*(1-abs(x-W//2)/(W/2)))
        val=max(4,min(92,38+grad+n))
        px[x,y]=(val,val,val)
d=ImageDraw.Draw(im)
# Abstract geometric curves ONLY; unequivocally a test phantom, not medical evidence.
d.ellipse((210,135,760,716),outline=(185,192,196),width=14)
d.arc((405,155,790,640),18,155,fill=(228,230,233),width=12)
d.line([(600,280),(750,375),(684,410),(788,496),(680,550),(595,650)],fill=(215,215,218),width=12,joint="curve")
d.arc((310,300,800,805),27,145,fill=(185,192,196),width=9)
d.line([(340,620),(550,700),(718,663)],fill=(226,228,230),width=7,joint="curve")
d.ellipse((408,250,508,350),outline=(210,217,230),width=7)
d.line([(180,740),(844,740)],fill=(90,95,103),width=2)
# The only known length is between exact *digital* endpoints.
d.line([P1,P2],fill=(255,255,255),width=5)
for x in [P1[0],P2[0]]:
    d.line([(x,828),(x,900)],fill=(255,255,255),width=5)
    d.ellipse((x-5,857,x+5,867),fill=(255,190,0))
d.text((432,898),"20 DESIGN mm = 200 px",fill=(255,240,198))
d.text((36,50),"SYNTHETIC TEST PHANTOM - NO PATIENT",fill=(252,240,164))
d.text((36,80),"NOT A MEDICAL RADIOGRAPH OR CLINICALLY MEASURED RULER",fill=(252,240,164))
filename=OUT/"ceph_fue_p2_phantom.png"
im.save(filename, format="PNG", compress_level=9)
assert im.size==(1024,1024)
assert RATIO==0.1
sha=hashlib.sha256(filename.read_bytes()).hexdigest()
manifest={
 "schema":"CEPH_FUE_P2_DESIGN_PHANTOM_V1",
 "image_path":str(filename),"image_size_px":[W,H],
 "point_1":dict(x=P1[0],y=P1[1]),"point_2":dict(x=P2[0],y=P2[1]),
 "design_distance_mm":DESIGN_MM,"design_mm_per_pixel":RATIO,
 "synthetic_no_human_source":True,"true_physical_patient_scale":False,
 "clinical_ground_truth":False,"sha256":sha,
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("CEPH_FUE_P2_DESIGN_PHANTOM_CREATED",json.dumps({k:manifest[k] for k in ("image_size_px","design_mm_per_pixel","sha256","clinical_ground_truth")}))
