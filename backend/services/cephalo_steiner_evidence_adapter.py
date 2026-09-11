"""Typed evidence adapter for the Steiner skeletal slice.

This module materializes versioned SNA, SNB, ANB and SN-MP geometry from source
landmarks. SNA/SNB/ANB remain parity-bound to the legacy runtime; SN-MP is typed
patient geometry with no duplicate legacy field. It contains no norms,
classification, diagnosis, growth projection or treatment logic.

Compatibility note: the established skeletal rematerialization seam is also used
as the composition point for R6 Tweed/Merrifield evidence so creation and landmark
edits share one audited path. R6 keeps independent analysis IDs, method IDs and
namespaces; it is not reclassified as Steiner evidence.
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
from backend.services.cephalo_steiner_geometry import (
    steiner_anb_deg_v1,
    steiner_sna_deg_v1,
    steiner_snb_deg_v1,
    steiner_sn_mp_deg_v1,
)
from backend.services.cephalo_tweed_merrifield_evidence import (
    adapt_tweed_merrifield_measurements,
    materialize_tweed_merrifield_constructions,
)

STEINER_SOURCE_REFERENCES = (
    "doi:10.1016/0002-9416(53)90082-7",
    "Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29",
)


@dataclass(frozen=True)
class _SteinerSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]
    runtime_metric_name: Optional[str]


_STEINER_SPECS = (
    _SteinerSpec(
        metric_name="SNA",
        construction_definition_id="STEINER_SNA_V1",
        method_id="STEINER_SNA_DEG_V1",
        required_landmark_ids=("S", "N", "A"),
        runtime_metric_name="SNA",
    ),
    _SteinerSpec(
        metric_name="SNB",
        construction_definition_id="STEINER_SNB_V1",
        method_id="STEINER_SNB_DEG_V1",
        required_landmark_ids=("S", "N", "B"),
        runtime_metric_name="SNB",
    ),
    _SteinerSpec(
        metric_name="ANB",
        construction_definition_id="STEINER_ANB_V1",
        method_id="STEINER_ANB_DEG_V1",
        required_landmark_ids=("S", "N", "A", "B"),
        runtime_metric_name="ANB",
    ),
    _SteinerSpec(
        metric_name="SN_MP",
        construction_definition_id="STEINER_SN_MP_V1",
        method_id="STEINER_SN_MP_DEG_V1",
        required_landmark_ids=("S", "N", "Go", "Gn"),
        runtime_metric_name=None,
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _computed_value(
    definition_id: str, landmarks: Mapping[str, LandmarkEvidence]
) -> Optional[float]:
    if definition_id == "STEINER_SNA_V1":
        return steiner_sna_deg_v1(_point(landmarks, "S"), _point(landmarks, "N"), _point(landmarks, "A"))
    if definition_id == "STEINER_SNB_V1":
        return steiner_snb_deg_v1(_point(landmarks, "S"), _point(landmarks, "N"), _point(landmarks, "B"))
    if definition_id == "STEINER_ANB_V1":
        return steiner_anb_deg_v1(
            _point(landmarks, "S"),
            _point(landmarks, "N"),
            _point(landmarks, "A"),
            _point(landmarks, "B"),
        )
    if definition_id == "STEINER_SN_MP_V1":
        return steiner_sn_mp_deg_v1(
            _point(landmarks, "S"),
            _point(landmarks, "N"),
            _point(landmarks, "Go"),
            _point(landmarks, "Gn"),
        )
    raise ValueError(f"Unsupported Steiner construction {definition_id}")


def materialize_steiner_skeletal_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _STEINER_SPECS:
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

        availability = AvailabilityStatus.AVAILABLE
        geometry: dict[str, object] = {
            "kind": "cephalometric_angle",
            "analysis": "STEINER",
            "source_references": list(STEINER_SOURCE_REFERENCES),
        }
        if spec.construction_definition_id == "STEINER_SN_MP_V1":
            geometry.update(
                {
                    "axis_orientation_invariant": True,
                    "reference_axis": "S-N",
                    "mandibular_plane": "Go-Gn",
                }
            )
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            geometry["required_landmark_ids"] = list(spec.required_landmark_ids)
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
            geometry["required_landmark_ids"] = list(spec.required_landmark_ids)
        else:
            value = _computed_value(spec.construction_definition_id, landmarks)
            if value is None:
                availability = AvailabilityStatus.INVALID
                geometry["required_landmark_ids"] = list(spec.required_landmark_ids)
            else:
                geometry.update(
                    {
                        "computed_angle_deg": round(value, 1),
                        "source_image_ref": next(iter(sources)),
                        "required_landmark_ids": list(spec.required_landmark_ids),
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

    out.update(
        materialize_tweed_merrifield_constructions(
            landmarks,
            construction_namespace=f"{construction_namespace}:r6",
        )
    )
    return out


def adapt_steiner_skeletal_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    out: list[MeasurementEvidence] = []
    for spec in _STEINER_SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing Steiner construction {spec.construction_definition_id}")
        if construction.definition_id != spec.construction_definition_id:
            raise ValueError(
                f"Construction key {spec.construction_definition_id} resolves to {construction.definition_id}"
            )

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            computed = construction.geometry.get("computed_angle_deg")
            if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                raise ValueError(
                    f"Available Steiner construction {spec.construction_definition_id} lacks finite computed_angle_deg"
                )
            computed_value = float(computed)
            if spec.runtime_metric_name is not None:
                raw_value = getattr(result.metrics.analyse_osseuse, spec.runtime_metric_name).valeur
                if raw_value is None or not math.isfinite(raw_value) or not math.isclose(
                    raw_value, computed_value, rel_tol=0.0, abs_tol=1e-12
                ):
                    raise ValueError(
                        f"Runtime {spec.runtime_metric_name} does not match typed Steiner geometry"
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
                analysis_id="STEINER",
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

    out.extend(
        adapt_tweed_merrifield_measurements(
            result,
            measurement_namespace=f"{measurement_namespace}:r6",
            constructions=constructions,
        )
    )
    return out


STEINER_SKELETAL_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _STEINER_SPECS
)
