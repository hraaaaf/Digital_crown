"""Typed evidence adapter for R6 Tweed/Merrifield patient geometry.

No norms, classification, diagnosis or treatment logic is activated here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
)
from backend.schemas.clinical import CephaloAnalysisResult
from backend.services.cephalo_tweed_merrifield_geometry import (
    merrifield_z_angle_deg_v1,
    tweed_fma_deg_v1,
    tweed_fmia_deg_v1,
    tweed_impa_deg_v1,
)

TWEED_SOURCE_REFERENCES = (
    "doi:10.1016/0096-6347(46)90001-4",
    "Tweed CH. The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis. Angle Orthod. 1954;24:121-169",
)
MERRIFIELD_SOURCE_REFERENCES = (
    "doi:10.1016/0002-9416(66)90250-8",
    "Merrifield LL. The profile line as an aid in critically evaluating facial esthetics. Am J Orthod. 1966;52(11):804-822",
)


@dataclass(frozen=True)
class _R6Spec:
    metric_name: str
    analysis_id: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]
    runtime_section: Optional[str]
    runtime_metric_name: Optional[str]


_R6_SPECS = (
    _R6Spec(
        metric_name="FMA",
        analysis_id="TWEED",
        construction_definition_id="TWEED_FMA_V1",
        method_id="TWEED_FMA_DEG_V1",
        required_landmark_ids=("Go", "Me", "Po", "Or"),
        runtime_section="analyse_osseuse",
        runtime_metric_name="Angle_de_Tweed",
    ),
    _R6Spec(
        metric_name="IMPA",
        analysis_id="TWEED",
        construction_definition_id="TWEED_IMPA_V1",
        method_id="TWEED_IMPA_DEG_V1",
        required_landmark_ids=("L1_apex", "L1_incisal", "Go", "Me"),
        runtime_section="analyse_dentaire",
        runtime_metric_name="IMPA",
    ),
    _R6Spec(
        metric_name="FMIA",
        analysis_id="TWEED",
        construction_definition_id="TWEED_FMIA_V1",
        method_id="TWEED_FMIA_DEG_V1",
        required_landmark_ids=("L1_apex", "L1_incisal", "Po", "Or"),
        runtime_section=None,
        runtime_metric_name=None,
    ),
    _R6Spec(
        metric_name="Z_ANGLE",
        analysis_id="MERRIFIELD",
        construction_definition_id="MERRIFIELD_Z_ANGLE_V1",
        method_id="MERRIFIELD_Z_ANGLE_DEG_V1",
        required_landmark_ids=("Po", "Or", "Pog_soft", "Ls_soft", "Li_soft"),
        runtime_section=None,
        runtime_metric_name=None,
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _computed_value(
    definition_id: str, landmarks: Mapping[str, LandmarkEvidence]
) -> Optional[float]:
    if definition_id == "TWEED_FMA_V1":
        return tweed_fma_deg_v1(
            _point(landmarks, "Go"), _point(landmarks, "Me"),
            _point(landmarks, "Po"), _point(landmarks, "Or"),
        )
    if definition_id == "TWEED_IMPA_V1":
        return tweed_impa_deg_v1(
            _point(landmarks, "L1_apex"), _point(landmarks, "L1_incisal"),
            _point(landmarks, "Go"), _point(landmarks, "Me"),
        )
    if definition_id == "TWEED_FMIA_V1":
        return tweed_fmia_deg_v1(
            _point(landmarks, "L1_apex"), _point(landmarks, "L1_incisal"),
            _point(landmarks, "Po"), _point(landmarks, "Or"),
        )
    if definition_id == "MERRIFIELD_Z_ANGLE_V1":
        return merrifield_z_angle_deg_v1(
            _point(landmarks, "Po"), _point(landmarks, "Or"),
            _point(landmarks, "Pog_soft"), _point(landmarks, "Ls_soft"),
            _point(landmarks, "Li_soft"),
        )
    raise ValueError(f"Unsupported R6 construction {definition_id}")


def materialize_tweed_merrifield_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _R6_SPECS:
        refs: list[str] = []
        missing: list[str] = []
        sources: set[str] = set()
        for landmark_id in spec.required_landmark_ids:
            item = landmarks.get(landmark_id)
            if item is None:
                missing.append(landmark_id)
                continue
            if item.landmark_id != landmark_id:
                raise ValueError(
                    f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
                )
            refs.append(item.evidence_id)
            sources.add(item.source_image_ref)
            if item.availability_status != AvailabilityStatus.AVAILABLE:
                missing.append(landmark_id)

        source_refs = (
            TWEED_SOURCE_REFERENCES if spec.analysis_id == "TWEED" else MERRIFIELD_SOURCE_REFERENCES
        )
        geometry: dict[str, object] = {
            "kind": "cephalometric_angle",
            "analysis": spec.analysis_id,
            "source_references": list(source_refs),
            "required_landmark_ids": list(spec.required_landmark_ids),
        }
        if spec.construction_definition_id == "TWEED_FMA_V1":
            geometry.update({"frankfort_plane": "Po-Or", "mandibular_plane": "Go-Me"})
        elif spec.construction_definition_id == "TWEED_IMPA_V1":
            geometry.update({"lower_incisor_axis": "L1_apex-L1_incisal", "mandibular_plane": "Go-Me"})
        elif spec.construction_definition_id == "TWEED_FMIA_V1":
            geometry.update({
                "lower_incisor_axis": "L1_apex-L1_incisal",
                "frankfort_plane": "Po-Or",
                "axis_orientation_invariant": True,
            })
        else:
            geometry.update({
                "frankfort_plane": "Po-Or",
                "profile_line": "Pog_soft-most_protrusive(Ls_soft,Li_soft)",
                "lip_selection_axis": "Po->Or",
                "axis_orientation_invariant": True,
            })

        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            value = _computed_value(spec.construction_definition_id, landmarks)
            if value is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update(
                    {
                        "computed_angle_deg": round(value, 1),
                        "source_image_ref": next(iter(sources)),
                    }
                )

        out[spec.construction_definition_id] = ConstructionEvidence(
            construction_id=f"{construction_namespace}:{spec.construction_definition_id}",
            definition_id=spec.construction_definition_id,
            definition_version="1",
            landmark_refs=refs,
            missing_landmark_ids=missing,
            geometry=geometry,
            evidence_refs=refs,
            availability_status=availability,
        )
    return out


def adapt_tweed_merrifield_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    out: list[MeasurementEvidence] = []
    for spec in _R6_SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing R6 construction {spec.construction_definition_id}")

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            computed = construction.geometry.get("computed_angle_deg")
            if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                raise ValueError(
                    f"Available R6 construction {spec.construction_definition_id} lacks finite computed_angle_deg"
                )
            computed_value = float(computed)
            if spec.runtime_section and spec.runtime_metric_name:
                section = getattr(result.metrics, spec.runtime_section)
                raw_value = getattr(section, spec.runtime_metric_name).valeur
                if raw_value is None or not math.isfinite(raw_value) or not math.isclose(
                    raw_value, computed_value, rel_tol=0.0, abs_tol=1e-12
                ):
                    raise ValueError(
                        f"Runtime {spec.runtime_metric_name} does not match typed {spec.analysis_id} geometry"
                    )
            value = computed_value
        elif availability == AvailabilityStatus.INVALID:
            value = None
        else:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            value = None

        out.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id=spec.analysis_id,
                method_id=spec.method_id,
                method_version="1",
                value=value,
                unit="deg",
                construction_refs=[construction.construction_id],
                calibration_ref=None,
                requires_calibration=False,
                evidence_refs=[construction.construction_id],
                availability_status=availability,
            )
        )
    return out


R6_CONSTRUCTION_DEFINITIONS = tuple(spec.construction_definition_id for spec in _R6_SPECS)
