"""Presentation-only McNamara/Ricketts R23-G2 PDF sections.

Do not compute measurements or assert clinical validity. Strictly consume
the verified backend typed profile projection. Invalid/stale data yields
an explicit blocked section, never reconstructed/fabricated values.
"""
from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

_PROFILES = (
    ("mcnamara", "McNamara 1984", "MCNAMARA_1984_SINGLE_FILM_V1", 13,
     "WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL", "HISTORICAL_WORKING_REFERENCE_ONLY"),
    ("ricketts_atlas2009", "Ricketts Atlas 2009", "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1", 33,
     "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL",
     "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED"),
    ("ricketts_gregoret13", "Ricketts Gregoret 1997", "RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1", 13,
     "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED",
     "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED"),
)
_STATES = frozenset({"AVAILABLE", "MISSING", "INVALID", "NOT_APPLICABLE", "NOT_COMPUTABLE"})


def project_r23g2_pdf_sections(
    profiles: Mapping[str, Any], *, active_runtime_chain_verified: bool,
) -> list[dict[str, Any]]:
    """Expose only complete and consistent versioned profiles, in source order."""
    output: list[dict[str, Any]] = []
    for slot, title, profile_id, count, status, gate in _PROFILES:
        section: dict[str, Any] = {
            "slot": slot, "title": title, "protocol_profile_id": profile_id,
            "expected_rows": count, "verified": False, "rows": [],
            "warning": "Profil non vérifié ou chaîne scientifique périmée : aucune mesure affichée.",
        }
        try:
            profile = profiles.get(slot)
            if not active_runtime_chain_verified or not isinstance(profile, dict):
                raise ValueError("missing active verified profile")
            rows = profile.get("rows")
            if (profile.get("protocol_profile_id") != profile_id
                or profile.get("profile_status") != status
                or profile.get("source_lock_gate") != gate
                or profile.get("classification_authority") is not False
                or not isinstance(rows, list) or len(rows) != count):
                raise ValueError("profile identity, authority or cardinality mismatch")
            seen: set[str] = set()
            verified_rows = []
            for i, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    raise ValueError("invalid row")
                key = row.get("canonical_measurement_id")
                state = row.get("availability_status")
                value = row.get("value")
                if (row.get("order") != i or not isinstance(key, str)
                    or not key.startswith("M_") or key in seen
                    or row.get("source_contract") != profile_id
                    or row.get("classification_authority") is not False
                    or state not in _STATES):
                    raise ValueError("noncanonical, duplicated or unordered row")
                seen.add(key)
                if state == "AVAILABLE":
                    if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not isfinite(value) or not row.get("value_authority_method_id")
                        or not isinstance(row.get("measurement_refs"), list)
                        or not row["measurement_refs"]):
                        raise ValueError("unsupported available measurement")
                    shown = f"{value:g} {row.get('unit') or ''}".strip()
                else:
                    if value is not None:
                        raise ValueError("nonavailable row carrying a numeric value")
                    shown = "NC — non calculable"
                verified_rows.append({
                    "canonical_measurement_id": key,
                    "label": str(row.get("label") or key),
                    "value": shown,
                    "availability_status": state,
                    "contract_state": str(row.get("contract_state") or "NON VERIFIE"),
                })
            section.update({"verified": True, "rows": verified_rows, "warning":
                "Document de travail : aucune validation clinique, normative ou Facad."})
        except (ValueError, TypeError, AttributeError, KeyError):
            pass
        output.append(section)
    return output
