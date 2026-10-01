"""LOT04 benchmark/acceptance semantic validator.

Documentation/certification harness only. No product runtime import.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class Lot04ContractError(ValueError):
    pass


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_manifest_semantics(payload: Mapping[str, Any]) -> None:
    cases = payload["dataset"]["cases"]
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise Lot04ContractError("duplicate case_id")
    known = set(case_ids)
    development = set(payload["dataset"]["development_case_ids"])
    acceptance = set(payload["dataset"]["acceptance_case_ids"])
    if not development <= known or not acceptance <= known:
        raise Lot04ContractError("split references unknown case_id")
    if development & acceptance:
        raise Lot04ContractError("development and acceptance splits must be disjoint")


def validate_acceptance_semantics(record: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    validate_manifest_semantics(manifest)
    expected_manifest = canonical_json_sha256(manifest)
    if record["manifest_sha256"] != expected_manifest:
        raise Lot04ContractError("acceptance record manifest_sha256 mismatch")
    if record["candidate_model_sha256"] != manifest["candidate"]["model_sha256"]:
        raise Lot04ContractError("acceptance record candidate_model_sha256 mismatch")

    landmarks = record["landmarks"]
    if len({item["landmark_id"] for item in landmarks}) != len(landmarks):
        raise Lot04ContractError("duplicate landmark decision")

    clinical = record["clinical_measurements"]
    if len({item["measurement_id"] for item in clinical}) != len(clinical):
        raise Lot04ContractError("duplicate clinical measurement decision")

    overall = record["overall_decision"]
    landmark_decisions = [item["decision"] for item in landmarks]
    clinical_decisions = [item["decision"] for item in clinical]

    policy = manifest["acceptance_policy"]
    landmark_tolerances = {item["landmark_id"]: item for item in policy["landmark_tolerances"]}
    clinical_tolerances = {item["measurement_id"]: item for item in policy["clinical_tolerances"]}

    if len(landmark_tolerances) != len(policy["landmark_tolerances"]):
        raise Lot04ContractError("duplicate landmark tolerance")
    if len(clinical_tolerances) != len(policy["clinical_tolerances"]):
        raise Lot04ContractError("duplicate clinical tolerance")

    if overall == "PASS":
        if not manifest["dataset"]["acceptance_case_ids"]:
            raise Lot04ContractError("overall PASS requires a non-empty untouched acceptance split")
        if any(decision != "PASS" for decision in landmark_decisions):
            raise Lot04ContractError("overall PASS requires every reported landmark to PASS")
        if any(item["n"] <= 0 for item in landmarks):
            raise Lot04ContractError("overall PASS requires observed landmark evidence")
        if any(item["human_reference_uncertainty_mm"] is None for item in landmarks):
            raise Lot04ContractError("overall PASS requires human-reference uncertainty")
        if any(decision != "PASS" for decision in clinical_decisions):
            raise Lot04ContractError("overall PASS cannot hide a non-passing clinical measurement")
        for item in landmarks:
            tolerance = landmark_tolerances.get(item["landmark_id"])
            if tolerance is None:
                raise Lot04ContractError("overall PASS requires preregistered tolerance for every landmark")
            if item.get("tolerance_version") != policy["tolerance_version"]:
                raise Lot04ContractError("landmark tolerance_version mismatch")
            if item.get("median_mm") is None or item.get("p95_mm") is None:
                raise Lot04ContractError("overall PASS requires quantitative landmark metrics")
            if item["median_mm"] > tolerance["max_median_mm"] or item["p95_mm"] > tolerance["max_p95_mm"] or item["failure_rate"] > tolerance["max_failure_rate"]:
                raise Lot04ContractError("landmark PASS exceeds preregistered tolerance")
        for item in clinical:
            tolerance = clinical_tolerances.get(item["measurement_id"])
            if tolerance is None:
                raise Lot04ContractError("overall PASS requires preregistered tolerance for every clinical measurement")
            if item.get("absolute_error") is None or item["absolute_error"] > tolerance["max_absolute_error"]:
                raise Lot04ContractError("clinical PASS exceeds preregistered tolerance")

    if overall == "FAIL":
        if "FAIL" not in landmark_decisions and "FAIL" not in clinical_decisions:
            raise Lot04ContractError("overall FAIL requires an explicit failing component")

    if overall == "INSUFFICIENT_EVIDENCE":
        insufficient = {"INSUFFICIENT_EVIDENCE", "NOT_COMPUTABLE"}
        if not any(d in insufficient for d in landmark_decisions + clinical_decisions):
            raise Lot04ContractError("INSUFFICIENT_EVIDENCE requires an explicit insufficient component")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
