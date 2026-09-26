"""Bootstrap applicability metadata for the built-in catalog.

These are editable defaults, not runtime clinical prohibitions. A cabinet can
override them from Settings; unknown/custom acts remain searchable with no
automatic suggestion priority.
"""

from __future__ import annotations

DEFAULT_APPLICABILITY_BY_CODE: dict[str, dict] = {
    # Conservative / prevention
    "HBMD001": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 70},
    "HBMD002": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 70},
    "HBMD003": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 65},
    "HBMD004": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 45},
    "HBMD005": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 10},
    "HBMD006": {"dentitions": ["PRIMARY", "PERMANENT"], "tooth_types": ["MOLAR", "PREMOLAR"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 75},

    # Endodontics
    "HBMD020": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD021": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD022": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD023": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 45},
    "HBMD024": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 70},
    "HBMD025": {"dentitions": ["PRIMARY"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 85},

    # Surgery
    "HBMD040": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD041": {"dentitions": ["PERMANENT"], "tooth_types": ["MOLAR"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 65},
    "HBMD042": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 35},
    "HBMD043": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["TOOTH_RANGE", "QUADRANT"], "suggestion_priority": 10},
    "HBMD044": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},
    "HBMD045": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 20},

    # Prosthodontics
    "HBMD060": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD061": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 55},
    "HBMD062": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 45},
    "HBMD063": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["TOOTH_RANGE"], "min_selected_teeth": 3, "suggestion_priority": 95},
    "HBMD064": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP", "GENERAL"], "treatment_areas": ["TOOTH_RANGE", "ARCH"], "min_selected_teeth": 2, "suggestion_priority": 70},
    "HBMD065": {"dentitions": ["PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["ARCH", "MOUTH"], "suggestion_priority": 25},
    "HBMD066": {"dentitions": ["PERMANENT"], "tooth_types": ["INCISOR", "CANINE", "PREMOLAR"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 35},
    "HBMD067": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 35},

    # Implantology — permanent dentition only, searchable unless context matches.
    "HBMD080": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 0},
    "HBMD081": {"dentitions": ["PERMANENT"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 20},
    "HBMD082": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP", "GENERAL"], "treatment_areas": ["TOOTH_RANGE", "QUADRANT"], "suggestion_priority": 0},
    "HBMD083": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["QUADRANT", "TOOTH_RANGE"], "suggestion_priority": 0},
    "HBMD084": {"dentitions": ["PERMANENT"], "selection_modes": ["GROUP", "GENERAL"], "treatment_areas": ["TOOTH_RANGE", "ARCH"], "suggestion_priority": 0},

    # Periodontology — accessible by search in pediatric contexts, not auto-suggested.
    "HBMD100": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 15},
    "HBMD101": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["QUADRANT", "TOOTH_RANGE"], "suggestion_priority": 0},
    "HBMD102": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["QUADRANT", "TOOTH_RANGE"], "suggestion_priority": 0},
    "HBMD103": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},
    "HBMD104": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GROUP"], "treatment_areas": ["QUADRANT", "TOOTH_RANGE"], "suggestion_priority": 0},

    # Orthodontics
    "HBMD120": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},
    "HBMD121": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["ARCH", "MOUTH"], "suggestion_priority": 0},
    "HBMD122": {"dentitions": ["PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},
    "HBMD123": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},

    # Prevention
    "HBMD140": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 45},
    "HBMD141": {"dentitions": ["PRIMARY", "PERMANENT"], "tooth_types": ["MOLAR", "PREMOLAR"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 80},
    "HBMD142": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},
    "HBMD143": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 0},

    # Pediatric dentistry
    "HBMD180": {"dentitions": ["PRIMARY", "PERMANENT"], "selection_modes": ["GENERAL"], "treatment_areas": ["MOUTH"], "suggestion_priority": 50},
    "HBMD181": {"dentitions": ["PRIMARY", "PERMANENT"], "tooth_types": ["MOLAR", "PREMOLAR"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH", "SURFACE"], "suggestion_priority": 90},
    "HBMD182": {"dentitions": ["PRIMARY"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 85},
    "HBMD183": {"dentitions": ["PRIMARY"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 95},
    "HBMD184": {"dentitions": ["PRIMARY"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 95},
    "HBMD185": {"dentitions": ["PRIMARY"], "selection_modes": ["INDIVIDUAL"], "treatment_areas": ["TOOTH"], "suggestion_priority": 90},
    "HBMD186": {"dentitions": ["PRIMARY"], "selection_modes": ["GROUP"], "treatment_areas": ["TOOTH_RANGE", "ARCH"], "min_selected_teeth": 2, "suggestion_priority": 85},
}


def default_applicability_for_code(code: str | None) -> dict:
    if not code:
        return {}
    return dict(DEFAULT_APPLICABILITY_BY_CODE.get(code, {}))
