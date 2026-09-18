"""
Canonical cephalometric measurement identity registry.

This module extends the historical unit helpers without replacing their
legacy name-based behaviour. Canonical ``M_*`` identifiers are explicit and
fail closed when their unit is not source-locked.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CanonicalMeasurement:
    measurement_id: str
    unit: Optional[str]
    source_status: str


def _m(measurement_id: str, unit: Optional[str], source_status: str) -> CanonicalMeasurement:
    return CanonicalMeasurement(
        measurement_id=measurement_id,
        unit=unit,
        source_status=source_status,
    )


CANONICAL_MEASUREMENTS: dict[str, CanonicalMeasurement] = {
    # Skeletal sagittal / AP.
    "M_SNA_DEG_V1": _m("M_SNA_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_SNB_DEG_V1": _m("M_SNB_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_ANB_DEG_V1": _m("M_ANB_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_SND_DEG_V1": _m("M_SND_DEG_V1", "°", "BLOCKED_LANDMARK"),
    "M_A_NPERP_MM_V1": _m("M_A_NPERP_MM_V1", "mm", "PRIMITIVE_AVAILABLE"),
    "M_B_NPERP_MM_V1": _m("M_B_NPERP_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_POG_NPERP_MM_V1": _m("M_POG_NPERP_MM_V1", "mm", "PRIMITIVE_AVAILABLE"),
    "M_POG_NB_MM_V1": _m("M_POG_NB_MM_V1", "mm", "IMPLEMENTATION_MISSING"),
    "M_AB_PRIME_FH_MM_V1": _m("M_AB_PRIME_FH_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1": _m(
        "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1", "mm", "GEOMETRY_COVERED"
    ),
    "M_FACIAL_ANGLE_NPOG_FH_DEG_V1": _m(
        "M_FACIAL_ANGLE_NPOG_FH_DEG_V1", "°", "GEOMETRY_COVERED"
    ),
    "M_COM_S_NPERP_DEPTH_MM_V1": _m(
        "M_COM_S_NPERP_DEPTH_MM_V1", "mm", "GEOMETRY_COVERED"
    ),
    # Skeletal vertical / pattern.
    "M_SN_GOGN_DEG_V1": _m("M_SN_GOGN_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_FH_GOME_DEG_V1": _m("M_FH_GOME_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_FH_SUBGO_M_DEG_V1": _m("M_FH_SUBGO_M_DEG_V1", "°", "IMPLEMENTATION_MISSING"),
    "M_ANS_ME_MM_V1": _m("M_ANS_ME_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_PALATAL_PLANE_FH_DEG_V1": _m(
        "M_PALATAL_PLANE_FH_DEG_V1", "°", "PRIMITIVE_AVAILABLE"
    ),
    "M_OCCLUSAL_PLANE_SN_DEG_V1": _m(
        "M_OCCLUSAL_PLANE_SN_DEG_V1", "°", "SOURCE_LOCK_REQUIRED"
    ),
    "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1": _m(
        "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1", "°", "BLOCKED_LANDMARK"
    ),
    "M_BEND_OF_MANDIBLE_DEG_V1": _m(
        "M_BEND_OF_MANDIBLE_DEG_V1", "°", "IMPLEMENTATION_MISSING"
    ),
    # Facial axes / growth.
    "M_FACIAL_AXIS_RICKETTS_DEG_V1": _m(
        "M_FACIAL_AXIS_RICKETTS_DEG_V1", "°", "GEOMETRY_COVERED+BLOCKED_LANDMARK"
    ),
    "M_FACIAL_AXIS_MCNAMARA_DEG_V1": _m(
        "M_FACIAL_AXIS_MCNAMARA_DEG_V1", "°", "IMPLEMENTATION_MISSING"
    ),
    # Maxillo-mandibular lengths.
    "M_CO_A_MM_V1": _m("M_CO_A_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_CO_GN_ANATOMIC_MM_V1": _m("M_CO_GN_ANATOMIC_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_CO_GN_MINUS_CO_A_MM_V1": _m(
        "M_CO_GN_MINUS_CO_A_MM_V1", "mm", "PRIMITIVE_AVAILABLE"
    ),
    # Maxillary dento-alveolar.
    "M_U1_NA_DEG_V1": _m("M_U1_NA_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_U1_NA_MM_V1": _m("M_U1_NA_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_U1_FH_DEG_V1": _m("M_U1_FH_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_U1_A_VERTICAL_MM_V1": _m("M_U1_A_VERTICAL_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_U6_NA_MM_V1": _m("M_U6_NA_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_U6_PTV_MM_V1": _m("M_U6_PTV_MM_V1", "mm", "BLOCKED_LANDMARK"),
    # Mandibular dento-alveolar.
    "M_L1_NB_DEG_V1": _m("M_L1_NB_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_L1_NB_MM_V1": _m("M_L1_NB_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_L1_GOGN_DEG_V1": _m("M_L1_GOGN_DEG_V1", "°", "IMPLEMENTATION_MISSING"),
    "M_IMPA_GOME_DEG_V1": _m("M_IMPA_GOME_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_FMIA_L1_FH_DEG_V1": _m("M_FMIA_L1_FH_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_L1_FACIAL_SURFACE_APOG_MM_V1": _m(
        "M_L1_FACIAL_SURFACE_APOG_MM_V1", "mm", "BLOCKED_LANDMARK"
    ),
    "M_L1_EDGE_APOG_MM_V1": _m("M_L1_EDGE_APOG_MM_V1", "mm", "PRIMITIVE_AVAILABLE"),
    "M_L1_DLINE_MM_V1": _m("M_L1_DLINE_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_L1_DLINE_DEG_V1": _m("M_L1_DLINE_DEG_V1", "°", "BLOCKED_LANDMARK"),
    "M_L6_NB_MM_V1": _m("M_L6_NB_MM_V1", "mm", "BLOCKED_LANDMARK"),
    # Dental / occlusal relations.
    "M_INTERINCISAL_DEG_V1": _m("M_INTERINCISAL_DEG_V1", "°", "GEOMETRY_COVERED"),
    "M_OVERJET_MM_V1": _m("M_OVERJET_MM_V1", "mm", "LEGACY_TO_AUDIT"),
    "M_OVERBITE_V1": _m("M_OVERBITE_V1", "mm", "LEGACY_TO_AUDIT"),
    # Soft tissue and airway.
    "M_LI_EPLANE_MM_V1": _m("M_LI_EPLANE_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_LS_EPLANE_MM_V1": _m("M_LS_EPLANE_MM_V1", "mm", "GEOMETRY_COVERED"),
    "M_NASOLABIAL_ANGLE_DEG_V1": _m(
        "M_NASOLABIAL_ANGLE_DEG_V1", "°", "SOURCE_LOCK_REQUIRED"
    ),
    "M_UPPER_PHARYNX_MM_V1": _m("M_UPPER_PHARYNX_MM_V1", "mm", "BLOCKED_LANDMARK"),
    "M_LOWER_PHARYNX_MM_V1": _m("M_LOWER_PHARYNX_MM_V1", "mm", "BLOCKED_LANDMARK"),
    # PA / frontal Ricketts.
    "M_PA_NASAL_CAVITY_WIDTH_MM_V1": _m(
        "M_PA_NASAL_CAVITY_WIDTH_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_MAXILLARY_RELATION_R_MM_V1": _m(
        "M_PA_MAXILLARY_RELATION_R_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_MAXILLARY_RELATION_L_MM_V1": _m(
        "M_PA_MAXILLARY_RELATION_L_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_MANDIBULAR_WIDTH_MM_V1": _m(
        "M_PA_MANDIBULAR_WIDTH_MM_V1", "mm", "BLOCKED_MODALITY_PA+NORM_HOLD"
    ),
    "M_PA_SKELETAL_SYMMETRY_V1": _m(
        "M_PA_SKELETAL_SYMMETRY_V1", None, "BLOCKED_MODALITY_PA+SOURCE_LOCK_REQUIRED"
    ),
    "M_PA_INTERMOLAR_WIDTH_MM_V1": _m(
        "M_PA_INTERMOLAR_WIDTH_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_INTERCANINE_WIDTH_MM_V1": _m(
        "M_PA_INTERCANINE_WIDTH_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_LOWER_MOLAR_FDP_R_MM_V1": _m(
        "M_PA_LOWER_MOLAR_FDP_R_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_LOWER_MOLAR_FDP_L_MM_V1": _m(
        "M_PA_LOWER_MOLAR_FDP_L_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_LOWER_INCISOR_FRONTAL_APO_MM_V1": _m(
        "M_PA_LOWER_INCISOR_FRONTAL_APO_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_MOLAR_CROSSBITE_R_MM_V1": _m(
        "M_PA_MOLAR_CROSSBITE_R_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    "M_PA_MOLAR_CROSSBITE_L_MM_V1": _m(
        "M_PA_MOLAR_CROSSBITE_L_MM_V1", "mm", "BLOCKED_MODALITY_PA"
    ),
    # Serial / growth-change measurements.
    "M_SERIAL_INCISOR_DISPLACEMENT_V1": _m(
        "M_SERIAL_INCISOR_DISPLACEMENT_V1", None, "IMPLEMENTATION_MISSING"
    ),
    "M_SERIAL_MOLAR_DISPLACEMENT_V1": _m(
        "M_SERIAL_MOLAR_DISPLACEMENT_V1", None, "IMPLEMENTATION_MISSING"
    ),
    "M_SERIAL_CO_A_CHANGE_MM_V1": _m(
        "M_SERIAL_CO_A_CHANGE_MM_V1", "mm", "IMPLEMENTATION_MISSING"
    ),
    "M_SERIAL_CO_GN_CHANGE_MM_V1": _m(
        "M_SERIAL_CO_GN_CHANGE_MM_V1", "mm", "IMPLEMENTATION_MISSING"
    ),
    "M_SERIAL_MAXMAND_DIFF_CHANGE_MM_V1": _m(
        "M_SERIAL_MAXMAND_DIFF_CHANGE_MM_V1", "mm", "IMPLEMENTATION_MISSING"
    ),
    "M_SERIAL_ANS_ME_CHANGE_MM_V1": _m(
        "M_SERIAL_ANS_ME_CHANGE_MM_V1", "mm", "IMPLEMENTATION_MISSING"
    ),
}


def canonical_measurement(measurement_id: str) -> Optional[CanonicalMeasurement]:
    """Return canonical metadata for an exact ID, without alias resolution."""
    return CANONICAL_MEASUREMENTS.get(measurement_id)


def canonical_unit(measurement_id: str) -> Optional[str]:
    """Return a source-locked canonical unit, or None if unknown/unlocked."""
    measurement = canonical_measurement(measurement_id)
    return None if measurement is None else measurement.unit


# Historical name classifier kept for persisted/runtime compatibility.
MM_KEYWORDS: tuple[str, ...] = (
    "Ligne", "Surplomb", "Recouvrement", "Decalage", "Décalage",
    "Situation", "Profondeur", "I_NA_mm", "I_NB_mm", "Wits",
    "Longueur", "Differentiel", "Etage",
)

_MM_KEYWORDS_LOWER: tuple[str, ...] = tuple(k.lower() for k in MM_KEYWORDS)


def _legacy_is_mm_metric(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in _MM_KEYWORDS_LOWER)


def is_mm_metric(name: str) -> bool:
    """Return True for canonical millimetric IDs or legacy mm metric names."""
    measurement = canonical_measurement(name)
    if measurement is not None and measurement.unit is not None:
        return measurement.unit == "mm"
    return _legacy_is_mm_metric(name)


def cephalo_unit(metric_name: str) -> str:
    """Return ``mm`` or ``°`` while preserving legacy name compatibility.

    Canonical IDs with an unresolved unit fail closed instead of being guessed.
    """
    measurement = canonical_measurement(metric_name)
    if measurement is not None:
        if measurement.unit is None:
            raise ValueError(
                f"Canonical measurement {metric_name} has no source-locked unit"
            )
        return measurement.unit
    return "mm" if _legacy_is_mm_metric(metric_name) else "°"
