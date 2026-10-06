"""LOT06 canonical cephalometric measurements from explicit landmark identities.

This module is additive. Legacy typed adapters remain immutable. Every consumer
here requires versioned canonical landmark IDs and fails closed if they are absent.
"""
from __future__ import annotations
import math
from typing import Callable, Mapping, Optional
from backend.schemas.cephalo_evidence import AvailabilityStatus, ConstructionEvidence, LandmarkEvidence, LandmarkOrigin, MeasurementEvidence
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_CF_CONSTRUCTION_ID,
    RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID,
    RICKETTS_GN_CONSTRUCTION_ID,
    RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID,
    RICKETTS_PTV_CONSTRUCTION_ID,
    RICKETTS_XI_CONSTRUCTION_ID,
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
    ricketts_line_angle_acute_deg_v1,
    ricketts_signed_projection_on_plane_px_v1,
    ricketts_upper_lip_length_px_v1,
    ricketts_u1_apog_inclination_deg_v1,
    ricketts_l1_occlusal_extrusion_signed_px_v1,
    ricketts_lower_facial_height_ans_xi_pm_deg_v1,
    ricketts_mandibular_arc_deg_v1,
    ricketts_maxillary_depth_deg_v1,
    ricketts_maxillary_height_n_cf_a_deg_v1,
    ricketts_palatal_plane_fh_deg_v1,
    ricketts_u6_distal_to_ptv_signed_px_v1,
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
    "RICKETTS_MAXILLARY_DEPTH_CANONICAL_DEG_V2",
    "RICKETTS_MANDIBULAR_PLANE_FH_CANONICAL_DEG_V2",
    "RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
    "RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2",
    "RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2",
    "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2",
    "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2",
    "RICKETTS_U6_PTV_CANONICAL_MM_V2",
    "RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2",
    "RICKETTS_OVERJET_FOP_CANONICAL_MM_V2",
    "RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2",
    "RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2",
    "RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
    "RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2",
    "RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2",
    "RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2",
    "RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2",
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

    ricketts_mp_ids=("Po_anatomic","Or","MP_ANGLE_INFERIOR_Ricketts","Me")
    ricketts_mp_deps,ricketts_mp_status=_deps(landmarks,ricketts_mp_ids)
    ricketts_mp_construction=constructions.get(RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID)
    if ricketts_mp_deps:
        ricketts_mp_value=None
        ricketts_mp_refs:tuple[str,...]=()
        if ricketts_mp_construction is None:
            ricketts_mp_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_mp_refs=(ricketts_mp_construction.construction_id,)
            if ricketts_mp_construction.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_mp_status=AvailabilityStatus.NOT_COMPUTABLE
            elif ricketts_mp_status==AvailabilityStatus.AVAILABLE:
                point_x=ricketts_mp_construction.geometry.get("point_x")
                point_y=ricketts_mp_construction.geometry.get("point_y")
                direction_x=ricketts_mp_construction.geometry.get("direction_x")
                direction_y=ricketts_mp_construction.geometry.get("direction_y")
                values=(point_x,point_y,direction_x,direction_y)
                if not all(isinstance(value,(int,float)) for value in values):
                    ricketts_mp_status=AvailabilityStatus.INVALID
                else:
                    p1=(float(point_x),float(point_y))
                    p2=(p1[0]+float(direction_x),p1[1]+float(direction_y))
                    ricketts_mp_value=ricketts_mandibular_plane_fh_deg_v1(
                        _p(landmarks,"Po_anatomic"),_p(landmarks,"Or"),p1,p2,
                    )
                    if ricketts_mp_value is None:
                        ricketts_mp_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_MANDIBULAR_PLANE_FH",analysis="RICKETTS",
            method="RICKETTS_MANDIBULAR_PLANE_FH_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1",ids=ricketts_mp_ids,
            lm=landmarks,value=ricketts_mp_value,unit="deg",
            construction_refs=ricketts_mp_refs,availability=ricketts_mp_status,
        ))
    angular("RICKETTS_L1_APOG_INCLINATION","RICKETTS","RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
        "M_RICKETTS_L1_APOG_INCLINATION_DEG_V1",
        ("L1_incisal","L1_apex","A","Pog_hard"),ricketts_l1_apog_inclination_deg_v1)
    linear("RICKETTS_L1_EDGE_APOG","RICKETTS","RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2",
        "M_L1_EDGE_APOG_MM_V1",("L1_incisal","A","Pog_hard","Po_anatomic","Or"),
        lambda:ricketts_l1_edge_apog_signed_distance_px_v1(_p(landmarks,"L1_incisal"),_p(landmarks,"A"),_p(landmarks,"Pog_hard"),_p(landmarks,"Po_anatomic"),_p(landmarks,"Or")))


    # Atlas/complete Ricketts dental Wave A. FOP direction is stored by the
    # canonical construction; its first->second orientation is the source-locked
    # premolar->molar/anterior-posterior axis and is not replaced by screen X.
    def _fop_projection_measure(
        *,
        name: str,
        method: str,
        canonical_id: str,
        first_id: str,
        second_id: str,
        require_manual: bool,
    ) -> None:
        ids=(first_id,second_id)
        deps,status=_deps(landmarks,ids)
        if require_manual:
            for landmark_id in ids:
                item=landmarks.get(landmark_id)
                if (
                    item is not None
                    and item.origin not in {LandmarkOrigin.MANUAL,LandmarkOrigin.MANUAL_CORRECTED}
                ):
                    status=AvailabilityStatus.NOT_COMPUTABLE
        if not deps:
            return
        value=None
        refs:tuple[str,...]=()
        fop=constructions.get(RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID)
        if fop is None:
            status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            refs=(fop.construction_id,)
            if fop.availability_status!=AvailabilityStatus.AVAILABLE:
                status=fop.availability_status
            elif status==AvailabilityStatus.AVAILABLE:
                direction_x=fop.geometry.get("direction_x")
                direction_y=fop.geometry.get("direction_y")
                source_image_ref=fop.geometry.get("source_image_ref")
                if (
                    not isinstance(direction_x,(int,float))
                    or not isinstance(direction_y,(int,float))
                    or source_image_ref != landmarks[first_id].source_image_ref
                    or source_image_ref != landmarks[second_id].source_image_ref
                ):
                    status=AvailabilityStatus.INVALID
                else:
                    px=ricketts_signed_projection_on_plane_px_v1(
                        _p(landmarks,first_id),
                        _p(landmarks,second_id),
                        (float(direction_x),float(direction_y)),
                    )
                    value,status=_calibrated_px(px,mm_per_pixel,calibration_ref)
        out.append(_measurement(
            namespace=measurement_namespace,name=name,analysis="RICKETTS",
            method=method,canonical_id=canonical_id,ids=ids,lm=landmarks,
            value=value,unit="mm",requires_calibration=True,
            calibration_ref=calibration_ref if status==AvailabilityStatus.AVAILABLE else None,
            construction_refs=refs,availability=status,
        ))

    _fop_projection_measure(
        name="RICKETTS_MOLAR_RELATION_FOP",
        method="RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2",
        canonical_id="M_RICKETTS_MOLAR_RELATION_FOP_MM_V1",
        first_id="L6_DISTAL_Ricketts",
        second_id="U6_DISTAL_Ricketts",
        require_manual=True,
    )
    _fop_projection_measure(
        name="RICKETTS_CANINE_RELATION_FOP",
        method="RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2",
        canonical_id="M_RICKETTS_CANINE_RELATION_FOP_MM_V1",
        first_id="L3_CUSP_Ricketts",
        second_id="U3_CUSP_Ricketts",
        require_manual=True,
    )
    _fop_projection_measure(
        name="RICKETTS_OVERJET_FOP",
        method="RICKETTS_OVERJET_FOP_CANONICAL_MM_V2",
        canonical_id="M_RICKETTS_OVERJET_FOP_MM_V1",
        first_id="L1_incisal",
        second_id="U1_incisal",
        require_manual=False,
    )

    angular(
        "RICKETTS_U1_APOG_INCLINATION","RICKETTS",
        "RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2",
        "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1",
        ("U1_incisal","U1_apex","A","Pog_hard"),
        ricketts_u1_apog_inclination_deg_v1,
    )


    # Atlas/33 Wave B source-locked measurements.
    #14 (FOP-to-Xi signed distance) and #18 (commissure-to-FOP signed distance)
    # remain intentionally absent from runtime because their signed normal
    # orientation is not yet deterministic from the source contract.

    ricketts_op_inclination_ids=("Pm_Ricketts",)
    ricketts_op_inclination_deps,ricketts_op_inclination_status=_deps(
        landmarks,ricketts_op_inclination_ids
    )
    ricketts_op_fop=constructions.get(RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID)
    ricketts_op_xi=constructions.get(RICKETTS_XI_CONSTRUCTION_ID)
    if ricketts_op_inclination_deps:
        ricketts_op_inclination_value=None
        ricketts_op_inclination_refs:tuple[str,...]=()
        if (
            landmarks["Pm_Ricketts"].origin
            not in {LandmarkOrigin.MANUAL,LandmarkOrigin.MANUAL_CORRECTED}
        ):
            ricketts_op_inclination_status=AvailabilityStatus.NOT_COMPUTABLE
        if ricketts_op_fop is None or ricketts_op_xi is None:
            ricketts_op_inclination_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_op_inclination_refs=(
                ricketts_op_fop.construction_id,
                ricketts_op_xi.construction_id,
            )
            if ricketts_op_fop.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_op_inclination_status=ricketts_op_fop.availability_status
            elif ricketts_op_xi.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_op_inclination_status=ricketts_op_xi.availability_status
            elif ricketts_op_inclination_status==AvailabilityStatus.AVAILABLE:
                fx=ricketts_op_fop.geometry.get("direction_x")
                fy=ricketts_op_fop.geometry.get("direction_y")
                xi_x=ricketts_op_xi.geometry.get("x")
                xi_y=ricketts_op_xi.geometry.get("y")
                fop_source=ricketts_op_fop.geometry.get("source_image_ref")
                xi_source=ricketts_op_xi.geometry.get("source_image_ref")
                pm=landmarks["Pm_Ricketts"]
                if (
                    not all(isinstance(v,(int,float)) for v in (fx,fy,xi_x,xi_y))
                    or fop_source != xi_source
                    or fop_source != pm.source_image_ref
                ):
                    ricketts_op_inclination_status=AvailabilityStatus.INVALID
                else:
                    ricketts_op_inclination_value=ricketts_line_angle_acute_deg_v1(
                        (float(fx),float(fy)),
                        (pm.x-float(xi_x),pm.y-float(xi_y)),
                    )
                    if ricketts_op_inclination_value is None:
                        ricketts_op_inclination_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_OCCLUSAL_PLANE_XIPM",
            analysis="RICKETTS",
            method="RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1",
            ids=ricketts_op_inclination_ids,lm=landmarks,
            value=ricketts_op_inclination_value,unit="deg",
            construction_refs=ricketts_op_inclination_refs,
            availability=ricketts_op_inclination_status,
        ))

    ricketts_lip_ids=("ANS","LABIAL_COMMISSURE_Ricketts")
    ricketts_lip_deps,ricketts_lip_status=_deps(landmarks,ricketts_lip_ids)
    if ricketts_lip_deps:
        ricketts_lip_value=None
        if (
            "LABIAL_COMMISSURE_Ricketts" in landmarks
            and landmarks["LABIAL_COMMISSURE_Ricketts"].origin
            not in {LandmarkOrigin.MANUAL,LandmarkOrigin.MANUAL_CORRECTED}
        ):
            ricketts_lip_status=AvailabilityStatus.NOT_COMPUTABLE
        if ricketts_lip_status==AvailabilityStatus.AVAILABLE:
            px=ricketts_upper_lip_length_px_v1(
                _p(landmarks,"ANS"),_p(landmarks,"LABIAL_COMMISSURE_Ricketts")
            )
            ricketts_lip_value,ricketts_lip_status=_calibrated_px(
                px,mm_per_pixel,calibration_ref
            )
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_UPPER_LIP_LENGTH",
            analysis="RICKETTS",method="RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2",
            canonical_id="M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1",
            ids=ricketts_lip_ids,lm=landmarks,value=ricketts_lip_value,unit="mm",
            requires_calibration=True,
            calibration_ref=calibration_ref if ricketts_lip_status==AvailabilityStatus.AVAILABLE else None,
            availability=ricketts_lip_status,
        ))

    ricketts_taper_ids=("N","Pog_hard")
    ricketts_taper_deps,ricketts_taper_status=_deps(landmarks,ricketts_taper_ids)
    ricketts_taper_mp=constructions.get(RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID)
    if ricketts_taper_deps:
        ricketts_taper_value=None
        ricketts_taper_refs:tuple[str,...]=()
        if ricketts_taper_mp is None:
            ricketts_taper_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_taper_refs=(ricketts_taper_mp.construction_id,)
            if ricketts_taper_mp.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_taper_status=ricketts_taper_mp.availability_status
            elif ricketts_taper_status==AvailabilityStatus.AVAILABLE:
                dx=ricketts_taper_mp.geometry.get("direction_x")
                dy=ricketts_taper_mp.geometry.get("direction_y")
                source=ricketts_taper_mp.geometry.get("source_image_ref")
                if (
                    not all(isinstance(v,(int,float)) for v in (dx,dy))
                    or source != landmarks["N"].source_image_ref
                    or source != landmarks["Pog_hard"].source_image_ref
                ):
                    ricketts_taper_status=AvailabilityStatus.INVALID
                else:
                    ricketts_taper_value=ricketts_line_angle_acute_deg_v1(
                        (float(dx),float(dy)),
                        (
                            landmarks["Pog_hard"].x-landmarks["N"].x,
                            landmarks["Pog_hard"].y-landmarks["N"].y,
                        ),
                    )
                    if ricketts_taper_value is None:
                        ricketts_taper_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_FACIAL_TAPER",
            analysis="RICKETTS",method="RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1",
            ids=ricketts_taper_ids,lm=landmarks,value=ricketts_taper_value,unit="deg",
            construction_refs=ricketts_taper_refs,availability=ricketts_taper_status,
        ))

    ricketts_mx_height_ids=("N","A")
    ricketts_mx_height_deps,ricketts_mx_height_status=_deps(
        landmarks,ricketts_mx_height_ids
    )
    ricketts_cf=constructions.get(RICKETTS_CF_CONSTRUCTION_ID)
    if ricketts_mx_height_deps:
        ricketts_mx_height_value=None
        ricketts_mx_height_refs:tuple[str,...]=()
        if ricketts_cf is None:
            ricketts_mx_height_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_mx_height_refs=(ricketts_cf.construction_id,)
            if ricketts_cf.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_mx_height_status=ricketts_cf.availability_status
            elif ricketts_mx_height_status==AvailabilityStatus.AVAILABLE:
                cf_x=ricketts_cf.geometry.get("x")
                cf_y=ricketts_cf.geometry.get("y")
                source=ricketts_cf.geometry.get("source_image_ref")
                if (
                    not all(isinstance(v,(int,float)) for v in (cf_x,cf_y))
                    or source != landmarks["N"].source_image_ref
                    or source != landmarks["A"].source_image_ref
                ):
                    ricketts_mx_height_status=AvailabilityStatus.INVALID
                else:
                    ricketts_mx_height_value=ricketts_maxillary_height_n_cf_a_deg_v1(
                        _p(landmarks,"N"),(float(cf_x),float(cf_y)),_p(landmarks,"A")
                    )
                    if ricketts_mx_height_value is None:
                        ricketts_mx_height_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_MAXILLARY_HEIGHT",
            analysis="RICKETTS",method="RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1",
            ids=ricketts_mx_height_ids,lm=landmarks,value=ricketts_mx_height_value,unit="deg",
            construction_refs=ricketts_mx_height_refs,availability=ricketts_mx_height_status,
        ))

    ricketts_palatal_ids=("Po_anatomic","Or","ANS","PNS_Ricketts")
    ricketts_palatal_deps,ricketts_palatal_status=_deps(landmarks,ricketts_palatal_ids)
    if ricketts_palatal_deps:
        ricketts_palatal_value=None
        if (
            "PNS_Ricketts" in landmarks
            and landmarks["PNS_Ricketts"].origin
            not in {LandmarkOrigin.MANUAL,LandmarkOrigin.MANUAL_CORRECTED}
        ):
            ricketts_palatal_status=AvailabilityStatus.NOT_COMPUTABLE
        if ricketts_palatal_status==AvailabilityStatus.AVAILABLE:
            ricketts_palatal_value=ricketts_palatal_plane_fh_deg_v1(
                _p(landmarks,"Po_anatomic"),_p(landmarks,"Or"),
                _p(landmarks,"ANS"),_p(landmarks,"PNS_Ricketts")
            )
            if ricketts_palatal_value is None:
                ricketts_palatal_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_PALATAL_PLANE_FH",
            analysis="RICKETTS",method="RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_PALATAL_PLANE_FH_DEG_V1",
            ids=ricketts_palatal_ids,lm=landmarks,value=ricketts_palatal_value,unit="deg",
            availability=ricketts_palatal_status,
        ))

    ricketts_extrusion_ids=("L1_incisal","L1_apex")
    ricketts_extrusion_deps,ricketts_extrusion_status=_deps(landmarks,ricketts_extrusion_ids)
    ricketts_fop=constructions.get(RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID)
    if ricketts_extrusion_deps:
        ricketts_extrusion_value=None
        ricketts_extrusion_refs:tuple[str,...]=()
        if ricketts_fop is None:
            ricketts_extrusion_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_extrusion_refs=(ricketts_fop.construction_id,)
            if ricketts_fop.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_extrusion_status=ricketts_fop.availability_status
            elif ricketts_extrusion_status==AvailabilityStatus.AVAILABLE:
                point_x=ricketts_fop.geometry.get("point_x")
                point_y=ricketts_fop.geometry.get("point_y")
                direction_x=ricketts_fop.geometry.get("direction_x")
                direction_y=ricketts_fop.geometry.get("direction_y")
                source_image_ref=ricketts_fop.geometry.get("source_image_ref")
                values=(point_x,point_y,direction_x,direction_y)
                if (
                    not all(isinstance(value,(int,float)) for value in values)
                    or source_image_ref != landmarks["L1_incisal"].source_image_ref
                ):
                    ricketts_extrusion_status=AvailabilityStatus.INVALID
                else:
                    px=ricketts_l1_occlusal_extrusion_signed_px_v1(
                        _p(landmarks,"L1_incisal"),
                        _p(landmarks,"L1_apex"),
                        (float(point_x),float(point_y)),
                        (float(direction_x),float(direction_y)),
                    )
                    ricketts_extrusion_value,ricketts_extrusion_status=_calibrated_px(
                        px,mm_per_pixel,calibration_ref
                    )
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_L1_OCCLUSAL_EXTRUSION",analysis="RICKETTS",
            method="RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2",
            canonical_id="M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1",ids=ricketts_extrusion_ids,
            lm=landmarks,value=ricketts_extrusion_value,unit="mm",
            requires_calibration=True,
            calibration_ref=calibration_ref if ricketts_extrusion_status==AvailabilityStatus.AVAILABLE else None,
            construction_refs=ricketts_extrusion_refs,availability=ricketts_extrusion_status,
        ))

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

    ricketts_lfh_ids=("ANS","Pm_Ricketts")
    ricketts_lfh_deps,ricketts_lfh_status=_deps(landmarks,ricketts_lfh_ids)
    if (
        "Pm_Ricketts" in landmarks
        and landmarks["Pm_Ricketts"].origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
    ):
        ricketts_lfh_status=AvailabilityStatus.NOT_COMPUTABLE
    ricketts_xi=constructions.get(RICKETTS_XI_CONSTRUCTION_ID)
    if ricketts_lfh_deps:
        ricketts_lfh_value=None
        ricketts_lfh_refs:tuple[str,...]=()
        if ricketts_xi is None:
            ricketts_lfh_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_lfh_refs=(ricketts_xi.construction_id,)
            if ricketts_xi.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_lfh_status=ricketts_xi.availability_status
            elif ricketts_lfh_status==AvailabilityStatus.AVAILABLE:
                x=ricketts_xi.geometry.get("x")
                y=ricketts_xi.geometry.get("y")
                source_image_ref=ricketts_xi.geometry.get("source_image_ref")
                if (
                    not isinstance(x,(int,float))
                    or not isinstance(y,(int,float))
                    or source_image_ref != landmarks["ANS"].source_image_ref
                ):
                    ricketts_lfh_status=AvailabilityStatus.INVALID
                else:
                    ricketts_lfh_value=ricketts_lower_facial_height_ans_xi_pm_deg_v1(
                        _p(landmarks,"ANS"),
                        (float(x),float(y)),
                        _p(landmarks,"Pm_Ricketts"),
                    )
                    if ricketts_lfh_value is None:
                        ricketts_lfh_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_LOWER_FACIAL_HEIGHT",analysis="RICKETTS",
            method="RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2",
            canonical_id="M_ORAL_GNOMON_ANS_XI_PM_DEG_V1",ids=ricketts_lfh_ids,
            lm=landmarks,value=ricketts_lfh_value,unit="deg",
            construction_refs=ricketts_lfh_refs,availability=ricketts_lfh_status,
        ))

    ricketts_arc_ids=("DC_Ricketts","Pm_Ricketts")
    ricketts_arc_deps,ricketts_arc_status=_deps(landmarks,ricketts_arc_ids)
    if (
        "DC_Ricketts" in landmarks
        and landmarks["DC_Ricketts"].origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
    ):
        ricketts_arc_status=AvailabilityStatus.NOT_COMPUTABLE
    if (
        "Pm_Ricketts" in landmarks
        and landmarks["Pm_Ricketts"].origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
    ):
        ricketts_arc_status=AvailabilityStatus.NOT_COMPUTABLE
    ricketts_arc_xi=constructions.get(RICKETTS_XI_CONSTRUCTION_ID)
    if ricketts_arc_deps:
        ricketts_arc_value=None
        ricketts_arc_refs:tuple[str,...]=()
        if ricketts_arc_xi is None:
            ricketts_arc_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_arc_refs=(ricketts_arc_xi.construction_id,)
            if ricketts_arc_xi.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_arc_status=ricketts_arc_xi.availability_status
            elif ricketts_arc_status==AvailabilityStatus.AVAILABLE:
                x=ricketts_arc_xi.geometry.get("x")
                y=ricketts_arc_xi.geometry.get("y")
                source_image_ref=ricketts_arc_xi.geometry.get("source_image_ref")
                if (
                    not isinstance(x,(int,float))
                    or not isinstance(y,(int,float))
                    or source_image_ref != landmarks["DC_Ricketts"].source_image_ref
                    or source_image_ref != landmarks["Pm_Ricketts"].source_image_ref
                ):
                    ricketts_arc_status=AvailabilityStatus.INVALID
                else:
                    ricketts_arc_value=ricketts_mandibular_arc_deg_v1(
                        _p(landmarks,"DC_Ricketts"),
                        (float(x),float(y)),
                        _p(landmarks,"Pm_Ricketts"),
                    )
                    if ricketts_arc_value is None:
                        ricketts_arc_status=AvailabilityStatus.INVALID
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_MANDIBULAR_ARC",analysis="RICKETTS",
            method="RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2",
            canonical_id="M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1",ids=ricketts_arc_ids,
            lm=landmarks,value=ricketts_arc_value,unit="deg",
            construction_refs=ricketts_arc_refs,availability=ricketts_arc_status,
        ))

    ricketts_u6_ids=("U6_DISTAL_Ricketts",)
    ricketts_u6_deps,ricketts_u6_status=_deps(landmarks,ricketts_u6_ids)
    if (
        "U6_DISTAL_Ricketts" in landmarks
        and landmarks["U6_DISTAL_Ricketts"].origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
    ):
        ricketts_u6_status=AvailabilityStatus.NOT_COMPUTABLE
    ricketts_ptv=constructions.get(RICKETTS_PTV_CONSTRUCTION_ID)
    if ricketts_u6_deps:
        ricketts_u6_value=None
        ricketts_u6_refs:tuple[str,...]=()
        if ricketts_ptv is None:
            ricketts_u6_status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            ricketts_u6_refs=(ricketts_ptv.construction_id,)
            if ricketts_ptv.availability_status!=AvailabilityStatus.AVAILABLE:
                ricketts_u6_status=ricketts_ptv.availability_status
            elif ricketts_u6_status==AvailabilityStatus.AVAILABLE:
                point_x=ricketts_ptv.geometry.get("point_x")
                point_y=ricketts_ptv.geometry.get("point_y")
                anterior_x=ricketts_ptv.geometry.get("anterior_x")
                anterior_y=ricketts_ptv.geometry.get("anterior_y")
                source_image_ref=ricketts_ptv.geometry.get("source_image_ref")
                if (
                    not isinstance(point_x,(int,float))
                    or not isinstance(point_y,(int,float))
                    or not isinstance(anterior_x,(int,float))
                    or not isinstance(anterior_y,(int,float))
                    or source_image_ref != landmarks["U6_DISTAL_Ricketts"].source_image_ref
                ):
                    ricketts_u6_status=AvailabilityStatus.INVALID
                else:
                    px=ricketts_u6_distal_to_ptv_signed_px_v1(
                        _p(landmarks,"U6_DISTAL_Ricketts"),
                        (float(point_x),float(point_y)),
                        (float(anterior_x),float(anterior_y)),
                    )
                    ricketts_u6_value,ricketts_u6_status=_calibrated_px(
                        px,mm_per_pixel,calibration_ref
                    )
        out.append(_measurement(
            namespace=measurement_namespace,name="RICKETTS_U6_PTV",analysis="RICKETTS",
            method="RICKETTS_U6_PTV_CANONICAL_MM_V2",
            canonical_id="M_U6_PTV_MM_V1",ids=ricketts_u6_ids,
            lm=landmarks,value=ricketts_u6_value,unit="mm",
            requires_calibration=True,
            calibration_ref=calibration_ref if ricketts_u6_status==AvailabilityStatus.AVAILABLE else None,
            construction_refs=ricketts_u6_refs,availability=ricketts_u6_status,
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
