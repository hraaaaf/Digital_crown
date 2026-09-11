"""R4 proofs for typed CRANIOM interincisal angle evidence."""

import pytest

from backend.schemas.cephalo_evidence import AvailabilityStatus, EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_construction_evidence_adapter import materialize_craniom_constructions
from backend.services.cephalo_craniom_angular import craniom_interincisal_deg_v1
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_geometric_conventions import get_active_craniom_convention
from backend.services.cephalo_measurement_adapter import adapt_craniom_measurements


def _points():
    return {
        "S": (10.0, 10.0), "N": (20.0, 10.0), "Po": (0.0, 20.0), "Or": (20.0, 20.0),
        "A": (24.0, 28.0), "B": (22.0, 38.0), "Go": (5.0, 50.0), "Me": (25.0, 55.0),
        "U1_apex": (20.0, 25.0), "U1_incisal": (24.0, 35.0),
        "L1_apex": (20.0, 48.0), "L1_incisal": (23.0, 38.0),
    }


def _landmarks(points=None):
    points = points or _points()
    return {
        key: LandmarkEvidence(
            evidence_id=f"lm:{key}", landmark_id=key, x=x, y=y,
            source_image_ref="img:1", origin=LandmarkOrigin.MANUAL,
            evidence_refs=["src:1"], evidence_status=EvidenceStatus.OBSERVED,
        )
        for key, (x, y) in points.items()
    }


def test_interincisal_convention_is_explicit_and_calibration_independent():
    convention = get_active_craniom_convention("CRANIOM_U1_L1_INTERINCISAL_V1")
    assert convention.convention_id == "CRANIOM_INTERINCISAL_ANGLE_V1"
    assert convention.reference_frame_id == "U1_L1_LONG_AXES_V1"
    assert convention.required_landmark_ids == ("U1_apex", "U1_incisal", "L1_apex", "L1_incisal")
    assert "doi:10.1051/odfen/2011104" in convention.source_references


def test_versioned_geometry_matches_existing_runtime_inter_incisif_exactly():
    points = _points()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(points)
    typed = craniom_interincisal_deg_v1(
        points["U1_apex"], points["U1_incisal"], points["L1_apex"], points["L1_incisal"]
    )
    assert typed is not None
    assert round(typed, 1) == result.metrics.analyse_dentaire.Inter_Incisif.valeur

    constructions = materialize_craniom_constructions(_landmarks(), construction_namespace="c")
    measurements = adapt_craniom_measurements(
        result, measurement_namespace="m", constructions=constructions, calibration_ref=None
    )
    measurement = next(x for x in measurements if x.method_id == "CRANIOM_INTERINCISAL_DEG_V1")
    assert measurement.value == result.metrics.analyse_dentaire.Inter_Incisif.valeur
    assert measurement.unit == "deg"
    assert measurement.requires_calibration is False
    assert measurement.calibration_ref is None
    assert measurement.availability_status == AvailabilityStatus.AVAILABLE


def test_interincisal_runtime_parity_guard_fails_closed():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())
    result.metrics.analyse_dentaire.Inter_Incisif.valeur = 99.9
    constructions = materialize_craniom_constructions(_landmarks(), construction_namespace="c")
    with pytest.raises(ValueError, match="Runtime Inter_Incisif does not match"):
        adapt_craniom_measurements(
            result, measurement_namespace="m", constructions=constructions, calibration_ref=None
        )


def test_missing_or_degenerate_axis_fails_closed():
    missing = _landmarks()
    missing.pop("L1_apex")
    construction = materialize_craniom_constructions(missing, construction_namespace="c1")["CRANIOM_U1_L1_INTERINCISAL_V1"]
    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert construction.missing_landmark_ids == ["L1_apex"]

    degenerate_points = _points()
    degenerate_points["L1_incisal"] = degenerate_points["L1_apex"]
    construction = materialize_craniom_constructions(_landmarks(degenerate_points), construction_namespace="c2")["CRANIOM_U1_L1_INTERINCISAL_V1"]
    assert construction.availability_status == AvailabilityStatus.INVALID
