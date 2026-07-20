from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "scientific_validator", ROOT / "scripts" / "validate_scientific_ai_assets.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / ".claude", root / ".claude")
    shutil.copytree(ROOT / "docs" / "scientific-ai", root / "docs" / "scientific-ai")
    return root


def test_current_scientific_assets_validate() -> None:
    assert validator.validate(ROOT) == []


def test_rejects_write_tool_on_audit_skill(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / ".claude" / "skills" / "audit-prescription-flow" / "SKILL.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "allowed-tools: Read, Grep, Glob, Bash",
        "allowed-tools: Read, Grep, Glob, Bash, Edit",
    ), encoding="utf-8")
    assert any("allows writes" in error for error in validator.validate(root))


def test_rejects_untraceable_clinical_approval(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "scientific-ai" / "SOURCE_REGISTRY.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["status"] = "approved-by-clinician"
    data["sources"][0]["reviewed_by"] = ""
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert any("untraceable clinical approval" in error for error in validator.validate(root))


def test_rejects_weak_eval_structure(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / ".claude" / "skills" / "implement-cephalo-measurement" / "evals" / "evals.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["ambiguous_cases"] = []
    path.write_text(json.dumps(data), encoding="utf-8")
    assert any("ambiguous_cases" in error for error in validator.validate(root))


def test_rejects_schema_without_required_contract(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    path = root / "docs" / "scientific-ai" / "templates" / "cephalo-measurement.schema.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.pop("required")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert any("incomplete machine-readable schema" in error for error in validator.validate(root))

