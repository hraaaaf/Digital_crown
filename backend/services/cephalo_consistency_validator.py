"""Fail-closed structural validator for cephalometric analysis.

This validator may reject structural/data contradictions. It must not act as a
parallel clinical normative authority. Population/method-dependent clinical
classification belongs to the normative registry and practitioner workflow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.services.cephalo_measure_registry import is_mm_metric as _is_mm_name


def _val(obj: Any, *keys: str) -> Optional[float]:
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    if cur is None:
        return None
    if isinstance(cur, dict):
        cur = cur.get("valeur")
    try:
        return float(cur)
    except (TypeError, ValueError):
        return None


@dataclass
class ValidationResult:
    fatals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.fatals

    def to_dict(self) -> dict:
        return {"valid": self.is_valid, "fatals": self.fatals, "warnings": self.warnings}


class CephaloConsistencyValidator:
    """Validate structure, arithmetic consistency, units and calibration only."""

    @staticmethod
    def _iter_metrics(metrics: dict):
        for section in metrics.values():
            if not isinstance(section, dict):
                continue
            for name, data in section.items():
                if not isinstance(data, dict):
                    continue
                raw = data.get("valeur")
                unit = data.get("unite") or ""
                try:
                    yield name, float(raw), unit
                except (TypeError, ValueError):
                    continue

    def _check_unit_contradictions(self, metrics: dict, result: ValidationResult) -> None:
        for name, val, unit in self._iter_metrics(metrics):
            if _is_mm_name(name) and unit == "°":
                result.fatals.append(
                    f"Unité contradictoire : '{name}' = {val:.1f} est étiqueté '°' mais devrait être en mm."
                )

    def validate(self, angles_data: dict) -> ValidationResult:
        result = ValidationResult()
        if not isinstance(angles_data, dict):
            result.fatals.append("angles_data manquant ou format invalide.")
            return result

        metrics = angles_data.get("metrics", angles_data)
        if not isinstance(metrics, dict):
            result.fatals.append("metrics manquant ou format invalide.")
            return result

        osseuse = metrics.get("analyse_osseuse", {})
        sna = _val(osseuse, "SNA", "valeur")
        snb = _val(osseuse, "SNB", "valeur")
        anb = _val(osseuse, "ANB", "valeur")

        # Structural identity: when all three are present, ANB must agree with
        # the same SNA/SNB geometry. This is arithmetic consistency, not a norm.
        if sna is not None and snb is not None and anb is not None:
            expected_anb = round(sna - snb, 1)
            if abs(expected_anb - anb) > 1.5:
                result.fatals.append(
                    f"Incohérence interne : SNA({sna:.1f}°) - SNB({snb:.1f}°) = {expected_anb}° mais ANB = {anb:.1f}°."
                )

        self._check_unit_contradictions(metrics, result)

        # No local 'normal', Class II/III, overjet/deep-bite or population-based
        # thresholds are applied here. The normative registry is the sole future
        # authority for such interpretation.

        if angles_data.get("calibration_status") == "unverified":
            result.warnings.append(
                "Calibration non vérifiée : les mesures linéaires en millimètres ne doivent pas être interprétées avant calibration."
            )

        return result


cephalo_consistency_validator = CephaloConsistencyValidator()
