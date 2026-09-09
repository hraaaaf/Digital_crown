"""Reachability contract for the quarantined legacy CephaloEngine.

Application runtime code may only execute the legacy engine through
``cephalo_safe_engine.py``. Tests are excluded because they may exercise the
legacy implementation directly for migration/regression purposes.
"""
from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
SAFE_ADAPTER = BACKEND / "services/cephalo_safe_engine.py"


def _imports_legacy_engine(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "backend.services.cephalo_engine":
            for alias in node.names:
                if alias.name == "cephalo_engine":
                    names.add(alias.asname or alias.name)
    return names


def _calls_calculate_metrics(tree: ast.AST, bindings: set[str]) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "calculate_metrics":
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id in bindings:
            return True
    return False


def test_no_runtime_module_calls_legacy_cephalo_engine_directly():
    offenders: list[str] = []

    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts or path == SAFE_ADAPTER:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        bindings = _imports_legacy_engine(tree)
        if bindings and _calls_calculate_metrics(tree, bindings):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], (
        "Legacy CephaloEngine.calculate_metrics bypasses the safe adapter: "
        + ", ".join(sorted(offenders))
    )


def test_safe_adapter_is_the_only_runtime_module_allowed_to_execute_legacy_engine():
    source = SAFE_ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SAFE_ADAPTER))
    bindings = _imports_legacy_engine(tree)
    assert bindings == {"_legacy_cephalo_engine"}
    assert _calls_calculate_metrics(tree, bindings)
