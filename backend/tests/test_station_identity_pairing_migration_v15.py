import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect


def _load(name: str, filename: str):
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_station_identity_pairing_migration_roundtrip(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'station-identity.sqlite'}")
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    base = _load("v7100000021", "v7100000021_workstation_mode_memory.py")
    revision = _load("neo000000026", "neo000000026_station_identity_pairing.py")

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        base_original = base.op
        revision_original = revision.op
        base.op = operations
        revision.op = operations
        try:
            base.upgrade()
            revision.upgrade()
            inspector = inspect(connection)
            assert "workstation_pairing_codes" in inspector.get_table_names()
            policy_columns = {column["name"] for column in inspector.get_columns("workstation_security_policies")}
            assert {
                "pairing_failed_attempts",
                "pairing_failure_window_started_at",
                "pairing_locked_until",
            }.issubset(policy_columns)
            columns = {column["name"] for column in inspector.get_columns("workstation_modes")}
            assert {"display_name", "revoked_at", "last_seen_at"}.issubset(columns)
            pairing_columns = {column["name"] for column in inspector.get_columns("workstation_pairing_codes")}
            pairing_indexes = {index["name"]: index for index in inspector.get_indexes("workstation_pairing_codes")}
            assert "uq_workstation_pairing_codes_one_active" in pairing_indexes
            assert pairing_indexes["uq_workstation_pairing_codes_one_active"]["unique"] is True
            assert {
                "id",
                "employer_id",
                "code_hash",
                "expires_at",
                "used_at",
                "created_by_user_id",
                "created_at",
            }.issubset(pairing_columns)

            revision.downgrade()
            inspector = inspect(connection)
            assert "workstation_pairing_codes" not in inspector.get_table_names()
            columns = {column["name"] for column in inspector.get_columns("workstation_modes")}
            assert "display_name" not in columns
            assert "revoked_at" not in columns
            assert "last_seen_at" not in columns
            policy_columns = {column["name"] for column in inspector.get_columns("workstation_security_policies")}
            assert "pairing_failed_attempts" not in policy_columns
            assert "pairing_failure_window_started_at" not in policy_columns
            assert "pairing_locked_until" not in policy_columns
        finally:
            base.op = base_original
            revision.op = revision_original
