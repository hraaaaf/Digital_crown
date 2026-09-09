"""Safe runtime boundary for the legacy cephalometric engine.

The legacy CephaloEngine still contains historical normative and treatment
narrative code. Runtime application code must import ``cephalo_safe_engine``
instead. This adapter preserves geometry/measurements while removing autonomous
treatment content before any service can persist or expose the result.

This is a quarantine boundary, not scientific validation of the legacy engine.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.services.cephalo_engine import cephalo_engine as _legacy_cephalo_engine


class SafeCephaloEngine:
    """Compatibility adapter that prevents legacy treatment output escaping."""

    def calculate_metrics(self, *args: Any, **kwargs: Any):
        result = _legacy_cephalo_engine.calculate_metrics(*args, **kwargs)

        # Pydantic models are copied before mutation so the legacy result remains
        # untouched for debugging/tests. Runtime receives a separately validated
        # model with the autonomous treatment field removed.
        payload: Dict[str, Any] = result.model_dump()
        narrative = payload.get("ai_narrative")
        if isinstance(narrative, dict):
            narrative.pop("strategie_therapeutique", None)

        return type(result).model_validate(payload)


cephalo_safe_engine = SafeCephaloEngine()
