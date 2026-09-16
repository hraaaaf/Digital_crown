"""Validated loader for the audited dental subset of Morocco's NGAP 177-06.

Reference-only by design: loading this JSON never certifies a CatalogAct mapping and
never promotes a row to VERIFIED_PRIMARY. Runtime activation still requires the
existing source-lock and practitioner-validation gates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATASET_ID = "ngap-dental-177-06-v1"
EXPECTED_SOURCE_SHA256 = "e9db137d6a758bd4ad7a506a94a7c0c84726813de3db1e225c761318a75e1fdb"
REFERENCE_STATUS = "REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED"
EXPECTED_ENTRY_COUNT = 145
EXPECTED_COLUMNS = ["code", "acte", "coefficient", "anesthesia_coefficient", "entry_type"]
DEFAULT_REFERENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "ngap_dental_177_06.json"
_CODE_RE = re.compile(r"^D\d{3}$")
_ALLOWED_ENTRY_TYPES = {"act", "anesthesia", "ceiling", "calculation_rule", "quote_required"}


def _expected_codes() -> list[str]:
    return [
        *(f"D{value}" for value in range(600, 642)),
        *(f"D{value}" for value in range(700, 786)),
        *(f"D{value}" for value in range(800, 817)),
    ]


def validate_ngap_dental_reference(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate structure, coverage and provenance without activating runtime mappings."""

    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported NGAP dental reference schema version")
    if payload.get("dataset_id") != DATASET_ID:
        raise ValueError("Unexpected NGAP dental dataset id")
    if payload.get("status") != REFERENCE_STATUS:
        raise ValueError("NGAP dental reference must remain reference-only")

    reference = payload.get("reference")
    if not isinstance(reference, dict):
        raise ValueError("NGAP dental reference provenance is missing")
    if reference.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("NGAP dental primary source hash mismatch")
    if reference.get("arrete") != "177-06 du 26 hija 1426 (27 janvier 2006)":
        raise ValueError("NGAP dental legal reference mismatch")

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

    # A canonical JSON is evidence, not runtime certification.
    forbidden = {"verification_status", "validated_by_practitioner_id", "validated_at"}
    if forbidden.intersection(payload):
        raise ValueError("Runtime certification fields are forbidden in canonical JSON")

    return payload


def load_ngap_dental_reference(path: Path | str | None = None) -> dict[str, Any]:
    reference_path = Path(path) if path is not None else DEFAULT_REFERENCE_PATH
    with reference_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("NGAP dental reference root must be an object")
    return validate_ngap_dental_reference(payload)


def index_ngap_dental_reference(payload: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Return a code-keyed human-readable view after full validation."""

    validated = validate_ngap_dental_reference(payload) if payload is not None else load_ngap_dental_reference()
    columns = validated["columns"]
    return {row[0]: dict(zip(columns, row, strict=True)) for row in validated["acts"]}
