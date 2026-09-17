from __future__ import annotations

import csv
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "pharmacology_reference_validator", ROOT / "scripts" / "validate_pharmacology_reference.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "docs" / "audits", root / "docs" / "audits")
    return root


def _rewrite_csv(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_current_pharmacology_reference_is_fail_closed() -> None:
    assert validator.validate(ROOT) == []


def test_rejects_any_clinical_activation(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "audits" / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_CANONICAL_MATRIX_V1_2026-09-17.csv"
    _rewrite_csv(path, lambda rows: rows[0].__setitem__("clinical_activation", "YES"))
    errors = validator.validate(root)
    assert any("clinical_activation must fail closed to NO" in error for error in errors)


def test_rejects_missing_historical_mapping_row(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "audits" / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_HISTORICAL_TO_CANONICAL_MAP_V1_2026-09-17.csv"
    _rewrite_csv(path, lambda rows: rows.pop())
    errors = validator.validate(root)
    assert any("historical map must contain 170 rows" in error for error in errors)
    assert any("do not exactly match" in error for error in errors)


def test_rejects_dangling_canonical_target(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "audits" / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_HISTORICAL_TO_CANONICAL_MAP_V1_2026-09-17.csv"
    _rewrite_csv(path, lambda rows: rows[0].__setitem__("canonical_target", "CAN-DOES-NOT-EXIST"))
    errors = validator.validate(root)
    assert any("unresolved canonical targets" in error for error in errors)


def test_rejects_auto_merge_on_overlap_entity(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "audits" / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_CANONICAL_ENTITY_MAP_V1_2026-09-16.csv"
    _rewrite_csv(path, lambda rows: rows[0].__setitem__("auto_merge_allowed", "YES"))
    errors = validator.validate(root)
    assert any("must never auto-merge" in error for error in errors)
