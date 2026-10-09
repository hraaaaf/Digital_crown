#!/usr/bin/env python3
"""Research-only counterexample: Facad's derived PM' cannot be blindly aliased to PM.

All coordinates here are synthetic geometry, NEVER patient-derived.
No product runtime edits and no Facad numerical clinical parity assertion.
"""
import argparse, json, math
from pathlib import Path

def cross(a,b):
    return a[0]*b[1]-a[1]*b[0]

def sub(a,b):
    return (a[0]-b[0],a[1]-b[1])

def intersection(xi,pm,a,pog):
    r=sub(pm,xi)
    s=sub(pog,a)
    det=cross(r,s)
    if abs(det)<1e-12:
        raise ValueError("Parallel or degenerate source lines")
    t=cross(sub(a,xi),s)/det
    return (xi[0]+t*r[0], xi[1]+t*r[1])

def dist(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])

def verify_source(f):
    if f["facad_constructions"]["PM'"]["calc_type"]!="Intersect":
        raise ValueError("Vendor point is not defined as line intersection")
    if f["facad_constructions"]["PM'"]["refs"]!=["Xi","PM","A","Pog"]:
        raise ValueError("Vendor construct dependencies modified")
    if f["resolutions"]["Mand len"]["facad"]["calc_type"]!="Dist2p":
        raise ValueError("Vendor length method unexpectedly changed")
    if f["resolutions"]["Mand len"]["facad"]["refs"]!=["Xi","PM'"]:
        raise ValueError("Vendor length endpoint mismatch")
    if f["resolutions"]["Mand len"]["dc"]["direct_alias_allowed"] is not False:
        raise ValueError("Unsafe vendor-to-DC alias enabled")

def test():
    xi=(0.,0.)
    pm=(10.,0.)
    a=(5.,-5.)
    pog=(5.,5.)
    pp=intersection(xi,pm,a,pog)
    assert pp==(5.,0.) and dist(xi,pp)==5. and dist(xi,pm)==10.
    assert intersection(xi,pm,pog,a)==pp
    assert intersection(pm,xi,a,pog)==pp
    assert intersection((0,0),(10,0),(10,-3),(10,3))==(10.,0.)
    for bad in (
        ((0,0),(10,0),(0,1),(10,1)),
        ((0,0),(0,0),(1,1),(2,2)),
    ):
        try: intersection(*bad)
        except ValueError: pass
        else: raise AssertionError("Degenerate geometry improperly accepted")
    print("PM_PRIME_VENDOR_INTERSECTION_GEO_TESTS=6")
    print("SYNTHETIC_XI_PM_MM=10")
    print("SYNTHETIC_XI_PM_PRIME_MM=5")
    print("NON_ALIAS_COUNTEREXAMPLE_VERIFIED=true")
    print("PATIENT_NUMERICAL_PARITY_CERTIFIED=false")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--vendor-source",type=Path,required=True)
    args=ap.parse_args()
    verify_source(json.loads(args.vendor_source.read_text(encoding="utf-8")))
    test()
