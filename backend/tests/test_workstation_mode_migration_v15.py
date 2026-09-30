import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect


def _load_revision_module():
    repo_root = Path(__file__).resolve().parents[2]
    revision_path = repo_root / "alembic" / "versions" / "v7100000021_workstation_mode_memory.py"
    spec = importlib.util.spec_from_file_location("v7100000021_workstation_mode_memory", revision_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workstation_mode_migration_upgrade_downgrade_roundtrip(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'workstation-mode.sqlite'}")
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    revision = _load_revision_module()

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        original_op = revision.op
        revision.op = operations
        try:
            revision.upgrade()
            inspector = inspect(connection)
            assert "workstation_modes" in inspector.get_table_names()
            assert "workstation_security_policies" in inspector.get_table_names()

            workstation_columns = {column["name"] for column in inspector.get_columns("workstation_modes")}
            assert {
                "id",
                "employer_id",
                "token_hash",
                "default_experience",
                "mode_revision",
                "updated_by_user_id",
                "created_at",
                "updated_at",
            }.issubset(workstation_columns)

            check_names = {
                constraint["name"]
                for constraint in inspector.get_check_constraints("workstation_modes")
            }
            assert "ck_workstation_default_experience" in check_names

            revision.downgrade()
            inspector = inspect(connection)
            assert "workstation_modes" not in inspector.get_table_names()
            assert "workstation_security_policies" not in inspector.get_table_names()

            revision.upgrade()
            inspector = inspect(connection)
            assert "workstation_modes" in inspector.get_table_names()
            assert "workstation_security_policies" in inspector.get_table_names()
        finally:
            revision.op = original_op
