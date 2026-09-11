#!/usr/bin/env python3
"""Fail-closed validator for the Digital Crown competitive evidence harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPETITIVE_DIR = ROOT / "docs" / "competitive"

CAPABILITIES_PATH = COMPETITIVE_DIR / "capabilities.json"
SOURCES_PATH = COMPETITIVE_DIR / "orthalis_sources.json"
SCENARIOS_PATH = COMPETITIVE_DIR / "scenarios.json"
DATASET_PATH = COMPETITIVE_DIR / "synthetic_dataset.json"

ALLOWED_CAPABILITY_STATUSES = {
    "VERIFIED_REPO",
    "PARTIAL_VERIFIED",
    "VENDOR_CLAIM_VERIFIED",
    "NOT_PROVEN",
    "BLOCKED_RUNTIME",
}
ALLOWED_MEASUREMENT_STATUSES = {"NOT_MEASURED", "MEASURED", "BLOCKED_RUNTIME"}
METRIC_FIELDS = ("elapsed_ms", "primary_actions", "errors", "retries")


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing required manifest: {path.relative_to(ROOT)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"top-level JSON must be an object: {path.relative_to(ROOT)}")
    return data


def require_unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
    ids: set[str] = set()
    for index, item in enumerate(items):
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValidationError(f"{label}[{index}] has no non-empty id")
        if item_id in ids:
            raise ValidationError(f"duplicate {label} id: {item_id}")
        ids.add(item_id)
    return ids


def validate_sources(data: dict[str, Any]) -> set[str]:
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValidationError("orthalis_sources.json must contain a non-empty sources list")
    source_ids = require_unique_ids(sources, "source")
    for source in sources:
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://www.orthalis.com/"):
            raise ValidationError(f"source {source['id']} is not an official orthalis.com HTTPS URL")
        claims = source.get("claims")
        if not isinstance(claims, list) or not claims or not all(isinstance(c, str) and c.strip() for c in claims):
            raise ValidationError(f"source {source['id']} must contain non-empty textual claims")
    checked_on = data.get("checked_on")
    if not isinstance(checked_on, str) or len(checked_on) != 10:
        raise ValidationError("orthalis_sources.json must contain checked_on YYYY-MM-DD")
    return source_ids


def validate_evidence_list(
    capability_id: str,
    side: str,
    status: str,
    evidence: Any,
    source_ids: set[str],
) -> None:
    if not isinstance(evidence, list) or not evidence:
        raise ValidationError(f"{capability_id}.{side} must have at least one evidence item")

    repo_evidence = 0
    official_evidence = 0
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValidationError(f"{capability_id}.{side}.evidence[{index}] must be an object")
        evidence_type = item.get("type")
        if evidence_type == "repo_path":
            path = item.get("path")
            if not isinstance(path, str) or not path.strip():
                raise ValidationError(f"{capability_id}.{side} has empty repo_path")
            repo_evidence += 1
        elif evidence_type == "source_id":
            source_id = item.get("source_id")
            if source_id not in source_ids:
                raise ValidationError(f"{capability_id}.{side} references unknown source_id {source_id!r}")
            official_evidence += 1
        else:
            raise ValidationError(f"{capability_id}.{side} has unsupported evidence type {evidence_type!r}")

    if status == "VERIFIED_REPO" and repo_evidence == 0:
        raise ValidationError(f"{capability_id}.{side} VERIFIED_REPO requires repo_path evidence")
    if status == "VENDOR_CLAIM_VERIFIED" and official_evidence == 0:
        raise ValidationError(f"{capability_id}.{side} VENDOR_CLAIM_VERIFIED requires source_id evidence")


def validate_capabilities(data: dict[str, Any], source_ids: set[str]) -> set[str]:
    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        raise ValidationError("capabilities.json must contain baseline")
    ref = baseline.get("digital_crown_ref")
    if not isinstance(ref, str) or len(ref) != 40:
        raise ValidationError("digital_crown_ref must be an exact 40-character commit SHA")

    vocabulary = data.get("status_vocabulary")
    if set(vocabulary or []) != ALLOWED_CAPABILITY_STATUSES:
        raise ValidationError("status_vocabulary does not exactly match the validator vocabulary")

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValidationError("capabilities.json must contain non-empty capabilities")
    capability_ids = require_unique_ids(capabilities, "capability")

    for capability in capabilities:
        capability_id = capability["id"]
        statement = capability.get("benchmark_statement")
        if not isinstance(statement, str) or not statement.strip():
            raise ValidationError(f"{capability_id} has no benchmark_statement")
        for side in ("digital_crown", "orthalis"):
            payload = capability.get(side)
            if not isinstance(payload, dict):
                raise ValidationError(f"{capability_id}.{side} must be an object")
            status = payload.get("status")
            if status not in ALLOWED_CAPABILITY_STATUSES:
                raise ValidationError(f"{capability_id}.{side} has invalid status {status!r}")
            validate_evidence_list(capability_id, side, status, payload.get("evidence"), source_ids)
    return capability_ids


def validate_dataset(data: dict[str, Any]) -> set[str]:
    if data.get("synthetic_only") is not True:
        raise ValidationError("synthetic_dataset.json must set synthetic_only=true")
    safety = data.get("safety_contract")
    if not isinstance(safety, dict) or safety.get("contains_real_patient_data") is not False:
        raise ValidationError("synthetic dataset must explicitly declare contains_real_patient_data=false")
    if safety.get("forbidden_target") != "cabinet database":
        raise ValidationError("synthetic dataset must explicitly forbid cabinet database target")

    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValidationError("synthetic_dataset.json must contain non-empty fixtures")
    fixture_ids = require_unique_ids(fixtures, "fixture")
    for fixture in fixtures:
        fixture_id = fixture["id"]
        if not fixture_id.startswith("SYN-"):
            raise ValidationError(f"synthetic fixture id must start with SYN-: {fixture_id}")
        payload = fixture.get("data")
        if not isinstance(payload, dict):
            raise ValidationError(f"fixture {fixture_id} has no data object")
        for pii_field in ("phone", "email"):
            if payload.get(pii_field) not in (None, ""):
                raise ValidationError(f"fixture {fixture_id} contains non-empty {pii_field}")
    return fixture_ids


def validate_measurement(scenario_id: str, side: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValidationError(f"{scenario_id}.{side} measurement must be an object")
    status = payload.get("measurement_status")
    if status not in ALLOWED_MEASUREMENT_STATUSES:
        raise ValidationError(f"{scenario_id}.{side} has invalid measurement_status {status!r}")

    if status == "MEASURED":
        if not isinstance(payload.get("success"), bool):
            raise ValidationError(f"{scenario_id}.{side} MEASURED requires boolean success")
        if not isinstance(payload.get("evidence_ref"), str) or not payload["evidence_ref"].strip():
            raise ValidationError(f"{scenario_id}.{side} MEASURED requires evidence_ref")
        for field in METRIC_FIELDS:
            value = payload.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValidationError(f"{scenario_id}.{side}.{field} must be a non-negative integer when measured")
    else:
        fields_that_must_be_null = ("success", *METRIC_FIELDS, "evidence_ref")
        for field in fields_that_must_be_null:
            if payload.get(field) is not None:
                raise ValidationError(
                    f"{scenario_id}.{side}.{field} must be null when measurement_status={status}"
                )


def validate_scenarios(
    data: dict[str, Any], capability_ids: set[str], fixture_ids: set[str]
) -> set[str]:
    policy = data.get("measurement_policy")
    if not isinstance(policy, dict) or set(policy.get("allowed_statuses") or []) != ALLOWED_MEASUREMENT_STATUSES:
        raise ValidationError("scenarios measurement policy does not match validator vocabulary")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValidationError("scenarios.json must contain non-empty scenarios")
    scenario_ids = require_unique_ids(scenarios, "scenario")

    for scenario in scenarios:
        scenario_id = scenario["id"]
        linked_capabilities = scenario.get("capability_ids")
        if not isinstance(linked_capabilities, list) or not linked_capabilities:
            raise ValidationError(f"{scenario_id} must reference at least one capability")
        unknown_caps = set(linked_capabilities) - capability_ids
        if unknown_caps:
            raise ValidationError(f"{scenario_id} references unknown capabilities: {sorted(unknown_caps)}")

        fixture_refs = scenario.get("synthetic_fixture_ids")
        if not isinstance(fixture_refs, list) or not fixture_refs:
            raise ValidationError(f"{scenario_id} must reference at least one synthetic fixture")
        unknown_fixtures = set(fixture_refs) - fixture_ids
        if unknown_fixtures:
            raise ValidationError(f"{scenario_id} references unknown fixtures: {sorted(unknown_fixtures)}")

        validate_measurement(scenario_id, "digital_crown", scenario.get("digital_crown"))
        validate_measurement(scenario_id, "orthalis", scenario.get("orthalis"))
    return scenario_ids


def validate() -> dict[str, int]:
    sources = load_json(SOURCES_PATH)
    capabilities = load_json(CAPABILITIES_PATH)
    dataset = load_json(DATASET_PATH)
    scenarios = load_json(SCENARIOS_PATH)

    source_ids = validate_sources(sources)
    capability_ids = validate_capabilities(capabilities, source_ids)
    fixture_ids = validate_dataset(dataset)
    scenario_ids = validate_scenarios(scenarios, capability_ids, fixture_ids)

    return {
        "sources": len(source_ids),
        "capabilities": len(capability_ids),
        "fixtures": len(fixture_ids),
        "scenarios": len(scenario_ids),
    }


def main() -> int:
    try:
        counts = validate()
    except ValidationError as exc:
        print(f"COMPETITIVE_EVIDENCE_HARNESS=FAIL: {exc}")
        return 1
    print(
        "COMPETITIVE_EVIDENCE_HARNESS=PASS "
        + " ".join(f"{key}={value}" for key, value in counts.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
