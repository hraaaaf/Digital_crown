import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "v7100000022_agenda_identity_defaults.py"


def _load():
    spec = importlib.util.spec_from_file_location("agenda_identity_defaults", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Dialect:
    def __init__(self, name: str):
        self.name = name
        self.identifier_preparer = type("P", (), {"quote": staticmethod(lambda value: f'"{value}"')})()


class _Bind:
    def __init__(self, dialect_name: str):
        self.dialect = _Dialect(dialect_name)
        self.sql: list[str] = []

    def execute(self, statement):
        self.sql.append(str(statement))


def test_pg_identity_default_uses_sequence_and_syncs_after_existing_rows():
    migration = _load()
    bind = _Bind("postgresql")

    migration._ensure_pg_pk_default(bind, "cabinet_settings")

    rendered = "\n".join(bind.sql)
    assert 'CREATE SEQUENCE IF NOT EXISTS "cabinet_settings_id_seq"' in rendered
    assert "SELECT MAX(id) FROM \"cabinet_settings\"" in rendered
    assert "SET DEFAULT nextval('cabinet_settings_id_seq')" in rendered
    assert 'OWNED BY "cabinet_settings".id' in rendered


def test_non_postgres_is_noop():
    migration = _load()
    bind = _Bind("sqlite")

    migration._ensure_pg_pk_default(bind, "cabinet_settings")

    assert bind.sql == []
