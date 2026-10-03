"""Source-locked Steiner static/1959 extension evidence for LOT08.

This module remains part of the LOT06 scientific authority path: deterministic
geometry only, explicit identities only, no norms/classification/treatment.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus, ConstructionEvidence, LandmarkEvidence, MeasurementEvidence,
)
from backend.services.cephalo_canonical_method_bridge import canonical_measurement_id_for_method
from backend.services.cephalo_steiner_geometry import (
    steiner_l1_dline_deg_v1, steiner_l1_dline_mm_v1, steiner_l1_gogn_deg_v1,
    steiner_l1_nb_mm_v1, steiner_occlusal_sn_deg_v1, steiner_pog_nb_mm_v1,
    steiner_snd_deg_v1, steiner_u1_na_mm_v1,
)

STEINER_PROTOCOL_SOURCE_REFERENCES=(
    "doi:10.1016/0002-9416(53)90082-7",
    "doi:10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2",
    "doi:10.1016/0002-9416(60)90145-7",
)

@dataclass(frozen=True)
class _Spec:
    name:str; definition_id:str; method_id:str; canonical_id:str
    ids:tuple[str,...]; unit:str; requires_calibration:bool

_SPECS=(
    _Spec("SND","STEINER_SND_1959_V1","STEINER_SND_CANONICAL_DEG_V2","M_SND_DEG_V1",("S","N","D_Steiner_1959"),"deg",False),
    _Spec("U1_NA_MM","STEINER_U1_NA_LINEAR_V1","STEINER_U1_NA_CANONICAL_MM_V2","M_U1_NA_MM_V1",("U1_facial_surface","N","A"),"mm",True),
    _Spec("L1_NB_MM","STEINER_L1_NB_LINEAR_V1","STEINER_L1_NB_CANONICAL_MM_V2","M_L1_NB_MM_V1",("L1_facial_surface","N","B"),"mm",True),
    _Spec("POG_NB_MM","STEINER_POG_NB_1959_V1","STEINER_POG_NB_CANONICAL_MM_V2","M_POG_NB_MM_V1",("Pog_hard","N","B"),"mm",True),
    _Spec("L1_GOGN","STEINER_L1_GOGN_V1","STEINER_L1_GOGN_CANONICAL_DEG_V2","M_L1_GOGN_DEG_V1",("L1_apex","L1_incisal","Go","Gn_anatomic"),"deg",False),
    _Spec("OCCLUSAL_SN","STEINER_OCCLUSAL_SN_1953_V1","STEINER_OCCLUSAL_SN_CANONICAL_DEG_V2","M_OCCLUSAL_PLANE_SN_DEG_V1",("S","N","Occ_Steiner_Ant","Occ_Steiner_Post"),"deg",False),
    _Spec("L1_DLINE_MM","STEINER_L1_DLINE_LINEAR_1959_V1","STEINER_L1_DLINE_CANONICAL_MM_V2","M_L1_DLINE_MM_V1",("L1_facial_surface","D_Steiner_1959","Go","Gn_anatomic"),"mm",True),
    _Spec("L1_DLINE_DEG","STEINER_L1_DLINE_ANGULAR_1959_V1","STEINER_L1_DLINE_CANONICAL_DEG_V2","M_L1_DLINE_DEG_V1",("L1_apex","L1_incisal","D_Steiner_1959","Go","Gn_anatomic"),"deg",False),
)

def _point(lm:Mapping[str,LandmarkEvidence], key:str):
    x=lm[key]; return (x.x,x.y)

def _compute(spec:_Spec,lm:Mapping[str,LandmarkEvidence],ratio:Optional[float]):
    p=lambda k:_point(lm,k)
    if spec.name=="SND": return steiner_snd_deg_v1(p("S"),p("N"),p("D_Steiner_1959"))
    if spec.name=="U1_NA_MM": return steiner_u1_na_mm_v1(p("U1_facial_surface"),p("N"),p("A"),ratio)
    if spec.name=="L1_NB_MM": return steiner_l1_nb_mm_v1(p("L1_facial_surface"),p("N"),p("B"),ratio)
    if spec.name=="POG_NB_MM": return steiner_pog_nb_mm_v1(p("Pog_hard"),p("N"),p("B"),ratio)
    if spec.name=="L1_GOGN": return steiner_l1_gogn_deg_v1(p("L1_apex"),p("L1_incisal"),p("Go"),p("Gn_anatomic"))
    if spec.name=="OCCLUSAL_SN": return steiner_occlusal_sn_deg_v1(p("S"),p("N"),p("Occ_Steiner_Ant"),p("Occ_Steiner_Post"))
    if spec.name=="L1_DLINE_MM": return steiner_l1_dline_mm_v1(p("L1_facial_surface"),p("D_Steiner_1959"),p("Go"),p("Gn_anatomic"),ratio)
    if spec.name=="L1_DLINE_DEG": return steiner_l1_dline_deg_v1(p("L1_apex"),p("L1_incisal"),p("Go"),p("Gn_anatomic"))
    raise ValueError(spec.name)

def materialize_steiner_protocol_evidence(*, landmarks:Mapping[str,LandmarkEvidence],
        construction_namespace:str, measurement_namespace:str,
        mm_per_pixel:Optional[float], calibration_ref:Optional[str]):
    constructions:dict[str,ConstructionEvidence]={}; measurements:list[MeasurementEvidence]=[]
    for spec in _SPECS:
        if canonical_measurement_id_for_method(spec.method_id)!=spec.canonical_id:
            raise ValueError(f"{spec.method_id}: canonical bridge drift")
        present=[landmarks[k] for k in spec.ids if k in landmarks]
        missing=[k for k in spec.ids if k not in landmarks or landmarks[k].availability_status!=AvailabilityStatus.AVAILABLE]
        refs=[x.evidence_id for x in present]
        sources={x.source_image_ref for x in present}
        status=AvailabilityStatus.AVAILABLE
        value=None
        if missing:
            status=AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources)!=1:
            status=AvailabilityStatus.INVALID
        elif spec.requires_calibration and (mm_per_pixel is None or not math.isfinite(mm_per_pixel) or mm_per_pixel<=0 or not calibration_ref):
            status=AvailabilityStatus.NOT_COMPUTABLE
        else:
            value=_compute(spec,landmarks,mm_per_pixel)
            if value is None or not math.isfinite(value): status=AvailabilityStatus.INVALID; value=None
        cid=f"{construction_namespace}:{spec.definition_id}"
        geometry={"kind":"cephalometric_measurement_construction","analysis":"STEINER_PROTOCOL_V1","canonical_measurement_id":spec.canonical_id,"required_landmark_ids":list(spec.ids),"source_references":list(STEINER_PROTOCOL_SOURCE_REFERENCES)}
        if status==AvailabilityStatus.AVAILABLE: geometry["computed_value"]=float(value)
        construction=ConstructionEvidence(construction_id=cid,definition_id=spec.definition_id,definition_version="1",landmark_refs=refs,missing_landmark_ids=missing,geometry=geometry,evidence_refs=refs,availability_status=status)
        constructions[spec.definition_id]=construction
        evidence=[cid]+([calibration_ref] if calibration_ref and spec.requires_calibration else [])
        measurements.append(MeasurementEvidence(measurement_id=f"{measurement_namespace}:{spec.name}",analysis_id="STEINER_PROTOCOL_V1",method_id=spec.method_id,method_version="2",value=float(value) if status==AvailabilityStatus.AVAILABLE else None,unit=spec.unit,landmark_refs=refs,construction_refs=[cid],calibration_ref=calibration_ref if status==AvailabilityStatus.AVAILABLE and spec.requires_calibration else None,requires_calibration=spec.requires_calibration,evidence_refs=evidence,availability_status=status))
    return constructions,measurements

STEINER_PROTOCOL_METHOD_IDS=tuple(x.method_id for x in _SPECS)
