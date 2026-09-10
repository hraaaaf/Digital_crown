"""Defense-in-depth runtime boundary for the cephalometric geometry engine.

``CephaloEngine`` is now geometry-only after the Scientific Core purge, but
runtime application code still enters through this adapter. Keeping the boundary
preserves the architectural guard and prevents future normative, growth or
treatment fields from escaping accidentally if the core evolves.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.services.cephalo_engine import cephalo_engine as _legacy_cephalo_engine


def _neutralize_measurement(value: Any, measurement: Dict[str, Any]) -> None:
    """Keep the measured value and strip any normative authority in-place."""
    measurement["norm_mean"] = None
    measurement["norm_min"] = None
    measurement["norm_max"] = None
    measurement["plage_compensation"] = None
    measurement["z_score"] = None
    if value is None:
        measurement["status"] = "Missing"
        measurement["interpretation"] = "Mesure non disponible."
    else:
        measurement["status"] = "N/A"
        measurement["interpretation"] = (
            "Mesure brute conservée; aucune interprétation normative locale autoritative."
        )


def _neutralize_legacy_norms(payload: Dict[str, Any]) -> None:
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        return
    for group in metrics.values():
        if not isinstance(group, dict):
            continue
        for measurement in group.values():
            if isinstance(measurement, dict) and "valeur" in measurement:
                _neutralize_measurement(measurement.get("valeur"), measurement)


class SafeCephaloEngine:
    """Runtime adapter exposing geometry only with defense-in-depth sanitization."""

    def calculate_metrics(self, *args: Any, **kwargs: Any):
        result = _legacy_cephalo_engine.calculate_metrics(*args, **kwargs)

        # Copy before sanitizing so the underlying deterministic engine remains
        # inspectable in isolated migration/regression tests.
        payload: Dict[str, Any] = result.model_dump()

        # 1. Never expose an autonomous treatment strategy.
        narrative = payload.get("ai_narrative")
        if isinstance(narrative, dict):
            narrative.pop("strategie_therapeutique", None)

        # 2. Never expose local hard-coded normative status/interpretation as truth.
        _neutralize_legacy_norms(payload)

        # 3. No automatic future anatomical projection is authoritative here.
        payload["t1_projection"] = {}
        payload["t2_projection"] = {}

        return type(result).model_validate(payload)


cephalo_safe_engine = SafeCephaloEngine()
