"""Conservative source-locked, offline FACAD/DC manual candidate difference diagnostic.

Never launch FACAD, read vendor exports, verify clinical geometry, or promote parity.
Do not use patient names, credentials, or proprietary FACAD files in CI.
"""
from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs/audits/schemas"
MAPPING = SCHEMAS / "ortho_lot08_facad_dc_existing_protocol_mapping_v1.json"
BACKLOG = SCHEMAS / "ortho_lot08_facad_dc_unmapped_backlog_v1.json"
FINAL_SEVEN = SCHEMAS / "ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json"
MANIFEST = SCHEMAS / "ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json"
INPUT_SCHEMA = "FACAD_DC_MANUAL_DELTA_DIAGNOSTIC_INPUT_V1"
OUTPUT_SCHEMA = "FACAD_DC_MANUAL_DELTA_DIAGNOSTIC_OUTPUT_V1"
TARGET_32F = "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET"
TARGET_13F = "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET"
ROW_KEYS = frozenset({"profile_target_id", "facad_order", "facad_label", "facad_value",
                       "facad_unit", "dc_measurement_id", "dc_value", "dc_unit",
                       "geometry_identity_verified", "sign_orientation_verified", "rounding_verified"})


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_lock() -> dict:
    mapping, backlog, final, manifest = map(
        read, (MAPPING, BACKLOG, FINAL_SEVEN, MANIFEST)
    )
    require(mapping["rules"]["canonical_label_match_does_not_prove_geometry_equivalence"] is True,
            "labels must never imply geometric equivalence")
    mapped = mapping["profiles"]["Ricketts (32 F)"]["mappings"]
    resolved = backlog["profiles"]["Ricketts (32 F)"]["resolved_items"]
    require(len(mapped) == 6 and len(resolved) == 26, "expected 6+26 source-locked 32F labels")
    labels = {}
    for entry in resolved:
        label = entry["facad_label"]
        require(label not in labels and label not in mapped, "duplicate vendor label")
        labels[label] = entry["resolution"]
    require(len(set(mapped) | set(labels)) == 32, "32F vendor roster incomplete")
    counts = {p["target_id"]: p["expected_facad_factor_count"] for p in manifest["profiles"]}
    require(counts == {TARGET_32F: 32, TARGET_13F: 13}, "FACAD profile counts drifted")
    require(manifest["status"] == "DIRECT_DEFINITION_OBSERVED" and
            not manifest["evidence_records"] and not manifest["parity_rows"],
            "canonical source must remain definition-only")
    seven = final["resolutions"]
    require(len(seven) == 7 and set(seven) == set(final["scope"]) and set(seven) <= set(mapped) | set(labels),
            "seven geometry source definitions incomplete")
    positions = {}
    for label, d in seven.items():
        require(d["dc"].get("direct_alias_allowed") is False, "unsafe alias allowed")
        order = d["facad"]["order"]
        require(type(order) is int and 1 <= order <= 32 and order not in positions.values(),
                "invalid seven-factor order")
        positions[label] = order
    return {"mapped": mapped, "resolved": labels, "seven": positions, "counts": counts}


def readiness_report() -> dict:
    lock = source_lock()
    return {
        "schema_version": OUTPUT_SCHEMA,
        "scope": "SOURCE_LOCKED_READINESS_ONLY",
        "source_32f_labels": sorted(set(lock["mapped"]) | set(lock["resolved"])),
        "source_32f_label_count": 32,
        "source_13f_factor_positions": list(range(1, 14)),
        "source_13f_named_roster_independently_available": False,
        "sensitive_32f_no_direct_alias": [
            {"facad_label": k, "facad_order": v, "resolution": lock["resolved"][k]}
            for k, v in sorted(lock["seven"].items(), key=lambda pair: pair[1])
        ],
        "manual_candidate_delta_rows": [],
        "numeric_clinical_parity_rows": 0,
        "numeric_clinical_parity_proved": False,
        "vendor_source_data_read": False,
        "clinical_no_go": True,
        "warning": "Never interpret a manual numeric delta or equal value as clinical parity.",
    }


def decimal_value(v: object) -> Decimal | None:
    if v is None:
        return None
    require(type(v) is str and re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?", v) is not None,
            "numerics must be decimal STRINGS, not floats, NaN, locale or exponential values")
    try:
        out = Decimal(v)
    except InvalidOperation as exc:
        raise ValueError("invalid numeric candidate") from exc
    require(out.is_finite() and abs(out) <= Decimal("100000"), "unbounded numeric candidate")
    return out


def diagnostic(data: dict) -> dict:
    """Optionally process manual candidate readings; NEVER assert clinical parity."""
    lock = source_lock()
    require(type(data) is dict and set(data) == {"schema_version", "same_trace_case_id", "rows"},
            "unexpected input fields (patient details/secrets forbidden)")
    require(data["schema_version"] == INPUT_SCHEMA, "unsupported manual diagnostic schema")
    require(type(data["same_trace_case_id"]) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{8,64}", data["same_trace_case_id"]) is not None,
            "use an opaque tracing identifier")
    entries = data["rows"]
    require(type(entries) is list and len(entries) <= 45, "at most 45 candidates")
    seen_pairs, seen_names, result = set(), set(), []
    for item in entries:
        require(type(item) is dict and set(item) == ROW_KEYS, "invalid candidate fields")
        target, order, label = item["profile_target_id"], item["facad_order"], item["facad_label"]
        require(target in lock["counts"] and type(order) is int and
                1 <= order <= lock["counts"][target], "invalid vendor factor/order")
        require(type(label) is str and 0 < len(label) <= 80, "invalid vendor label")
        require((target, order) not in seen_pairs and (target, label) not in seen_names,
                "duplicate vendor slot or name")
        seen_pairs.add((target, order))
        seen_names.add((target, label))
        if target == TARGET_32F:
            require(label in lock["mapped"] or label in lock["resolved"], "unknown 32F vendor label")
            require(label not in lock["seven"] or lock["seven"][label] == order,
                    "seven-sensitive vendor factor order mismatch")
        dc_id = item["dc_measurement_id"]
        require(type(dc_id) is str and
                (not dc_id or re.fullmatch(r"M_[A-Z0-9_]{4,100}", dc_id) is not None),
                "DC measurement ID must be a valid explicit ID or empty")
        for field in ("geometry_identity_verified", "sign_orientation_verified", "rounding_verified"):
            require(type(item[field]) is bool, "identity/sign/rounding flags must be boolean")
        fv, dv = decimal_value(item["facad_value"]), decimal_value(item["dc_value"])
        fu, du = item["facad_unit"], item["dc_unit"]
        require(fu in ("mm", "deg") and du in ("mm", "deg"), "unsupported unit")
        gates = []
        if target == TARGET_13F:
            gates.append("13F_NAMED_VENDOR_ROSTER_NOT_IN_THIS_SOURCE")
        if target == TARGET_32F:
            if label in lock["seven"]:
                gates.append("SEVEN_SENSITIVE_DIRECT_ALIAS_FORBIDDEN")
            resolution = lock["resolved"].get(label, "")
            if "STRICT_EQUIVALENCE_FORBIDDEN" in resolution:
                gates.append("STRICT_EQUIVALENCE_FORBIDDEN")
            if "FACAD_VENDOR" in resolution:
                gates.append("VENDOR_VARIANT_REQUIRES_SEPARATE_GEOMETRY")
        if fu != du:
            gates.append("UNIT_MISMATCH")
        if fv is None or dv is None:
            gates.append("NUMERIC_MISSING")
        if not dc_id:
            gates.append("DC_CANONICAL_ID_MISSING")
        for field, gate in (
            ("geometry_identity_verified", "GEOMETRY_IDENTITY_UNPROVEN"),
            ("sign_orientation_verified", "SIGN_ORIENTATION_UNPROVEN"),
            ("rounding_verified", "ROUNDING_UNPROVEN"),
        ):
            if not item[field]:
                gates.append(gate)
        delta = None if gates else format(fv - dv, "f")
        result.append({
            "profile_target_id": target, "facad_order": order, "facad_label": label,
            "dc_measurement_id": dc_id, "unit": fu if fu == du else None,
            "raw_decimal_delta_facad_minus_dc": delta, "gates": gates,
            "status": "RAW_MANUAL_DIFFERENCE_UNVERIFIED" if delta is not None
                      else "NO_DIAGNOSTIC_DIFFERENCE_ALLOWED",
            "clinical_parity_proved": False,
        })
    output = readiness_report()
    output["scope"] = "MANUAL_TRANSCRIPTION_DIAGNOSTIC_ONLY_NO_VENDOR_EXPORT_PROOF"
    output["manual_candidate_delta_rows"] = sorted(result, key=lambda r: (r["profile_target_id"], r["facad_order"]))
    output["manual_rows_reviewed"] = len(result)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual-input", type=Path,
                        help="Optional PRIVATE manual candidate JSON OUTSIDE repository")
    parser.add_argument("--private-output", type=Path, required=True,
                        help="New PRIVATE JSON report OUTSIDE repository")
    args = parser.parse_args()
    try:
        output = args.private_output.resolve()
        require(not output.is_relative_to(ROOT.resolve()) and not output.exists(),
                "output must be new and outside Git repository")
        require(output.parent.is_dir() and not output.parent.is_symlink(),
                "private output parent must exist")
        if args.manual_input:
            path = args.manual_input.resolve(strict=True)
            require(not path.is_relative_to(ROOT.resolve()) and path.is_file() and
                    path.stat().st_size <= 200_000, "input must be a small private file outside repo")
            report = diagnostic(read(path))
        else:
            report = readiness_report()
        with output.open("x", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FACAD_MANUAL_DIAGNOSTIC_FAIL_CLOSED={type(exc).__name__}: {exc}")
        return 2
    print("FACAD_SOURCE_LOCKED_READINESS_32F=32")
    print("FACAD_SOURCE_LOCKED_READINESS_13F=13_POSITIONS_ONLY")
    print("FACAD_NUMERIC_CLINICAL_PARITY_ROWS=0")
    print("CLINICAL_NO_GO=true")
    print(f"FACAD_PRIVATE_REPORT={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
