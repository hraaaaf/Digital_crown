#!/usr/bin/env python3
"""Research-only synthetic geometry contract for Facad Ricketts F01.13 Phase 8.

Never opens patient records, launches Facad, edits runtime, imports clinical norms
or claims numerical parity. All coordinates below are arbitrary synthetic units.
The fail-closed behavior belongs to this harness, not necessarily Facad runtime.
"""
import argparse
import copy
import csv
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
    check("OPPOSITE_RAYS_SAME_UNSIGNED_LENGTH", dist(xi,intersection(xi,pm,(-5.,-5.),(-5.,5.)))==dist(xi,pp)==5.)
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
    same_projection_pr=foot_on_line((4.,100.),(0.,0.),(10.,0.))
    check("DISTINCT_PR_PT_CAN_SHARE_CF",close_point(vendor_cf,same_projection_pr))
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


def source_negative_tests(f,ptv,summary_rows):
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
        ("FORGE_VENDOR_XIPM_ANGLE_REFS",lambda v,p:v["resolutions"]["Xi-PM/OL"]["facad"].update(refs=["OLa","OLp","Xi","PM"])),
        ("FORGE_VENDOR_FACIAL_CONE_OPERATOR",lambda v,p:v["resolutions"]["Facial cone angle"]["facad"].update(calc_type="Angle2ln")),
        ("FORGE_VENDOR_MAND_ARC_ALIAS",lambda v,p:v["resolutions"]["Mand arc"]["dc"].update(direct_alias_allowed=True)),
    ]
    for name,mutator in variants:
        vv,pp=copy.deepcopy(f),copy.deepcopy(ptv)
        mutator(vv,pp)
        if not rejects(lambda: (verify_source(vv),verify_ptv_source(pp),verify_vendor_angle_source(vv,summary_rows))):
            raise AssertionError("Forged manufacturer contract accepted: "+name)
        print("NEGATIVE_TEST_PASS="+name)
        count+=1

    # A UIA transcription is evidence, not a substitute for source execution.
    for name,field,value in (
        ("FORGE_INTERINCISAL_OPERATOR","Type","Dist2p"),
        ("FORGE_INTERINCISAL_ARG_ORDER","Arg 1","UnknownLandmark"),
        ("FORGE_INTERINCISAL_NORM","Norm","0±0"),
        ("PROMOTE_UIA_TO_VENDOR_RUNTIME","evidence_level","RUNTIME_PARITY_CERTIFIED"),
    ):
        altered=copy.deepcopy(summary_rows)
        matches=[x for x in altered if x.get("analysis")=="Ricketts (13 F)" and x.get("Ceph name")=="InterIncisal"]
        if len(matches)!=1:
            raise AssertionError("13F synthetic negative fixture not uniquely grounded")
        matches[0][field]=value
        if not rejects(verify_vendor_angle_source,f,altered):
            raise AssertionError("Forged 13F Angle4p UIA row incorrectly accepted: "+name)
        print("NEGATIVE_TEST_PASS="+name)
        count+=1
    print("SYNTHETIC_SOURCE_NEGATIVE_CASES="+str(count))
    return count




def clockwise_screen_angle_degrees(v1, v2):
    """SYNTHETIC y-down coordinate model, not proprietary Facad Angle4p."""
    if not all(math.isfinite(v) for v in (*v1, *v2)):
        raise ValueError("Nonfinite synthetic vectors")
    n1, n2=math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        raise ValueError("Degenerate synthetic angle vectors")
    # In y-down screen axes, the determinant-positive turn is clockwise.
    return math.degrees(math.atan2(cross(v1,v2),v1[0]*v2[0]+v1[1]*v2[1]))


def display_angle_reference(raw_degrees, presentation):
    """Pure mathematics: modulo representation, NOT observed vendor UI."""
    if not math.isfinite(raw_degrees):
        raise ValueError("Nonfinite angle")
    if presentation not in ("SIGNED_180", "UNSIGNED_360"):
        raise ValueError("Unknown presentation")
    unsigned=raw_degrees % 360.0
    if presentation == "UNSIGNED_360":
        return unsigned
    # +/-180 has a convention-dependent tie at exactly 180; tests exclude it.
    return unsigned - 360.0 if unsigned > 180.0 else unsigned


def documentary_auto_mode(norm_upper):
    """Facad 3.13 MANUAL description only: norm upper < 135 selects +/-180.
    No claim the saved Facad 3.14 Ricketts analysis uses Auto for this row.
    """
    if not math.isfinite(norm_upper):
        raise ValueError("Nonfinite norm upper bound")
    return "SIGNED_180" if norm_upper < 135.0 else "UNSIGNED_360"


def verify_vendor_angle_source(vendor, summary_rows):
    expected={
        "Xi-PM/OL":["OLa","OLp","PM","Xi"],
        "Facial cone angle":["Go","Me","N","Pog"],
        "Mand arc":["Xi","PM","DC","Xi"],
    }
    for name, refs in expected.items():
        actual=vendor.get("resolutions",{}).get(name,{})
        a=actual.get("facad",{})
        if a.get("calc_type")!="Angle4p" or a.get("refs")!=refs:
            raise ValueError("Original vendor Angle4p contract changed: "+name)
        if actual.get("dc",{}).get("direct_alias_allowed") is not False:
            raise ValueError("Unsourced vendor Angle4p parity enabled: "+name)
    matches=[r for r in summary_rows if r.get("analysis")=="Ricketts (13 F)" and r.get("Ceph name")=="InterIncisal"]
    if len(matches)!=1:
        raise ValueError("Facad 13F InterIncisal vendor UIA row unavailable or ambiguous")
    row=matches[0]
    if row.get("Type")!="Angle4p" or [row.get("Arg "+str(i)) for i in range(1,5)]!=["Iia","Ii","Isa","Is"]:
        raise ValueError("Facad 13F InterIncisal original Angle4p source changed")
    if row.get("Norm")!="130±10" or row.get("evidence_level")!="EDITOR_UIA_TRANSCRIPTION_ONLY":
        raise ValueError("13F source age/authority norm must remain UIA literal only")


def synthetic_angle_presentation_tests():
    """Construct mathematical witnesses; NEVER certify Facad software output."""
    checks={}
    def check(name, condition):
        if not condition:
            raise AssertionError("Angle witness failed: "+name)
        checks[name]=True
        print("SYNTHETIC_ANGLE_CASE_PASS="+name)

    e=(1.,0.)
    q=(0.,1.)
    check("SCREEN_CLOCKWISE_POSITIVE_90",math.isclose(clockwise_screen_angle_degrees(e,q),90.))
    check("SCREEN_COUNTERCLOCKWISE_NEGATIVE_90",math.isclose(clockwise_screen_angle_degrees(e,(0.,-1.)),-90.))
    check("SCREEN_REFLECTION_FLIPS_SIGN",math.isclose(clockwise_screen_angle_degrees(e,(0.,-1.)),-clockwise_screen_angle_degrees(e,q)))
    check("VECTOR_REVERSAL_SUPPLEMENT_90_TO_90_NOT_PARITY",math.isclose(clockwise_screen_angle_degrees((-1.,0.),q),-90.))
    v=(math.cos(math.radians(350)),math.sin(math.radians(350)))
    raw=clockwise_screen_angle_degrees(e,v)
    check("SIGNED_NEG10",math.isclose(display_angle_reference(raw,"SIGNED_180"),-10.,abs_tol=1e-9))
    check("UNSIGNED_350_SAME_RAW_GEOMETRY",math.isclose(display_angle_reference(raw,"UNSIGNED_360"),350.,abs_tol=1e-9))
    check("AUTO_UPPER_134_9_SIGNED",documentary_auto_mode(134.9)=="SIGNED_180")
    check("AUTO_UPPER_135_UNSIGNED",documentary_auto_mode(135.)=="UNSIGNED_360")
    check("AUTO_26_PLUS4_IS_SIGNED_CANDIDATE",documentary_auto_mode(26.+4.)=="SIGNED_180")
    check("AUTO_68_PLUS3_IS_SIGNED_CANDIDATE",documentary_auto_mode(68.+3.)=="SIGNED_180")
    check("AUTO_130_PLUS10_IS_UNSIGNED_CANDIDATE",documentary_auto_mode(130.+10.)=="UNSIGNED_360")
    check("ZERO_DEGREES_REPRESENTED_ZERO",display_angle_reference(0.,"UNSIGNED_360")==0.)
    check("ROUNDING_0_1_DEG_CAN_HIDE_DIFFERENCE",round(12.24,1)==round(12.21,1))
    check("ROUNDING_0_1_DEG_NOT_NUMERICAL_PARITY",12.24!=12.21)
    check("UNSIGNED_WRAP_360_TO_ZERO",display_angle_reference(360.,"UNSIGNED_360")==0.)
    check("GEOMETRIC_ANGLES_DEPEND_ON_LINE_ORDER",math.isclose(clockwise_screen_angle_degrees(e,(0,1)),90.) and math.isclose(clockwise_screen_angle_degrees((0,1),e),-90.))
    check("REFLECTION_ORIENTATION_KEEP_UNSIGNED_MAGNITUDE",abs(clockwise_screen_angle_degrees(e,q))==abs(clockwise_screen_angle_degrees(e,(0.,-1.))))
    check("ZERO_VECTOR_FAIL_CLOSED",rejects(clockwise_screen_angle_degrees,(0.,0.),(1.,0.)))
    check("UNKNOWN_PRESENTATION_FAIL_CLOSED",rejects(display_angle_reference,10.,"AUTO_UNPROVEN_RUNTIME"))
    check("NONFINITE_BOUND_FAIL_CLOSED",rejects(documentary_auto_mode,math.nan))
    print("SYNTHETIC_ANGLE_POSITIVE_CASES="+str(len(checks)))
    print("FACAD_ANGLE4P_RUNTIME_PRESENTATION_VERIFIED=false")
    print("FACAD_ANGLE4P_SOURCE_PROFILE_OPTIONS_VERIFIED=false")
    return len(checks)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vendor-source",type=Path,required=True)
    ap.add_argument("--vendor-ptv-source",type=Path)
    ap.add_argument("--vendor-summary13",type=Path)
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
        if ptv is None or args.vendor_summary13 is None:
            raise ValueError("Phase 9 research source-locked checks require both vendor-ptv-source and vendor-summary13")
        with args.vendor_summary13.open(encoding="utf-8",newline="") as src:
            summary_rows=list(csv.DictReader(src))
        verify_vendor_angle_source(f,summary_rows)
        angles=synthetic_angle_presentation_tests()
        negative=source_negative_tests(f,ptv,summary_rows)
        print("PM_PRIME_PHASE8_SYNTHETIC_SELFTEST_PASS="+str(positive))
        print("FACAD_PHASE9_SYNTHETIC_SELFTEST_PASS="+str(positive+angles+negative))
    print("SOURCE_LOCK_ONLY=true")
    print("PATIENT_IO=false")
    print("CLINICAL_EDIT_ALLOWED=false")
    print("SYNTHETIC_COORDINATES_ONLY=true")


if __name__=="__main__":
    main()
