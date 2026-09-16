"""Validated loaders for the audited dental subset of Morocco's NGAP 177-06.

Reference-only by design: loading these JSON files never certifies a CatalogAct
mapping and never promotes a row to VERIFIED_PRIMARY. Runtime activation still
requires the existing source-lock and practitioner-validation gates.

The act/coefficient mapping and the legal conditions are intentionally separate:
the latter evolve independently and must not be inferred from a coefficient row.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATASET_ID = "ngap-dental-177-06-v1"
CONDITIONS_DATASET_ID = "ngap-dental-177-06-conditions-v1"
PROVENANCE_DATASET_ID = "ngap-dental-177-06-provenance-v1"
EXPECTED_SOURCE_SHA256 = "e9db137d6a758bd4ad7a506a94a7c0c84726813de3db1e225c761318a75e1fdb"
EXPECTED_LEGAL_REFERENCE = "177-06 du 26 hija 1426 (27 janvier 2006)"
REFERENCE_STATUS = "REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED"
EXPECTED_ENTRY_COUNT = 145
EXPECTED_COLUMNS = ["code", "acte", "coefficient", "anesthesia_coefficient", "entry_type"]
DEFAULT_REFERENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "ngap_dental_177_06.json"
DEFAULT_CONDITIONS_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "ngap_dental_177_06_conditions.json"
)
DEFAULT_PROVENANCE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "ngap_dental_177_06_provenance.json"
)
_CODE_RE = re.compile(r"^D\d{3}$")
_CONDITION_KEY_RE = re.compile(r"^D\d{3}(?:-D\d{3})?$")
_ALLOWED_ENTRY_TYPES = {"act", "anesthesia", "ceiling", "calculation_rule", "quote_required"}


def _expected_codes() -> list[str]:
    return [
        *(f"D{value}" for value in range(600, 642)),
        *(f"D{value}" for value in range(700, 786)),
        *(f"D{value}" for value in range(800, 817)),
    ]


def _validate_provenance(payload: dict[str, Any], *, context: str) -> None:
    if payload.get("status") != REFERENCE_STATUS:
        raise ValueError(f"{context} must remain reference-only")
    reference = payload.get("reference")
    if not isinstance(reference, dict):
        raise ValueError(f"{context} provenance is missing")
    if reference.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"{context} primary source hash mismatch")
    if reference.get("arrete") != EXPECTED_LEGAL_REFERENCE:
        raise ValueError(f"{context} legal reference mismatch")


def validate_ngap_dental_reference(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate mapping structure, coverage and provenance without runtime activation."""

    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported NGAP dental reference schema version")
    if payload.get("dataset_id") != DATASET_ID:
        raise ValueError("Unexpected NGAP dental dataset id")
    _validate_provenance(payload, context="NGAP dental reference")

    if payload.get("columns") != EXPECTED_COLUMNS:
        raise ValueError("NGAP dental row schema mismatch")

    acts = payload.get("acts")
    if not isinstance(acts, list) or len(acts) != EXPECTED_ENTRY_COUNT:
        raise ValueError("NGAP dental entry count mismatch")

    expected_codes = _expected_codes()
    seen_codes: list[str] = []
    for row in acts:
        if not isinstance(row, list) or len(row) != len(EXPECTED_COLUMNS):
            raise ValueError("NGAP dental row must match declared columns")

        code, act, coefficient, anesthesia_coefficient, entry_type = row
        if not isinstance(code, str) or not _CODE_RE.fullmatch(code):
            raise ValueError("Invalid NGAP dental code")
        if code in seen_codes:
            raise ValueError(f"Duplicate NGAP dental code: {code}")
        seen_codes.append(code)

        if not isinstance(act, str) or not act.strip():
            raise ValueError(f"Missing normalized act label for {code}")
        if entry_type not in _ALLOWED_ENTRY_TYPES:
            raise ValueError(f"Unsupported NGAP dental entry type for {code}")

        if entry_type in {"calculation_rule", "quote_required"}:
            if coefficient is not None:
                raise ValueError(f"{code} must not invent a fixed coefficient")
        elif not isinstance(coefficient, (int, float)) or isinstance(coefficient, bool) or coefficient <= 0:
            raise ValueError(f"Invalid NGAP dental coefficient for {code}")

        if anesthesia_coefficient is not None and (
            not isinstance(anesthesia_coefficient, (int, float))
            or isinstance(anesthesia_coefficient, bool)
            or anesthesia_coefficient <= 0
        ):
            raise ValueError(f"Invalid anesthesia coefficient for {code}")

    if seen_codes != expected_codes:
        raise ValueError("NGAP dental coverage/order mismatch")

    scope = payload.get("scope")
    if not isinstance(scope, dict) or scope.get("entry_count") != EXPECTED_ENTRY_COUNT:
        raise ValueError("NGAP dental scope metadata mismatch")

    forbidden = {"verification_status", "validated_by_practitioner_id", "validated_at"}
    if forbidden.intersection(payload):
        raise ValueError("Runtime certification fields are forbidden in canonical JSON")

    return payload


def validate_ngap_dental_conditions(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate source-bound legal conditions separately from act coefficients."""

    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported NGAP dental conditions schema version")
    if payload.get("dataset_id") != CONDITIONS_DATASET_ID:
        raise ValueError("Unexpected NGAP dental conditions dataset id")
    _validate_provenance(payload, context="NGAP dental conditions")

    conditions = payload.get("conditions")
    if not isinstance(conditions, dict) or not conditions:
        raise ValueError("NGAP dental conditions are missing")
    for key, value in conditions.items():
        if not isinstance(key, str) or not _CONDITION_KEY_RE.fullmatch(key):
            raise ValueError(f"Invalid NGAP dental condition key: {key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Empty NGAP dental condition: {key}")

    forbidden = {"verification_status", "validated_by_practitioner_id", "validated_at"}
    if forbidden.intersection(payload):
        raise ValueError("Runtime certification fields are forbidden in conditions JSON")

    return payload


def validate_ngap_dental_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the exact locked binary identity separately from discovery URLs."""

    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported NGAP dental provenance schema version")
    if payload.get("dataset_id") != PROVENANCE_DATASET_ID:
        raise ValueError("Unexpected NGAP dental provenance dataset id")
    if payload.get("status") != "LOCKED_BINARY_REFERENCE_ONLY":
        raise ValueError("NGAP dental provenance must remain reference-only")

    locked = payload.get("locked_binary")
    if not isinstance(locked, dict):
        raise ValueError("NGAP dental locked binary metadata is missing")
    if locked.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("NGAP dental locked binary hash mismatch")
    if locked.get("filename") != "bo_5414_fr.pdf":
        raise ValueError("NGAP dental locked binary filename mismatch")
    if locked.get("page_count") != 220 or locked.get("byte_size") != 11334738:
        raise ValueError("NGAP dental locked binary dimensions mismatch")

    sources = payload.get("discovery_sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("NGAP dental discovery sources are missing")
    for source in sources:
        if not isinstance(source, dict) or source.get("role") != "TEXT_CORROBORATION_NOT_LOCKED_BINARY":
            raise ValueError("NGAP dental discovery source role is unsafe")
        if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
            raise ValueError("NGAP dental discovery source URL is invalid")

    return payload


def _load_json_object(path: Path | str, *, context: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{context} root must be an object")
    return payload


def load_ngap_dental_reference(path: Path | str | None = None) -> dict[str, Any]:
    reference_path = Path(path) if path is not None else DEFAULT_REFERENCE_PATH
    payload = validate_ngap_dental_reference(
        _load_json_object(reference_path, context="NGAP dental reference")
    )

    # v1 stored a Ministry standalone-PDF URL beside the SHA of the locked full BO.
    # Never expose that discovery locator as the binary that produced the locked hash.
    reference = payload["reference"]
    discovery_url = reference.pop("primary_url", None)
    if discovery_url:
        reference["discovery_url"] = discovery_url
    reference["locked_binary_url"] = None

    # Conditions have their own source-bound dataset. Avoid two competing rule surfaces.
    payload.pop("rules", None)
    payload["conditions_dataset_id"] = CONDITIONS_DATASET_ID
    payload["provenance_dataset_id"] = PROVENANCE_DATASET_ID
    return payload


def load_ngap_dental_conditions(path: Path | str | None = None) -> dict[str, Any]:
    conditions_path = Path(path) if path is not None else DEFAULT_CONDITIONS_PATH
    return validate_ngap_dental_conditions(
        _load_json_object(conditions_path, context="NGAP dental conditions")
    )


def load_ngap_dental_provenance(path: Path | str | None = None) -> dict[str, Any]:
    provenance_path = Path(path) if path is not None else DEFAULT_PROVENANCE_PATH
    return validate_ngap_dental_provenance(
        _load_json_object(provenance_path, context="NGAP dental provenance")
    )


def load_ngap_dental_bundle(
    reference_path: Path | str | None = None,
    conditions_path: Path | str | None = None,
    provenance_path: Path | str | None = None,
) -> dict[str, dict[str, Any]]:
    """Load mapping, conditions and exact source identity without runtime certification."""

    reference = load_ngap_dental_reference(reference_path)
    conditions = load_ngap_dental_conditions(conditions_path)
    provenance = load_ngap_dental_provenance(provenance_path)
    hashes = {
        reference["reference"]["source_sha256"],
        conditions["reference"]["source_sha256"],
        provenance["locked_binary"]["sha256"],
    }
    if hashes != {EXPECTED_SOURCE_SHA256}:
        raise ValueError("NGAP dental bundle source hash mismatch")
    return {"reference": reference, "conditions": conditions, "provenance": provenance}


def index_ngap_dental_reference(payload: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Return a code-keyed human-readable view after full validation."""

    validated = validate_ngap_dental_reference(payload) if payload is not None else load_ngap_dental_reference()
    columns = validated["columns"]
    return {row[0]: dict(zip(columns, row, strict=True)) for row in validated["acts"]}
