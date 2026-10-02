"""Isolated LOT05 V1<->V2 migration proof harness. Not product runtime."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from datetime import datetime
from typing import Any, Mapping


class Lot05MigrationError(ValueError):
    pass


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def _context_sha(patient_id: int, coordinate_space: Mapping[str, Any], quality_metadata: Mapping[str, Any]) -> str:
    payload = {
        "patient_id": patient_id,
        "coordinate_space": coordinate_space,
        "quality_metadata": quality_metadata,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

