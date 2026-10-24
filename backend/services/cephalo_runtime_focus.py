"""R23-G3 view-only focus from exact, current, AVAILABLE typed measurement evidence.

No anatomical identity can be inferred here: Po and Po_anatomic, Co and
Co_anatomic, B and Pog_hard are never substituted. A protocol membership or
historical presentation value is not geometric evidence.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence


def derive_active_runtime_focus(
    canonical_measurements: Sequence[Mapping[str, Any]],
    *,
    landmarks: Mapping[str, Any],
    constructions: Mapping[str, Any],
    measurements: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return only exact-M_* focus links supported by the verified active chain."""
    landmarks_by_evidence = {item.evidence_id: item for item in landmarks.values()}
    # The runtime validator keys construction_map by construction_id; refs in
    # MeasurementEvidence are construction identifiers, never UI path guesses.
    by_construction = {item.construction_id: item for item in constructions.values()}
    out: dict[str, dict[str, Any]] = {}
    for row in canonical_measurements:
        cid = row.get("canonical_measurement_id")
        value = row.get("value")
        refs = row.get("measurement_refs")
        method = row.get("value_authority_method_id")
        if (not isinstance(cid, str) or not cid.startswith("M_")
                or row.get("availability_status") != "AVAILABLE"
                or not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(value) or not isinstance(method, str) or not method
                or not isinstance(refs, list) or not refs):
            continue
        # Refuse incompatible or ambiguous convergence, and require that the
        # canonical authority method/value matches an exact active measurement.
        candidate = [
            measurements.get(ref) for ref in refs
            if isinstance(ref, str) and ref in measurements
            and measurements[ref].method_id == method
        ]
        if len(candidate) != 1:
            continue
        measured = candidate[0]
        status = getattr(measured.availability_status, "value", measured.availability_status)
        if (status != "AVAILABLE"
                or measured.value != value
                or measured.unit != row.get("unit")):
            continue
        lm_refs = list(measured.landmark_refs or [])
        construction_refs = list(measured.construction_refs or [])
        if not lm_refs and not construction_refs:
            continue
        if (len(lm_refs) != len(set(lm_refs))
                or len(construction_refs) != len(set(construction_refs))
                or any(ref not in landmarks_by_evidence for ref in lm_refs)
                or any(ref not in by_construction for ref in construction_refs)):
            continue
        lm_items = [landmarks_by_evidence[ref] for ref in lm_refs]
        constructions_items = [by_construction[ref] for ref in construction_refs]
        if any(getattr(item.availability_status, "value", item.availability_status) != "AVAILABLE"
               for item in [*lm_items, *constructions_items]):
            continue
        if measured.requires_calibration and not measured.calibration_ref:
            continue
        if len({item.landmark_id for item in lm_items}) != len(lm_items):
            continue
        out[cid] = {
            "authority": "ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1",
            "canonical_measurement_id": cid,
            "measurement_ref": measured.measurement_id,
            "value_authority_method_id": method,
            "landmark_ids": [item.landmark_id for item in lm_items],
            "construction_ids": [item.construction_id for item in constructions_items],
            "calibration_required": bool(measured.requires_calibration),
        }
    return out
