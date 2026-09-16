import ast
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_RUNTIME = ROOT / "backend" / "core" / "schema_runtime.py"


def _declared_runtime_head() -> str:
    """Read CURRENT_ALEMBIC_HEAD without importing the backend package.

    This contract test intentionally stays at the migration boundary: importing
    ``backend.core.schema_runtime`` would execute ``backend/__init__.py`` and its
    model/service registration side effects, turning a schema-head check into an
    accidental full-backend dependency test.
    """
    module = ast.parse(SCHEMA_RUNTIME.read_text(encoding="utf-8"), filename=str(SCHEMA_RUNTIME))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "CURRENT_ALEMBIC_HEAD" for target in node.targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
        raise AssertionError("CURRENT_ALEMBIC_HEAD must remain a literal string")
    raise AssertionError("CURRENT_ALEMBIC_HEAD declaration not found")


def test_runtime_schema_gate_matches_unique_alembic_head():
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    heads = script.get_heads()

    assert heads == [_declared_runtime_head()]
