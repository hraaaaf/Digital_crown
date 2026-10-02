"""LOT06 canonical cephalometric measurements from explicit landmark identities.

This module is additive. Legacy typed adapters remain immutable. Every consumer
here requires versioned canonical landmark IDs and fails closed if they are absent.
"""
from __future__ import annotations
import math
from typing import Callable, Mapping, Optional
from backend.schemas.cephalo_evidence import AvailabilityStatus, LandmarkEvidence, MeasurementEvidence
from backend.services.cephalo_constructions import frankfort_axis_v1, signed_axis_distance_px_v1
from backend.services.cephalo_downs_geometry import downs_facial_angle_deg_v1, downs_y_axis_deg_v1
from backend.services.cephalo_mcnamara_geometry import mcnamara_linear_distance_px_v1
from backend.services.cephalo_ricketts_geometry import (
    ricketts_convexity_signed_distance_px_v1,
    ricketts_e_line_perpendicular_signed_distance_px_v2,
    ricketts_facial_depth_deg_v1,
)
from backend.services.cephalo_tweed_merrifield_geometry import (
    merrifield_z_angle_deg_v1, tweed_fma_deg_v1, tweed_fmia_deg_v1,
)

Point = tuple[float, float]

CANONICAL_V2_METHOD_IDS = {
    "TWEED_FMA_CANONICAL_DEG_V2",
    "TWEED_FMIA_CANONICAL_DEG_V2",
    "MCNAMARA_CO_A_CANONICAL_MM_V2",
    "MCNAMARA_CO_GN_CANONICAL_MM_V2",
    "MCNAMARA_A_NPERP_CANONICAL_MM_V2",
    "MCNAMARA_POG_NPERP_CANONICAL_MM_V2",
    "DOWNS_FACIAL_ANGLE_CANONICAL_DEG_V2",
    "DOWNS_Y_AXIS_CANONICAL_DEG_V2",
    "RICKETTS_FACIAL_DEPTH_CANONICAL_DEG_V2",
    "RICKETTS_CONVEXITY_CANONICAL_MM_V2",
    "RICKETTS_E_LINE_LS_CANONICAL_MM_V3",
    "RICKETTS_E_LINE_LI_CANONICAL_MM_V3",
    "MERRIFIELD_Z_CANONICAL_DEG_V2",
}

def _p(lm: Mapping[str, LandmarkEvidence], key: str) -> Point:
    item=lm[key]; return (item.x,item.y)
def _deps(lm: Mapping[str, LandmarkEvidence], ids: tuple[str,...]):
    present=[lm[i] for i in ids if i in lm]
    if len(present)!=len(ids): return present, AvailabilityStatus.NOT_COMPUTABLE
    if any(x.availability_status!=AvailabilityStatus.AVAILABLE for x in present):
        return present, AvailabilityStatus.NOT_COMPUTABLE
    if len({x.source_image_ref for x in present})!=1:
        return present, AvailabilityStatus.INVALID
    return present, AvailabilityStatus.AVAILABLE

def _measurement(*, namespace:str, name:str, analysis:str, method:str, canonical_id:str,
                 ids:tuple[str,...], lm:Mapping[str,LandmarkEvidence], value:Optional[float],
                 unit:str, requires_calibration:bool=False, calibration_ref:Optional[str]=None,
                 availability:AvailabilityStatus=AvailabilityStatus.AVAILABLE):
    refs=[lm[i].evidence_id for i in ids if i in lm]
    if not refs:
        raise ValueError(f"{method}: no landmark evidence available")
    if availability!=AvailabilityStatus.AVAILABLE: value=None
    evidence=list(refs)
    if calibration_ref: evidence.append(calibration_ref)
    return MeasurementEvidence(
        measurement_id=f"{namespace}:{name}", analysis_id=analysis, method_id=method,
        method_version="2", value=value, unit=unit, landmark_refs=refs,
        calibration_ref=calibration_ref, requires_calibration=requires_calibration,
        evidence_refs=evidence, availability_status=availability,
    )
def _calibrated_px(px:Optional[float], ratio:Optional[float], calibration_ref:Optional[str]):
    if px is None: return None, AvailabilityStatus.INVALID
    if ratio is None or not math.isfinite(ratio) or ratio<=0 or not calibration_ref:
        return None, AvailabilityStatus.NOT_COMPUTABLE
    value=px*ratio
    return (value, AvailabilityStatus.AVAILABLE) if math.isfinite(value) else (None, AvailabilityStatus.INVALID)

def materialize_canonical_analysis_v2_measurements(*, measurement_namespace:str,
        landmarks:Mapping[str,LandmarkEvidence], mm_per_pixel:Optional[float],
        calibration_ref:Optional[str]) -> list[MeasurementEvidence]:
    out=[]
    def angular(name,analysis,method,cid,ids,fn):
        deps,status=_deps(landmarks,ids); value=None
        if not deps:
            return
        if status==AvailabilityStatus.AVAILABLE:
            value=fn(*[_p(landmarks,i) for i in ids])
            if value is None: status=AvailabilityStatus.INVALID
        out.append(_measurement(namespace=measurement_namespace,name=name,analysis=analysis,
            method=method,canonical_id=cid,ids=ids,lm=landmarks,value=value,unit="deg",availability=status))
    def linear(name,analysis,method,cid,ids,px_fn):
        deps,status=_deps(landmarks,ids); value=None
        if not deps:
            return
        if status==AvailabilityStatus.AVAILABLE:
            px=px_fn()
            value,status=_calibrated_px(px,mm_per_pixel,calibration_ref)
        out.append(_measurement(namespace=measurement_namespace,name=name,analysis=analysis,
            method=method,canonical_id=cid,ids=ids,lm=landmarks,value=value,unit="mm",
            requires_calibration=True,calibration_ref=calibration_ref if status==AvailabilityStatus.AVAILABLE else None,
            availability=status))
    angular("TWEED_FMA","TWEED","TWEED_FMA_CANONICAL_DEG_V2","M_FH_GOME_DEG_V1",
        ("Go","Me","Po_anatomic","Or"),tweed_fma_deg_v1)
    angular("TWEED_FMIA","TWEED","TWEED_FMIA_CANONICAL_DEG_V2","M_FMIA_L1_FH_DEG_V1",
        ("L1_apex","L1_incisal","Po_anatomic","Or"),tweed_fmia_deg_v1)
    linear("MCNAMARA_CO_A","MCNAMARA","MCNAMARA_CO_A_CANONICAL_MM_V2","M_CO_A_MM_V1",
        ("Co_anatomic","A"),lambda:mcnamara_linear_distance_px_v1(_p(landmarks,"Co_anatomic"),_p(landmarks,"A")))
    linear("MCNAMARA_CO_GN","MCNAMARA","MCNAMARA_CO_GN_CANONICAL_MM_V2","M_CO_GN_ANATOMIC_MM_V1",
        ("Co_anatomic","Gn_anatomic"),lambda:mcnamara_linear_distance_px_v1(_p(landmarks,"Co_anatomic"),_p(landmarks,"Gn_anatomic")))

    def nperp(target):
        axis=frankfort_axis_v1(_p(landmarks,"Po_anatomic"),_p(landmarks,"Or"))
        return signed_axis_distance_px_v1(_p(landmarks,target),_p(landmarks,"N"),axis)
    linear("MCNAMARA_A_NPERP","MCNAMARA","MCNAMARA_A_NPERP_CANONICAL_MM_V2","M_A_NPERP_MM_V1",
        ("A","N","Po_anatomic","Or"),lambda:nperp("A"))
    linear("MCNAMARA_POG_NPERP","MCNAMARA","MCNAMARA_POG_NPERP_CANONICAL_MM_V2","M_POG_NPERP_MM_V1",
        ("Pog_hard","N","Po_anatomic","Or"),lambda:nperp("Pog_hard"))
    angular("DOWNS_FACIAL_ANGLE","DOWNS","DOWNS_FACIAL_ANGLE_CANONICAL_DEG_V2",
        "M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1",
        ("Po_anatomic","Or","N","Pog_hard"),downs_facial_angle_deg_v1)
    angular("DOWNS_Y_AXIS","DOWNS","DOWNS_Y_AXIS_CANONICAL_DEG_V2",
        "M_DOWNS_Y_AXIS_SGN_FH_DEG_V1",
        ("S","Gn_anatomic","Po_anatomic","Or"),downs_y_axis_deg_v1)
    angular("RICKETTS_FACIAL_DEPTH","RICKETTS","RICKETTS_FACIAL_DEPTH_CANONICAL_DEG_V2",
        "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1",
        ("Po_anatomic","Or","N","Pog_hard"),ricketts_facial_depth_deg_v1)

    def convexity():
        return ricketts_convexity_signed_distance_px_v1(_p(landmarks,"A"),_p(landmarks,"N"),
            _p(landmarks,"Pog_hard"),_p(landmarks,"Po_anatomic"),_p(landmarks,"Or"))
    linear("RICKETTS_CONVEXITY","RICKETTS","RICKETTS_CONVEXITY_CANONICAL_MM_V2",
        "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1",
        ("A","N","Pog_hard","Po_anatomic","Or"),convexity)
    def eline(lip):
        return ricketts_e_line_perpendicular_signed_distance_px_v2(
            _p(landmarks,lip),_p(landmarks,"Prn"),_p(landmarks,"Pog_soft"),
            _p(landmarks,"Po_anatomic"),_p(landmarks,"Or"))
    linear("RICKETTS_E_LINE_LS","RICKETTS","RICKETTS_E_LINE_LS_CANONICAL_MM_V3",
        "M_LS_EPLANE_MM_V1",("Ls_soft","Prn","Pog_soft","Po_anatomic","Or"),lambda:eline("Ls_soft"))
    linear("RICKETTS_E_LINE_LI","RICKETTS","RICKETTS_E_LINE_LI_CANONICAL_MM_V3",
        "M_LI_EPLANE_MM_V1",("Li_soft","Prn","Pog_soft","Po_anatomic","Or"),lambda:eline("Li_soft"))

    angular("MERRIFIELD_Z","MERRIFIELD","MERRIFIELD_Z_CANONICAL_DEG_V2",
        "M_MERRIFIELD_Z_FH_DEG_V1",
        ("Po_anatomic","Or","Pog_soft","Ls_soft","Li_soft"),merrifield_z_angle_deg_v1)
    return out
