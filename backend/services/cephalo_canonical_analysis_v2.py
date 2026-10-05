"""LOT06 canonical cephalometric measurements from explicit landmark identities.

This module is additive. Legacy typed adapters remain immutable. Every consumer
here requires versioned canonical landmark IDs and fails closed if they are absent.
"""
from __future__ import annotations
import math
from typing import Callable, Mapping, Optional
from backend.schemas.cephalo_evidence import AvailabilityStatus, ConstructionEvidence, LandmarkEvidence, MeasurementEvidence
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_GN_CONSTRUCTION_ID,
    RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID,
)
from backend.services.cephalo_canonical_method_bridge import canonical_measurement_id_for_method
from backend.services.cephalo_constructions import frankfort_axis_v1, signed_axis_distance_px_v1
from backend.services.cephalo_downs_geometry import downs_facial_angle_deg_v1, downs_y_axis_deg_v1
from backend.services.cephalo_mcnamara_geometry import mcnamara_linear_distance_px_v1
from backend.services.cephalo_ricketts_geometry import (
    ricketts_constructed_gn_v1,
    ricketts_convexity_signed_distance_px_v1,
    ricketts_e_line_perpendicular_signed_distance_px_v2,
    ricketts_facial_axis_deg_v1,
    ricketts_facial_depth_deg_v1,
    ricketts_l1_apog_inclination_deg_v1,
    ricketts_l1_edge_apog_signed_distance_px_v1,
    ricketts_maxillary_depth_deg_v1,
    ricketts_mandibular_plane_fh_deg_v1,
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
    "RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2",
    "RICKETTS_MANDIBULAR_PLANE_CANONICAL_DEG_V2",
    "RICKETTS_MAXILLARY_DEPTH_CANONICAL_DEG_V2",
    "RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
    "RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2",
    "RICKETTS_CONVEXITY_CANONICAL_MM_V2",
    "RICKETTS_E_LINE_LS_CANONICAL_MM_V3",
    "RICKETTS_E_LINE_LI_CANONICAL_MM_V3",
    "MERRIFIELD_Z_CANONICAL_DEG_V2",
}

def _p(lm: Mapping[str, LandmarkEvidence], key: str) -> Point:
    item=lm[key]; return (item.x,item.y)


def ricketts_facial_axis_from_explicit_identities_v2(
    ba: Point, n: Point, pt_ricketts: Point, pog_hard: Point, go: Point, me: Point
) -> Optional[float]:
    gn_constructed = ricketts_constructed_gn_v1(n, pog_hard, go, me)
    if gn_constructed is None:
        return None
    return ricketts_facial_axis_deg_v1(ba, n, pt_ricketts, gn_constructed)
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
                 construction_refs:tuple[str,...]=(),
                 availability:AvailabilityStatus=AvailabilityStatus.AVAILABLE):
    if canonical_measurement_id_for_method(method) != canonical_id:
        raise ValueError(f"{method}: canonical method bridge drift")
    refs=[lm[i].evidence_id for i in ids if i in lm]
    if not refs:
        raise ValueError(f"{method}: no landmark evidence available")
    if availability!=AvailabilityStatus.AVAILABLE: value=None
    evidence=[*refs,*construction_refs]
    if calibration_ref: evidence.append(calibration_ref)
    return MeasurementEvidence(
        measurement_id=f"{namespace}:{name}", analysis_id=analysis, method_id=method,
        method_version="2", value=value, unit=unit, landmark_refs=refs,
        construction_refs=list(construction_refs),
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
        calibration_ref:Optional[str],
        constructions:Mapping[str,ConstructionEvidence]|None=None) -> list[MeasurementEvidence]:
    out=[]
    constructions = constructions or {}
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
    angular("RICKETTS_MAXILLARY_DEPTH","RICKETTS","RICKETTS_MAXILLARY_DEPTH_CANONICAL_DEG_V2",
        "M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1",
        ("Po_anatomic","Or","N","A"),ricketts_maxillary_depth_deg_v1)
    mandibular_plane_ids=("Po_anatomic","Or","SubGo_Ricketts","Me")
    mandibular_plane_deps,mandibular_plane_status=_deps(landmarks,mandibular_plane_ids)
    mandibular_plane_construction=constructions.get(RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID)
    if mandibular_plane_deps:
        mandibular_plane_value=None
        construction_refs:tuple[str,...]=()
        if mandibular_plane_construction is None:
            mandibular_plane_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            construction_refs=(mandibular_plane_construction.construction_id,)
            if mandibular_plane_construction.availability_status==AvailabilityStatus.INVALID:
                mandibular_plane_status=AvailabilityStatus.INVALID
            elif mandibular_plane_construction.availability_status!=AvailabilityStatus.AVAILABLE:
                mandibular_plane_status=AvailabilityStatus.NOT_COMPUTABLE
            elif mandibular_plane_status==AvailabilityStatus.AVAILABLE:
                mandibular_plane_value=ricketts_mandibular_plane_fh_deg_v1(
                    _p(landmarks,"Po_anatomic"),_p(landmarks,"Or"),
                    _p(landmarks,"SubGo_Ricketts"),_p(landmarks,"Me"),
                )
                if mandibular_plane_value is None:
                    mandibular_plane_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_MANDIBULAR_PLANE",analysis="RICKETTS",
            method="RICKETTS_MANDIBULAR_PLANE_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1",ids=mandibular_plane_ids,
            lm=landmarks,value=mandibular_plane_value,unit="deg",
            construction_refs=construction_refs,availability=mandibular_plane_status,
        ))
    angular("RICKETTS_L1_APOG_INCLINATION","RICKETTS","RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
        "M_RICKETTS_L1_APOG_INCLINATION_DEG_V1",
        ("L1_incisal","L1_apex","A","Pog_hard"),ricketts_l1_apog_inclination_deg_v1)
    linear("RICKETTS_L1_EDGE_APOG","RICKETTS","RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2",
        "M_L1_EDGE_APOG_MM_V1",("L1_incisal","A","Pog_hard","Po_anatomic","Or"),
        lambda:ricketts_l1_edge_apog_signed_distance_px_v1(_p(landmarks,"L1_incisal"),_p(landmarks,"A"),_p(landmarks,"Pog_hard"),_p(landmarks,"Po_anatomic"),_p(landmarks,"Or")))

    facial_axis_ids=("Ba","N","Pt_Ricketts")
    facial_axis_deps,facial_axis_status=_deps(landmarks,facial_axis_ids)
    gn_construction=constructions.get(RICKETTS_GN_CONSTRUCTION_ID)
    if facial_axis_deps:
        facial_axis_value=None
        construction_refs:tuple[str,...]=()
        if gn_construction is None:
            facial_axis_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            construction_refs=(gn_construction.construction_id,)
            if gn_construction.availability_status!=AvailabilityStatus.AVAILABLE:
                facial_axis_status=AvailabilityStatus.NOT_COMPUTABLE
            elif facial_axis_status==AvailabilityStatus.AVAILABLE:
                x=gn_construction.geometry.get("x")
                y=gn_construction.geometry.get("y")
                if not isinstance(x,(int,float)) or not isinstance(y,(int,float)):
                    facial_axis_status=AvailabilityStatus.INVALID
                else:
                    facial_axis_value=ricketts_facial_axis_deg_v1(
                        _p(landmarks,"Ba"),_p(landmarks,"N"),_p(landmarks,"Pt_Ricketts"),
                        (float(x),float(y)),
                    )
                    if facial_axis_value is None:
                        facial_axis_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_FACIAL_AXIS",analysis="RICKETTS",
            method="RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2",
            canonical_id="M_FACIAL_AXIS_RICKETTS_DEG_V1",ids=facial_axis_ids,
            lm=landmarks,value=facial_axis_value,unit="deg",
            construction_refs=construction_refs,availability=facial_axis_status,
        ))

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
