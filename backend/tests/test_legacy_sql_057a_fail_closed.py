import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "filename,owner,method",
    [
        ("guided_restore.py", "GuidedRestoreService", "request_apply"),
        ("guided_restore_worker.py", "GuidedRestoreWorker", "run"),
    ],
)
def test_restore_entrypoint_denies_before_side_effects(filename, owner, method):
    path = ROOT / "backend" / "services" / filename
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner)
    fn = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method)
    first = fn.body[0]
    assert isinstance(first, ast.Raise), "Must deny before job reads and filesystem mutations"
    error = first.exc
    assert isinstance(error, ast.Call)
    assert isinstance(error.func, ast.Name) and error.func.id == "RuntimeError"
    assert len(error.args) == 1 and isinstance(error.args[0], ast.Constant)
    assert "autorité worker non attestée" in error.args[0].value
