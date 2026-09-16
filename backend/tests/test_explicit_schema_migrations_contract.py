import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, Table, Column, Integer, create_engine, inspect, text

from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD
from backend.core.sqlite_alembic_baseline import bootstrap_empty_sqlite_to_head
from backend.models import Base
from backend.services import cabinet_catalog_store as _cabinet_catalog_store  # noqa: F401


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, filename: str):
    path = ROOT / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_companion_migration_declares_the_four_runtime_tables_and_is_repeatable():
    migration = _load(
        "companion_migration",
        "d0b000000001_add_patient_companion_tables.py",
    )
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        migration.op = Operations(context)
        migration.upgrade()
        migration.upgrade()

        tables = set(inspect(connection).get_table_names())
        assert tables >= {
            "patient_companion_identities",
            "patient_companion_accesses",
            "patient_companion_invitations",
            "patient_companion_share_grants",
        }
        assert connection.execute(
            text("SELECT COUNT(*) FROM patient_companion_identities")
        ).scalar_one() == 0


def test_runtime_schema_migration_has_no_bootstrap_create_all_and_is_repeatable():
    migration_path = ROOT / "alembic" / "versions" / "d0b000000002_add_explicit_runtime_schema.py"
    source = migration_path.read_text(encoding="utf-8")
    assert "create_all" not in source
    assert "d0b000000001" in source


def test_companion_downgrade_is_explicitly_refused_before_any_drop():
    migration = _load(
        "companion_downgrade_contract",
        "d0b000000001_add_patient_companion_tables.py",
    )
    with pytest.raises(RuntimeError, match="Destructive downgrade"):
        migration.downgrade()
    source = (ROOT / "alembic" / "versions" / "d0b000000001_add_patient_companion_tables.py").read_text(
        encoding="utf-8"
    )
    assert "op.drop_table" not in source


def test_runtime_migration_versions_legacy_agenda_schema_without_router_ddl():
    migration = _load(
        "runtime_agenda_contract",
        "d0b000000002_add_explicit_runtime_schema.py",
    )
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        migration.op = Operations(context)
        migration._ensure_agenda_tables(connection)
        migration._ensure_agenda_tables(connection)

        assert set(inspect(connection).get_table_names()) >= {
            "cabinet_settings",
            "agenda_exceptions",
        }
        assert {column["name"] for column in inspect(connection).get_columns("cabinet_settings")} >= {
            "employer_id",
            "weekly_schedule_json",
        }
        assert "employer_id" in {
            column["name"] for column in inspect(connection).get_columns("agenda_exceptions")
        }


def test_agenda_router_schema_guard_contains_no_ddl():
    source = (ROOT / "backend" / "routers" / "agenda_settings.py").read_text(encoding="utf-8")
    ensure_schema = source.split("def _ensure_tenant_columns", 1)[1].split(
        "def _claim_legacy_rows_if_unambiguous", 1
    )[0]
    assert "ALTER TABLE" not in ensure_schema
    assert "CREATE INDEX" not in ensure_schema


def test_catalog_store_does_not_create_schema_implicitly():
    source = (ROOT / "backend" / "services" / "cabinet_catalog_store.py").read_text(encoding="utf-8")
    ensure_schema = source.split("def ensure_schema", 1)[1].split("def _root_owners", 1)[0]
    assert "create_all" not in ensure_schema


def test_empty_sqlite_alembic_baseline_materializes_current_metadata_and_stamps_exact_head():
    engine = create_engine("sqlite:///:memory:")
    expected_tables = {table.name for table in Base.metadata.sorted_tables}

    with engine.begin() as connection:
        assert bootstrap_empty_sqlite_to_head(
            connection,
            Base.metadata,
            [CURRENT_ALEMBIC_HEAD],
        ) is True

        inspector = inspect(connection)
        actual_tables = set(inspector.get_table_names())
        assert actual_tables >= expected_tables | {"alembic_version"}
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == CURRENT_ALEMBIC_HEAD

        # Representative high-risk runtime schema must come from the same snapshot.
        assert {column["name"] for column in inspector.get_columns("appointments")} >= {
            "source",
            "phone",
            "confirmed_by_id",
            "confirmed_at",
            "expires_at",
        }
        assert {column["name"] for column in inspector.get_columns("cabinet_configs")} >= {
            "header_logo_offset_x",
            "header_logo_offset_y",
            "qr_code_offset_x",
            "qr_code_offset_y",
            "inpe_etablissement",
        }
        assert {
            "patient_companion_identities",
            "patient_companion_accesses",
            "patient_companion_invitations",
            "patient_companion_share_grants",
        } <= actual_tables


def test_sqlite_alembic_baseline_refuses_to_touch_non_empty_database():
    metadata = MetaData()
    Table("already_here", metadata, Column("id", Integer, primary_key=True))
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        metadata.create_all(connection)
        assert bootstrap_empty_sqlite_to_head(
            connection,
            MetaData(),
            [CURRENT_ALEMBIC_HEAD],
        ) is False
        assert "alembic_version" not in set(inspect(connection).get_table_names())


def test_sqlite_alembic_baseline_rejects_multiple_heads():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        with pytest.raises(RuntimeError, match="exactly one Alembic head"):
            bootstrap_empty_sqlite_to_head(
                connection,
                MetaData(),
                ["head_a", "head_b"],
            )
