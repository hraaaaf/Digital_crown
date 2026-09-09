"""Safe runtime boundary for the legacy cephalometric engine.

The legacy ``CephaloEngine`` still contains historical local norms, growth
projections and treatment narrative code. Runtime application code must import
``cephalo_safe_engine`` instead.

This adapter is deliberately fail-closed. It preserves measured geometry while
preventing unvalidated normative interpretation, autonomous growth prediction
and treatment selection from escaping the quarantined engine.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.services.cephalo_engine import cephalo_engine as _legacy_cephalo_engine


def _neutralize_measurement(value: Any, measurement: Dict[str, Any]) -> None:
    """Keep the measured value, remove legacy normative authority in-place."""
    measurement["norm_mean"] = 0.0
    measurement["norm_min"] = 0.0
    measurement["norm_max"] = 0.0
    measurement["plage_compensation"] = None
    measurement["z_score"] = 0.0
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
    """Runtime adapter exposing geometry only from the quarantined legacy engine."""

    def calculate_metrics(self, *args: Any, **kwargs: Any):
        result = _legacy_cephalo_engine.calculate_metrics(*args, **kwargs)

        # Copy before sanitizing so the quarantined engine remains inspectable in
        # isolated tests/debugging while runtime gets a separately validated model.
        payload: Dict[str, Any] = result.model_dump()

        # 1. Never expose an autonomous treatment strategy.
        narrative = payload.get("ai_narrative")
        if isinstance(narrative, dict):
            narrative.pop("strategie_therapeutique", None)

        # 2. Never expose local hard-coded normative status/interpretation as truth.
        _neutralize_legacy_norms(payload)

        # 3. Legacy age-based T1/T2 morphing is not a validated patient-specific
        # growth model. Preserve no automatic future anatomical projection.
        payload["t1_projection"] = {}
        payload["t2_projection"] = {}

        return type(result).model_validate(payload)


cephalo_safe_engine = SafeCephaloEngine()
