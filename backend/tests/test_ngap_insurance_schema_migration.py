import importlib.util
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from backend.core.sqlite_alembic_baseline import bootstrap_empty_sqlite_to_head
from backend.models import Base


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_FILENAME = "d0b000000003_add_ngap_insurance_schema.py"


def _load_migration():
    path = ROOT / "alembic" / "versions" / MIGRATION_FILENAME
    spec = importlib.util.spec_from_file_location("ngap_insurance_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _alembic_heads() -> list[str]:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    return list(ScriptDirectory.from_config(config).get_heads())


def test_ngap_insurance_migration_is_current_unique_head():
    migration = _load_migration()
    assert migration.down_revision == "d0b000000002"
    assert _alembic_heads() == ["d0b000000003"]


def test_ngap_insurance_migration_is_additive_repeatable_and_preserves_actes():
    migration = _load_migration()
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE catalog_acts (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text(
                "CREATE TABLE actes ("
                "id INTEGER PRIMARY KEY, "
                "legacy_value TEXT NOT NULL"
                ")"
            )
        )
        connection.execute(
            text("INSERT INTO actes (id, legacy_value) VALUES (7, 'preserve-me')")
        )

        context = MigrationContext.configure(connection)
        migration.op = Operations(context)
        migration.upgrade()
        migration.upgrade()

        inspector = inspect(connection)
        assert "ngap_catalog_mappings" in set(inspector.get_table_names())
        assert {column["name"] for column in inspector.get_columns("ngap_catalog_mappings")} >= {
            "catalog_act_id",
            "code_kind",
            "ngap_code",
            "coefficient",
            "reference_version",
            "mapping_rule_id",
            "verification_status",
            "source_hash",
            "validated_by_practitioner_id",
            "validated_at",
        }
        assert {column["name"] for column in inspector.get_columns("actes")} >= {
            "source_line_uid",
            "catalog_act_id",
        }
        assert {
            item["name"] for item in inspector.get_indexes("actes")
        } >= {
            "ix_actes_source_line_uid",
            "ix_actes_catalog_act_id",
        }

        row = connection.execute(
            text(
                "SELECT id, legacy_value, source_line_uid, catalog_act_id "
                "FROM actes WHERE id = 7"
            )
        ).mappings().one()
        assert dict(row) == {
            "id": 7,
            "legacy_value": "preserve-me",
            "source_line_uid": None,
            "catalog_act_id": None,
        }


def test_ngap_insurance_migration_fails_closed_on_partial_ngap_table():
    migration = _load_migration()
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE catalog_acts (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE actes (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text("CREATE TABLE ngap_catalog_mappings (id INTEGER PRIMARY KEY)")
        )

        context = MigrationContext.configure(connection)
        migration.op = Operations(context)
        with pytest.raises(RuntimeError, match="Critical NGAP schema mismatch"):
            migration.upgrade()


def test_empty_sqlite_baseline_materializes_ngap_and_insurance_at_current_head():
    heads = _alembic_heads()
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        assert bootstrap_empty_sqlite_to_head(
            connection,
            Base.metadata,
            heads,
        ) is True

        inspector = inspect(connection)
        assert connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one() == "d0b000000003"
        assert "ngap_catalog_mappings" in set(inspector.get_table_names())
        assert {column["name"] for column in inspector.get_columns("actes")} >= {
            "source_line_uid",
            "catalog_act_id",
        }


def test_insurance_linkage_install_does_not_register_implicit_schema_ddl():
    source = (ROOT / "backend" / "models_insurance_linkage.py").read_text(
        encoding="utf-8"
    )
    assert "event.listen" not in source
    assert "before_create" not in source
    assert "def migrate_insurance_linkage_columns" in source
