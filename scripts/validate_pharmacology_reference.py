from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITS = ROOT / "docs" / "audits"

HISTORICAL = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv"
HISTORICAL_MAP = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_HISTORICAL_TO_CANONICAL_MAP_V1_2026-09-17.csv"
ADDENDUM_1 = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_INVENTORY_ADDENDUM_2026-09-16.csv"
ADDENDUM_2 = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_INVENTORY_ADDENDUM_V2_2026-09-16.csv"
ADDENDA_MAP = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_ADDENDA_TO_CANONICAL_MAP_V1_2026-09-17.csv"
PARA_BASE = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_CANONICAL_MATRIX_V1_2026-09-17.csv"
PARA_GAPS = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_CANONICAL_GAP_RESOLUTION_V1_2026-09-17.csv"
PARA_ADDENDA = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_ADDENDA_CANONICAL_EXTENSION_V1_2026-09-17.csv"
ENTITY_V1 = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_CANONICAL_ENTITY_MAP_V1_2026-09-16.csv"
ENTITY_V2 = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_CANONICAL_ENTITY_MAP_V2_EXTENSION_2026-09-17.csv"

EXPECTED_HISTORICAL_ROWS = 170
EXPECTED_ADDENDA_ROWS = 8
EXPECTED_STRUCTURAL_GAPS = 20
EXPECTED_HISTORICAL_TARGET_REFERENCES = 173


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _ids(rows: list[dict[str, str]], key: str) -> list[str]:
    return [row.get(key, "").strip() for row in rows]


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _activation_errors(root: Path) -> list[str]:
    errors: list[str] = []
    audits = root / "docs" / "audits"
    for path in sorted(audits.glob("PRESCRIPTION_PHARMACOLOGY_MOROCCO_*.csv")):
        rows = _rows(path)
        if not rows or "clinical_activation" not in rows[0]:
            continue
        for index, row in enumerate(rows, start=2):
            raw_value = row.get("clinical_activation")
            value = (raw_value or "").strip().upper()
            if value != "NO":
                errors.append(
                    f"{path.name}:{index} clinical_activation must fail closed to NO, got {value!r}"
                )
    return errors


def validate(root: Path = ROOT) -> list[str]:
    global AUDITS
    errors: list[str] = []
    audits = root / "docs" / "audits"

    def rows(name: str) -> list[dict[str, str]]:
        return _rows(audits / name)

    historical = rows(HISTORICAL.name)
    historical_map = rows(HISTORICAL_MAP.name)
    addendum_1 = rows(ADDENDUM_1.name)
    addendum_2 = rows(ADDENDUM_2.name)
    addenda_map = rows(ADDENDA_MAP.name)
    para_base = rows(PARA_BASE.name)
    para_gaps = rows(PARA_GAPS.name)
    para_addenda = rows(PARA_ADDENDA.name)
    entity_v1 = rows(ENTITY_V1.name)
    entity_v2 = rows(ENTITY_V2.name)

    historical_ids = _ids(historical, "id")
    mapped_ids = _ids(historical_map, "historical_id")
    addendum_ids = _ids(addendum_1, "id") + _ids(addendum_2, "id")
    mapped_addenda_ids = _ids(addenda_map, "source_id")

    if len(historical_ids) != EXPECTED_HISTORICAL_ROWS:
        errors.append(f"historical inventory must contain {EXPECTED_HISTORICAL_ROWS} rows, got {len(historical_ids)}")
    if _duplicates(historical_ids):
        errors.append(f"historical inventory contains duplicate IDs: {sorted(_duplicates(historical_ids))}")
    if len(mapped_ids) != EXPECTED_HISTORICAL_ROWS:
        errors.append(f"historical map must contain {EXPECTED_HISTORICAL_ROWS} rows, got {len(mapped_ids)}")
    if _duplicates(mapped_ids):
        errors.append(f"historical map contains duplicate source IDs: {sorted(_duplicates(mapped_ids))}")
    if set(mapped_ids) != set(historical_ids):
        errors.append("historical map source IDs do not exactly match the 170-row source inventory")

    if len(addendum_ids) != EXPECTED_ADDENDA_ROWS:
        errors.append(f"addenda must contain {EXPECTED_ADDENDA_ROWS} rows, got {len(addendum_ids)}")
    if _duplicates(addendum_ids):
        errors.append(f"addenda contain duplicate IDs: {sorted(_duplicates(addendum_ids))}")
    if len(mapped_addenda_ids) != EXPECTED_ADDENDA_ROWS:
        errors.append(f"addenda map must contain {EXPECTED_ADDENDA_ROWS} rows, got {len(mapped_addenda_ids)}")
    if set(mapped_addenda_ids) != set(addendum_ids):
        errors.append("addenda map source IDs do not exactly match the 8 addendum rows")

    gap_ids = _ids(para_gaps, "gap_id")
    if len(gap_ids) != EXPECTED_STRUCTURAL_GAPS or len(set(gap_ids)) != EXPECTED_STRUCTURAL_GAPS:
        errors.append(
            f"canonical structural gap extension must contain {EXPECTED_STRUCTURAL_GAPS} unique gap IDs, got {len(set(gap_ids))}"
        )

    para_ids = set(_ids(para_base, "canonical_id")) | set(_ids(para_gaps, "canonical_id")) | set(
        _ids(para_addenda, "canonical_id")
    )
    entity_ids = set(_ids(entity_v1, "canonical_entity_id")) | set(_ids(entity_v2, "canonical_entity_id"))
    medicine_ids = set(historical_ids) | set(addendum_ids)
    gap_aliases = set(gap_ids)

    target_refs = 0
    unresolved: list[str] = []
    for row in historical_map:
        raw = row.get("canonical_target", "").strip()
        targets = [part.strip() for part in raw.split("|") if part.strip()]
        target_refs += len(targets)
        if len(targets) > 1 and not row.get("required_discriminator", "").strip():
            errors.append(f"{row.get('historical_id')} split mapping lacks required discriminator")
        for target in targets:
            if target in para_ids or target in entity_ids or target in medicine_ids or target in gap_aliases:
                continue
            unresolved.append(f"{row.get('historical_id')}->{target}")

    if target_refs != EXPECTED_HISTORICAL_TARGET_REFERENCES:
        errors.append(
            f"historical map must resolve to {EXPECTED_HISTORICAL_TARGET_REFERENCES} target references, got {target_refs}"
        )
    if unresolved:
        errors.append(f"unresolved canonical targets: {sorted(unresolved)}")

    gap_targets_from_map = {
        target.strip()
        for row in historical_map
        for target in row.get("canonical_target", "").split("|")
        if target.strip().startswith("GAP-")
    }
    if gap_targets_from_map != gap_aliases:
        missing = sorted(gap_targets_from_map - gap_aliases)
        orphan = sorted(gap_aliases - gap_targets_from_map)
        errors.append(f"gap alias mismatch; missing={missing}, orphan={orphan}")

    for row in entity_v1 + entity_v2:
        relation = row.get("relation_type", "").upper()
        if any(token in relation for token in ("DUPLICATE", "OVERLAP", "BOUNDARY")):
            if row.get("auto_merge_allowed", "").strip().upper() != "NO":
                errors.append(
                    f"{row.get('source_id')} relation {relation} must never auto-merge"
                )
            if not row.get("required_discriminator", "").strip():
                errors.append(
                    f"{row.get('source_id')} relation {relation} requires an explicit discriminator"
                )

    errors.extend(_activation_errors(root))
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "PASS: pharmacology reference fail-closed integrity "
        f"({EXPECTED_HISTORICAL_ROWS} historical + {EXPECTED_ADDENDA_ROWS} addenda, "
        f"{EXPECTED_STRUCTURAL_GAPS} structural gaps, activation=NO)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())