from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_schema_gate_matches_unique_alembic_head():
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    heads = script.get_heads()

    assert heads == [CURRENT_ALEMBIC_HEAD]
