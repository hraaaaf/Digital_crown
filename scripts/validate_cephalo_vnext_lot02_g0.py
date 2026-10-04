#!/usr/bin/env python3
"""Independent synthetic geometry oracle for Cephalo vNext LOT02 G0."""
from __future__ import annotations
import math

class G0Error(ValueError):
    pass

def _vec(a,b):
    return (float(b[0])-float(a[0]), float(b[1])-float(a[1]))

def _norm(v):
    return math.hypot(v[0],v[1])

def angle_between(u,v):
    nu,nv=_norm(u),_norm(v)
    if nu==0 or nv==0:
        raise G0Error("degenerate vector")
    c=max(-1.0,min(1.0,(u[0]*v[0]+u[1]*v[1])/(nu*nv)))
    return math.degrees(math.acos(c))

def vertex_angle(a,b,c):
    return angle_between(_vec(b,a),_vec(b,c))

def acute_line_angle(a,b,c,d):
    x=angle_between(_vec(a,b),_vec(c,d))
    return min(x,180.0-x)

def distance_mm(a,b,mm_per_px):
    if not isinstance(mm_per_px,(int,float)) or mm_per_px<=0 or not math.isfinite(mm_per_px):
        raise G0Error("invalid calibration")
    return math.hypot(float(a[0])-float(b[0]),float(a[1])-float(b[1]))*mm_per_px

FIXTURE={
"S":(0,0),"N":(10,0),"A":(10,10),"B":(10,-10),
"Po":(0,0),"Or":(10,0),"Go":(0,10),"Me":(10,10),
"Gn":(6,8),"LIA":(5,15),"LIT":(5,5),"Co":(0,0),
}
EXPECTED={
"SNA_deg":90.0,"SNB_deg":90.0,"ANB_deg":0.0,
"FMA_deg":0.0,"IMPA_deg":90.0,"FMIA_deg":90.0,
"SN_GoGn_deg":18.434948822922017,"Co_A_mm":0.5,"Co_Gn_mm":1.0,
}

def compute_fixture():
    p=FIXTURE
    sna=vertex_angle(p["S"],p["N"],p["A"])
    snb=vertex_angle(p["S"],p["N"],p["B"])
    return {
      "SNA_deg":sna,"SNB_deg":snb,"ANB_deg":sna-snb,
      "FMA_deg":acute_line_angle(p["Po"],p["Or"],p["Go"],p["Me"]),
      "IMPA_deg":acute_line_angle(p["LIA"],p["LIT"],p["Go"],p["Me"]),
      "FMIA_deg":acute_line_angle(p["LIA"],p["LIT"],p["Po"],p["Or"]),
      "SN_GoGn_deg":acute_line_angle(p["S"],p["N"],p["Go"],p["Gn"]),
      "Co_A_mm":distance_mm(p["Co"],(3,4),0.1),
      "Co_Gn_mm":distance_mm(p["Co"],p["Gn"],0.1),
    }
