#!/usr/bin/env python3
"""Research-only synthetic geometry contract for Facad Ricketts F01.13 Phase 8.

Never opens patient records, launches Facad, edits runtime, imports clinical norms
or claims numerical parity. All coordinates below are arbitrary synthetic units.
The fail-closed behavior belongs to this harness, not necessarily Facad runtime.
"""
import argparse
import copy
import json
import math
from pathlib import Path

RELATIVE_LINE_TOLERANCE = 1e-12


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def intersection(xi, pm, a, pog):
    """Intersection of unbounded lines Xi--PM and A--Pog; no ray clipping."""
    r, s = sub(pm, xi), sub(pog, a)
    nr, ns = math.hypot(*r), math.hypot(*s)
    if nr == 0.0 or ns == 0.0:
        raise ValueError("Degenerate zero-length source line")
    det = cross(r, s)
    if abs(det) <= RELATIVE_LINE_TOLERANCE*nr*ns:
        raise ValueError("Parallel, coincident or numerically unstable source lines")
    t = cross(sub(a, xi), s)/det
    result = (xi[0]+t*r[0], xi[1]+t*r[1])
    if not all(math.isfinite(q) for q in result):
        raise ValueError("Nonfinite synthetic intersection")
    return result


def foot_on_line(point, line_a, line_b):
    """Geometric foot of point on infinite line: FH intersect its normal."""
    d = sub(line_b, line_a)
    denom = d[0]*d[0]+d[1]*d[1]
    if denom <= 0.0 or not math.isfinite(denom):
        raise ValueError("Degenerate synthetic FH")
    t = ((point[0]-line_a[0])*d[0] + (point[1]-line_a[1])*d[1])/denom
    result = (line_a[0]+t*d[0], line_a[1]+t*d[1])
    if not all(math.isfinite(q) for q in result):
        raise ValueError("Nonfinite synthetic CF")
    return result


def directed_vector_angle_degrees(first, second):
    """Unsigned [0,180] vector angle only; NOT Facad Angle4p rendering."""
    nr, ns = math.hypot(*first), math.hypot(*second)
    if nr == 0 or ns == 0:
        raise ValueError("Degenerate synthetic angle")
    c = (first[0]*second[0]+first[1]*second[1])/(nr*ns)
    return math.degrees(math.acos(max(-1., min(1., c))))


def verify_source(f):
    p=f.get("facad_constructions", {}).get("PM'", {})
    if p.get("calc_type") != "Intersect" or p.get("refs") != ["Xi","PM","A","Pog"]:
        raise ValueError("Vendor point is not source-locked as Xi-PM versus A-Pog intersection")
    q=f.get("resolutions", {}).get("Mand len", {})
    if q.get("facad", {}).get("calc_type") != "Dist2p" or q.get("facad", {}).get("refs") != ["Xi","PM'"]:
        raise ValueError("Vendor Mand len endpoint or operator mismatch")
    if q.get("dc", {}).get("direct_alias_allowed") is not False:
        raise ValueError("Unsafe Facad PM-prime to anatomical DC alias")
    if f.get("safety_rules", {}).get("facad_pm_prime_must_not_alias_pm_ricketts") is not True:
        raise ValueError("Source safety rule for PM prime missing")


def verify_ptv_source(d):
    c=d.get("facad_constructions", {})
    for key, op, refs in (
        ("FH","Line",["P","Or"]),
        ("PtV","Normal",["FH","Pt"]),
        ("CF","Inter2ln",["FH","PtV"]),
        ("Xi","Intersect",["R23","R14","R13","R24"]),
    ):
        x=c.get(key, {})
        if x.get("calc_type") != op or x.get("refs") != refs:
            raise ValueError("Facad PtV/CF/Xi dependency changed: "+key)
    pfh=d.get("resolutions",{}).get("PFH",{})
    if pfh.get("facad",{}).get("calc_type")!="Dist2p" or pfh.get("facad",{}).get("refs")!=["CF","Go"]:
        raise ValueError("Vendor PFH length incorrectly replaced")
    if pfh.get("dc",{}).get("direct_alias_allowed") is not False:
        raise ValueError("Unsafe Facad CF-Go to Digital Crown clinical alias")
    if d.get("safety_rules",{}).get("facad_pt_must_not_alias_dc_pr_ricketts_ptv") is not True:
        raise ValueError("Unsafe silent Facad Pt/Ricketts PR alias")


def close_point(a,b,eps=1e-9):
    return dist(a,b) <= eps


def rejects(function, *args):
    try:
        function(*args)
    except ValueError:
        return True
    return False


def synthetic_tests():
    cases={}
    def check(name, predicate):
        if not predicate:
            raise AssertionError("Synthetic geometry contract failed: "+name)
        cases[name]=True
        print("SYNTHETIC_CASE_PASS="+name)

    xi=(0.,0.)
    pm=(10.,0.)
    a=(5.,-5.)
    pog=(5.,5.)
    pp=intersection(xi,pm,a,pog)
    check("PMPRIME_INSIDE_SEGMENT", close_point(pp,(5.,0.)) and dist(xi,pp)==5 and dist(xi,pm)==10)
    check("PMPRIME_REVERSE_APOG", close_point(intersection(xi,pm,pog,a),pp))
    check("PMPRIME_REVERSE_XIPM", close_point(intersection(pm,xi,a,pog),pp))
    check("PMPRIME_OPPOSITE_RAY", close_point(intersection(xi,pm,(-5.,-5.),(-5.,5.)),(-5.,0.)))
    check("PMPRIME_BEYOND_PM", close_point(intersection(xi,pm,(15.,-5.),(15.,5.)),(15.,0.)))
    check("PMPRIME_EQUALS_PM_SPECIAL_CASE", close_point(intersection(xi,pm,(10.,-5.),(10.,5.)),pm))
    off=(100.,-32.)
    move=lambda z: (z[0]+off[0],z[1]+off[1])
    check("PMPRIME_TRANSLATION_INVARIANT",close_point(intersection(*map(move,(xi,pm,a,pog))),move(pp)))
    scale=lambda z: (z[0]*1e-6,z[1]*1e-6)
    check("PMPRIME_SCALE_INVARIANT",close_point(intersection(*map(scale,(xi,pm,a,pog))),scale(pp),eps=1e-11))
    check("PARALLEL_REJECT",rejects(intersection,(0,0),(10,0),(0,1),(10,1)))
    check("COLLINEAR_REJECT",rejects(intersection,(0,0),(10,0),(3,0),(7,0)))
    check("ZERO_XIPM_REJECT",rejects(intersection,(0,0),(0,0),(1,1),(2,3)))
    check("ZERO_APOG_REJECT",rejects(intersection,(0,0),(10,0),(3,4),(3,4)))
    check("NEAR_PARALLEL_REJECT",rejects(intersection,(0,0),(10,0),(0,1),(10,1+1e-13)))
    check("SYNTHETIC_XI_INTERSECT4P",close_point(intersection((0,5),(10,5),(5,0),(5,10)),(5,5)))
    check("FH_PT_NORMAL_INTERSECTION",close_point(foot_on_line((4,7),(0,0),(10,0)),(4,0)))
    check("FH_PT_NORMAL_OBLIQUE",close_point(foot_on_line((3,7),(0,0),(10,10)),(5,5)))
    check("FH_DEGENERATE_REJECT",rejects(foot_on_line,(3,7),(0,0),(0,0)))
    vendor_cf=foot_on_line((4.,7.),(0.,0.),(10.,0.))
    primary_pr_candidate_cf=foot_on_line((8.,7.),(0.,0.),(10.,0.))
    go=(4.,-20.)
    check("PRIMARY_PR_VS_VENDOR_PT_CF_DISTINCT",not close_point(vendor_cf,primary_pr_candidate_cf))
    check("PRIMARY_PR_VS_VENDOR_PT_PFH_DISTINCT",abs(dist(go,vendor_cf)-20.)<1e-10 and abs(dist(go,primary_pr_candidate_cf)-math.sqrt(416.))<1e-10)
    pm60=(.5,math.sqrt(3)/2.)
    check("HFT_60_VECTOR_ANGLE_ONLY",abs(directed_vector_angle_degrees((1.,0.),pm60)-60.)<1e-10)
    check("HFT_REVERSED_VECTOR_120_NOT_VENDOR_ANGLE4P",abs(directed_vector_angle_degrees((1.,0.),(-pm60[0],-pm60[1]))-120.)<1e-10)
    check("HFT_DEGENERATE_REJECT",rejects(directed_vector_angle_degrees,(0,0),(1,0)))
    print("SYNTHETIC_GEOMETRY_POSITIVE_CASES="+str(len(cases)))
    print("SYNTHETIC_XI_PM_UNITS=10")
    print("SYNTHETIC_XI_PM_PRIME_UNITS=5")
    print("FACAD_ANGLE4P_PRESENTATION_CERTIFIED=false")
    print("PATIENT_NUMERICAL_PARITY_CERTIFIED=false")
    return len(cases)


def source_negative_tests(f,ptv):
    count=0
    variants=[
        ("FORGE_PM_DIRECT_ALIAS",lambda v,p:v["resolutions"]["Mand len"]["dc"].update(direct_alias_allowed=True)),
        ("FORGE_PMPRIME_INTERSECT_REFS",lambda v,p:v["facad_constructions"]["PM'"].update(refs=["Xi","PM"])),
        ("FORGE_PTV_ANCHOR_PR",lambda v,p:p["facad_constructions"]["PtV"].update(refs=["FH","PR"])),
        ("FORGE_CF_INTERSECTION",lambda v,p:p["facad_constructions"]["CF"].update(refs=["FH","Xi"])),
        ("FORGE_PFH_ANGULAR",lambda v,p:p["resolutions"]["PFH"]["facad"].update(calc_type="Angle2ln")),
        ("FORGE_PFH_DIRECT_ALIAS",lambda v,p:p["resolutions"]["PFH"]["dc"].update(direct_alias_allowed=True)),
        ("ERASE_PT_PR_NONALIAS_SAFETY",lambda v,p:p["safety_rules"].update(facad_pt_must_not_alias_dc_pr_ricketts_ptv=False)),
        ("ERASE_PM_NONALIAS_SAFETY",lambda v,p:v["safety_rules"].update(facad_pm_prime_must_not_alias_pm_ricketts=False)),
    ]
    for name,mutator in variants:
        vv,pp=copy.deepcopy(f),copy.deepcopy(ptv)
        mutator(vv,pp)
        if not rejects(lambda: (verify_source(vv),verify_ptv_source(pp))):
            raise AssertionError("Forged manufacturer contract accepted: "+name)
        print("NEGATIVE_TEST_PASS="+name)
        count+=1
    print("SYNTHETIC_SOURCE_NEGATIVE_CASES="+str(count))
    return count


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vendor-source",type=Path,required=True)
    ap.add_argument("--vendor-ptv-source",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    f=json.loads(args.vendor_source.read_text(encoding="utf-8"))
    verify_source(f)
    ptv=None
    if args.vendor_ptv_source is not None:
        ptv=json.loads(args.vendor_ptv_source.read_text(encoding="utf-8"))
        verify_ptv_source(ptv)
    positive=synthetic_tests()
    if args.self_test:
        if ptv is None:
            raise ValueError("Full source-negative tests require --vendor-ptv-source")
        negative=source_negative_tests(f,ptv)
        print("PM_PRIME_PHASE8_SYNTHETIC_SELFTEST_PASS="+str(positive+negative))
    print("SOURCE_LOCK_ONLY=true")
    print("PATIENT_IO=false")
    print("CLINICAL_EDIT_ALLOWED=false")
    print("SYNTHETIC_COORDINATES_ONLY=true")


if __name__=="__main__":
    main()
