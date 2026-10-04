import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect


def _load(name: str, filename: str):
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_station_patient_session_migration_roundtrip(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'station-patient-session.sqlite'}")
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("patients", metadata, Column("id", Integer, primary_key=True))
    Table("patient_companion_accesses", metadata, Column("id", Integer, primary_key=True))
    Table(
        "cabinet_configs",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("owner_id", Integer, nullable=False),
    )
    metadata.create_all(engine)

    base = _load("v7100000021", "v7100000021_workstation_mode_memory.py")
    identity = _load("neo000000026", "neo000000026_station_identity_pairing.py")
    revision = _load("neo000000027", "neo000000027_station_patient_session.py")

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        originals = (base.op, identity.op, revision.op)
        base.op = operations
        identity.op = operations
        revision.op = operations
        try:
            base.upgrade()
            identity.upgrade()
            revision.upgrade()

            inspector = inspect(connection)
            assert "workstation_patient_sessions" in inspector.get_table_names()
            columns = {column["name"] for column in inspector.get_columns("workstation_patient_sessions")}
            assert {
                "id",
                "employer_id",
                "workstation_id",
                "claim_token_hash",
                "patient_access_id",
                "patient_id",
                "fallback_failed_attempts",
                "created_at",
                "expires_at",
                "claimed_at",
                "purged_at",
            }.issubset(columns)

            indexes = {index["name"]: index for index in inspector.get_indexes("workstation_patient_sessions")}
            assert bool(indexes["ix_workstation_patient_sessions_claim_token_hash"]["unique"])

            config_columns = {column["name"] for column in inspector.get_columns("cabinet_configs")}
            assert "station_identification_fallback" in config_columns

            revision.downgrade()
            inspector = inspect(connection)
            assert "workstation_patient_sessions" not in inspector.get_table_names()
            config_columns = {column["name"] for column in inspector.get_columns("cabinet_configs")}
            assert "station_identification_fallback" not in config_columns
        finally:
            base.op, identity.op, revision.op = originals
