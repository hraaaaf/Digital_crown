"""
Loader for the cephalometric normative registry.

Reads the YAML data files under backend/data/cephalometry/ and validates
every entry against backend/schemas/cephalo_normative.py, failing loudly on
any duplicate ID (mission CEPHALOMETRY-NORMATIVE-SERVICE-CORE-3 §32: a
scientific registry must never tolerate ambiguous configuration). Nothing
here performs profile selection, age/sex/population matching, or
classification — that is backend/services/cephalo_normative_service.py's
job. This module is not imported by any existing clinical consumer; it
changes no runtime clinical behavior.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, List

import yaml
from pydantic import ValidationError

from backend.schemas.cephalo_normative import (
    ClassificationRule,
    MeasurementDefinition,
    NormativeProfile,
    PlausibilityBounds,
)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cephalometry"


def _load_yaml_list(filename: str, list_key: str) -> List[dict]:
    path = _DATA_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        raw: Any = yaml.safe_load(f) or {}
    entries = raw.get(list_key)
    if entries is None:
        raise ValueError(f"{path}: missing top-level key '{list_key}'")
    if not isinstance(entries, list):
        raise ValueError(f"{path}: '{list_key}' must be a list")
    return entries


def _validate_entries(entries: List[dict], model, filename: str) -> List:
    validated = []
    for i, entry in enumerate(entries):
        try:
            validated.append(model(**entry))
        except ValidationError as exc:
            entry_id = (
                entry.get("profile_id")
                or entry.get("rule_id")
                or entry.get("bounds_id")
                or entry.get("measurement_id")
                or f"index {i}"
            )
            raise ValueError(f"{filename}: invalid entry '{entry_id}': {exc}") from exc
    return validated


def _reject_duplicate_ids(items: List, id_attr: str, filename: str) -> None:
    seen = set()
    for item in items:
        item_id = getattr(item, id_attr)
        if item_id in seen:
            raise ValueError(f"{filename}: duplicate {id_attr} '{item_id}' — a scientific registry must not contain ambiguous IDs")
        seen.add(item_id)


def load_measurement_definitions() -> List[MeasurementDefinition]:
    entries = _load_yaml_list("measurement_definitions.yaml", "measurements")
    definitions = _validate_entries(entries, MeasurementDefinition, "measurement_definitions.yaml")
    _reject_duplicate_ids(definitions, "measurement_id", "measurement_definitions.yaml")
    return definitions


def load_normative_profiles() -> List[NormativeProfile]:
    entries = _load_yaml_list("normative_profiles.yaml", "profiles")
    profiles = _validate_entries(entries, NormativeProfile, "normative_profiles.yaml")
    _reject_duplicate_ids(profiles, "profile_id", "normative_profiles.yaml")
    return profiles


def load_classification_rules() -> List[ClassificationRule]:
    entries = _load_yaml_list("classification_rules.yaml", "rules")
    rules = _validate_entries(entries, ClassificationRule, "classification_rules.yaml")
    _reject_duplicate_ids(rules, "rule_id", "classification_rules.yaml")
    return rules


def load_plausibility_bounds() -> List[PlausibilityBounds]:
    entries = _load_yaml_list("plausibility_bounds.yaml", "bounds")
    bounds = _validate_entries(entries, PlausibilityBounds, "plausibility_bounds.yaml")
    _reject_duplicate_ids(bounds, "bounds_id", "plausibility_bounds.yaml")
    return bounds
