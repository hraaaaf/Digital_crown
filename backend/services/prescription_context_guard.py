"""Structural missing-data guard for prescription assistance.

This module contains no therapeutic constants. It only decides whether the
patient context is sufficiently explicit for automated patient-specific
prescription assistance. Missing data stays missing; no synthetic value is
created here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PrescriptionContext:
    age: Optional[int]
    weight_kg: Optional[float]
    antecedents: Optional[str]
    status: str
    missing_fields: tuple[str, ...]

    @property
    def evaluable(self) -> bool:
        return self.status == "evaluable"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "weight": self.weight_kg,
            "antecedents_known": self.antecedents is not None,
        }

    def evaluation_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "missing_fields": list(self.missing_fields),
        }


def calculate_age(birth_date: Any) -> Optional[int]:
    if birth_date is None:
        return None
    today = date.today()
    try:
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
    except AttributeError:
        return None


def _coerce_positive_weight(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        weight = float(value)
    except (TypeError, ValueError):
        return None
    return weight if weight > 0 else None


def build_prescription_context(patient: Any) -> PrescriptionContext:
    age = calculate_age(getattr(patient, "date_naissance", None))

    # The current Patient model has no canonical structured weight field.
    # These lookups are forward-compatible only; they never create a value.
    weight = _coerce_positive_weight(
        getattr(patient, "weight_kg", None)
        if hasattr(patient, "weight_kg")
        else getattr(patient, "poids", None)
    )
    antecedents = getattr(patient, "antecedents_medicaux", None)

    missing: list[str] = []
    if age is None:
        missing.append("age")
    if antecedents is None:
        missing.append("antecedents")
    if age is not None and age < 15 and weight is None:
        missing.append("weight_kg")

    return PrescriptionContext(
        age=age,
        weight_kg=weight,
        antecedents=antecedents,
        status="non_evaluable" if missing else "evaluable",
        missing_fields=tuple(missing),
    )


def non_evaluable_plan(context: PrescriptionContext, act_context: str = "DEFAULT") -> Dict[str, Any]:
    return {
        "source": "Non évaluable",
        "act_context": act_context,
        "drugs": [],
        "patient_context": context.as_dict(),
        "evaluation": context.evaluation_dict(),
        "safety": {
            "risques": [],
            "dosage_note": "Contexte patient incomplet : validation manuelle requise.",
            "is_child": context.age is not None and context.age < 15,
        },
        "moteur": "MissingDataGuard v1",
    }
